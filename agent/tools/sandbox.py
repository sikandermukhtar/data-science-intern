import sys
import os
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from langchain_core.tools import tool
from agent.configs.config import agent_settings

class PythonSandbox:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.sandbox_dir = agent_settings.SANDBOX_DIR / session_id
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        self.output_dir = agent_settings.OUTPUT_DIR / session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def add_file(self, filename: str, content: bytes):
        """Saves a user-uploaded file directly to sandbox directory"""
        dest = self.sandbox_dir / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(content)

    def _get_files(self) -> set[Path]:
        """Scans all files inside the sandbox directory."""
        return {
            p for p in self.sandbox_dir.glob("**/*")
            if p.is_file() and p.name != "script.py"
        }

    async def run_code(self, code: str, timeout: float  = 180.0) -> Dict[str, Any]:
        """Runs python code asynchronously, capturing outputs and generated files."""
        script_path = self.sandbox_dir / "script.py"

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        pre_files = self._get_files()

        # Run Python script using the same virtual environment python executable
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.sandbox_dir)
            )
            # Await run completion with timeout to guard against infinite loops
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                returncode = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                stdout=""
                stderr = f"TimeoutError: Execution exceeded the {timeout}s limit."
                returncode = -1
        except Exception as e:
            stdout = ""
            stderr = f"Execution failed to launch: {str(e)}"
            returncode = -1

        post_files = self._get_files()
        new_files = post_files - pre_files

        # Copy any new files to the backend static folder and build URLs for frontend
        saved_files = []
        for file_path in new_files:
            relative_name = file_path.relative_to(self.sandbox_dir)
            dest_path = self.output_dir / relative_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy to backend/static/{session_id}/
            shutil.copy2(file_path, dest_path)
            
            # Generate the serving URL
            url = f"/static/{self.session_id}/{relative_name.as_posix()}"
            
            # Detect MIME file type roughly
            suffix = file_path.suffix.lower()
            if suffix in [".png", ".jpg", ".jpeg"]:
                mime = "image/png"
            elif suffix == ".csv":
                mime = "text/csv"
            else:
                mime = "application/octet-stream"
            saved_files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": mime,
                "url": url,
                "local_path": str(file_path)
            })
        return {
            "success": returncode == 0,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "files": saved_files
        }

def get_sandbox_tool(session_id: str):
    """Creates a Langgraph-compatible tool bound to a specific session."""
    sandbox = PythonSandbox(session_id)

    @tool
    async def execute_python_code(code: str) -> str:
        """
        Executes Python code in a local sandbox environment.
        Use this tool to run data science tasks, load datasets, perform EDA, and train models.
        All output files (plots, csvs) created in the sandbox will be saved and rendered on the UI automatically.
        Returns the console stdout and stderr.
        """
        result = await sandbox.run_code(code)

        from agent.core.session import get_or_create_session, EventType

        # Save code execution log to ContextManager (Persisted)
        session_state = get_or_create_session(session_id)
        code_log_content = (
            f"#### 💻 Running Sandbox Script\n"
            f"```python\n{code}\n```\n\n"
            f"**Console Output:**\n"
            f"```\n{result['stdout'] or '(No stdout)'}\n"
        )
        if result['stderr']:
            code_log_content += f"STDERR:\n{result['stderr']}\n"
        code_log_content += "```"
        session_state.context_manager.add_message("assistant", code_log_content)

        # Save generated images as a persistent charts message in context
        image_files = [f for f in result["files"] if f["type"].startswith("image/")]
        if image_files:
            session_state.context_manager.add_message(
                role="assistant",
                content="---charts---",
                files=image_files
            )

        await session_state.push_event(
            EventType.CODE_EXECUTED,
            {
                "code": code,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "success": result["success"],
                "files": result["files"]
            }
        )

        output_summary = f"STDOUT:\n{result['stdout']}"
        if result["stderr"]:
            output_summary += f"\nSTDERR:\n{result["stderr"]}"
        if result["files"]:
            filenames = [f["name"] for f in result["files"]]
            output_summary += f"\nGenerated Files: {', '.join(filenames)}"
        if not result["success"]:
            output_summary = f"EXECUTION FAILED (exit code {result['returncode']})\n" + output_summary
        return output_summary
    
    return execute_python_code