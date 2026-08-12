import re
import asyncio
from typing import Dict, Any, List
from litellm import acompletion
from agent.configs.config import agent_settings
from agent.core.session import get_or_create_session, EventType
from agent.tools.sandbox import PythonSandbox
from agent.context.manager import DEFAULT_WORKER_PROMPT

class TaskExecutionEngine:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_state = get_or_create_session(session_id)
        self.sandbox = PythonSandbox(session_id)

    async def execute_task(self, task_description: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Runs a data science sub-task by executing a LLM code generation
        and evaluation loop with built-in sandbox error self-correction.
        """
        await self.session_state.push_event(
            EventType.WORKER_SPAWNED,
            {"task": task_description}
        )

        existing_files = [f.name for f in self.sandbox._get_files()]
        files_str = ", ".join(existing_files) if existing_files else "No files uploaded yet."
        system_prompt = DEFAULT_WORKER_PROMPT.format(
            task_description=task_description,
            output_dir=self.sandbox.output_dir.as_posix()
        )

        #Initial prompt context for the worker model
        worker_messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Available files: [{files_str}]. Please write the Python script to execute this task."
            }
        ]

        attempt = 0
        latest_code = ""
        latest_stdout = ""
        latest_stderr = ""
        latest_files = []
        success = False

        while attempt < max_retries:
            attempt += 1
            await self.session_state.push_event(
                EventType.PROCESSING,
                {"status": f"Worker generating code (attempt {attempt}/{max_retries})"}
            )

            try:
                response = await acompletion(
                    model=agent_settings.WORKER_MODEL,
                    messages=worker_messages,
                    temperature=0.2
                )
                assistant_response = response.choices[0].message.content or ""
                worker_messages.append({"role": "assistant", "content": assistant_response})

                code = extract_python_code(assistant_response)
                latest_code = code

                if not code:
                    worker_messages.append({
                        "role": "user",
                        "content": "I couldn't detect a valid Python block in your response. Please wrap your code in ```python ... ```."
                    })
                    continue

                await self.session_state.push_event(
                    EventType.PROCESSING,
                    {"status": f"Running script in sandbox..."}
                )

                sandbox_result = await self.sandbox.run_code(code, timeout=180)
                latest_stdout = sandbox_result["stdout"]
                latest_stderr = sandbox_result["stderr"]
                latest_files = sandbox_result["files"]
                await self.session_state.push_event(
                    EventType.CODE_EXECUTED,
                    {
                        "code": code,
                        "stdout": latest_stdout,
                        "stderr": latest_stderr,
                        "success": sandbox_result["success"],
                        "files": latest_files
                    }
                )

                if sandbox_result["success"]:
                    success = True
                    break
                else:
                    # Self-correction step: feed error back to worker
                    feedback = (
                        f"Execution failed (Exit Code {sandbox_result['returncode']}).\n"
                        f"STDERR:\n{latest_stderr}\n"
                        f"STDOUT:\n{latest_stdout}\n\n"
                        f"Please analyze the errors, fix your code, and output the entire corrected script in ```python ... ```."
                    )
                    worker_messages.append({"role": "user", "content": feedback})

            except Exception as e:
                latest_stderr = f"Worker model or sandbox execution exception: {str(e)}"
                break
        return {
            "success": success,
            "task": task_description,
            "code": latest_code,
            "stdout": latest_stdout,
            "stderr": latest_stderr,
            "files": latest_files,
            "attempts": attempt
        }

def extract_python_code(text: str) -> str:
    """Helper to parse and extract a Python cdoe block from Markdown."""
    pattern = r"```python\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    pattern_fallback = r"```\s*(.*?)\s*```"
    match_fallback = re.search(pattern_fallback, text, re.DOTALL)
    if match_fallback:
        return match_fallback.group(1).strip()
        
    return text.strip()
