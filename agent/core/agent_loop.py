import json
import re
import traceback
from typing import TypedDict, List, Dict, Any, Literal
from litellm import acompletion
from langgraph.graph import StateGraph, END
from agent.configs.config import agent_settings
from agent.core.session import get_or_create_session, EventType, OperationType
from agent.core.execution_engine import TaskExecutionEngine
from agent.tools.sandbox import PythonSandbox

class AgentState(TypedDict):
    session_id: str
    messages: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    current_task_idx: int
    worker_results: List[Dict[str, Any]]
    final_response: str

async def generate_plan(session_id: str, messages: List[Dict[str, Any]], files: List[str]) -> List[str]:
    """Uses LLM to generate a structured list of subtasks for the supervisor."""
    files_str = ", ".join(files) if files else "No files currently uploaded."

    recent_conversation = []
    for m in messages[-3:]:
        if m["role"] in ["user", "assistant"]:
            recent_conversation.append(f"{m['role'].upper()}: {m['content']}")
    conversation_str = "\n".join(recent_conversation)

    system_prompt = (
        "You are a Data Science Planner. Given the conversation history and files in the sandbox, "
        "your job is to break the request down into a list of sequential, concrete data science tasks.\n"
        "Respond ONLY with a JSON object in this format:\n"
        '{"tasks": ["task 1 description", "task 2 description", "task 3 description"]}\n'
        "Keep the descriptions clear and action-oriented (e.g. 'Perform EDA and plot correlation heatmap')."
    )
    
    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Conversation:\n{conversation_str}\n\nSandbox files: {files_str}"}
    ]

    try:
        # Request JSON mode via LiteLLM
        response = await acompletion(
            model=agent_settings.SUPERVISOR_MODEL,
            messages=prompt_messages,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return data.get("tasks", [])
    except Exception as e:
        # fallback parsing
        try:
            response = await acompletion(
                model=agent_settings.SUPERVISOR_MODEL,
                messages=prompt_messages,
                temperature=0.2
            )
            content = response.choices[0].message.content or ""
            # Extract JSON block using regex if model wraps it in markdown
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return data.get("tasks", [])
            
            # Simple line parsing if json mode fails completely
            lines = [line.strip("- *").strip() for line in content.split("\n") if line.strip().startswith(("-", "*", "1.", "2.", "3."))]
            return lines if lines else ["Analyze dataset"]
        except Exception:
            return ["Analyze the data and output results"]

async def generate_final_response(session_id: str, user_query: str, worker_results: List[Dict[str, Any]]) -> str:
    """Uses LLM to synthesize all worker outputs into a single markdown summary."""
    summaries = []
    for i, res in enumerate(worker_results):
        status_str = "SUCCESS" if res["success"] else "FAILED"
        file_list = ", ".join([f["name"] for f in res["files"]]) if res["files"] else "None"
        summaries.append(
            f"### Task {i+1}: {res['task']}\n"
            f"- **Status**: {status_str}\n"
            f"- **Output Summary**:\n{res['stdout']}\n"
            f"- **Generated files**: {file_list}\n"
        )
    summary_str = "\n\n".join(summaries)
    
    system_prompt = (
        "You are the Lead Data Science Supervisor. Your workers have completed their tasks.\n"
        "Synthesize their results and compose a professional, comprehensive final response to the user.\n"
        "Guidelines:\n"
        "- Summarize all key data insights, statistics, and model parameters in Markdown tables.\n"
        "- Explicitly mention the generated charts/files. Note: the UI will render these files automatically.\n"
        "- Draw clear conclusions and recommendations for the user.\n"
        "- Do not include raw Python code unless explaining a specific function parameter."
    )
    
    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User's request: {user_query}\n\nWorker Execution Logs:\n{summary_str}"}
    ]
    
    response = await acompletion(
        model=agent_settings.SUPERVISOR_MODEL,
        messages=prompt_messages,
        temperature=0.3
    )
    return response.choices[0].message.content or ""


# Langgraph Node Implementations

async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    session_id = state["session_id"]
    session_state = get_or_create_session(session_id)

    if not state["tasks"]:
        await session_state.push_event(
            EventType.PROCESSING,
            {"status": "Planning tasks and dividing labor..."}
        )
        
        sandbox = PythonSandbox(session_id)
        files = [f.name for f in sandbox._get_files()]
        
        tasks_list = await generate_plan(session_id, state["messages"], files)
        
        tasks = [{"id": i + 1, "description": desc, "status": "pending"} for i, desc in enumerate(tasks_list)]
        session_state.current_tasks = tasks

        await session_state.push_event(
            EventType.PROCESSING,
            {"status": f"Scheduled {len(tasks)} sub-tasks."}
        )
        
        return {"tasks": tasks, "current_task_idx": 0}

    if state["current_task_idx"] >= len(state["tasks"]):
        await session_state.push_event(
            EventType.PROCESSING,
            {"status": "Synthesizing final response..."}
        )
        
        user_query = ""
        for m in reversed(state["messages"]):
            if m["role"] == "user":
                user_query = m["content"]
                break
                
        final_answer = await generate_final_response(session_id, user_query, state["worker_results"])
        
        session_state.context_manager.add_message("assistant", final_answer)
        
        await session_state.push_event(
            EventType.TURN_COMPLETE,
            {"content": final_answer}
        )
        
        return {"final_response": final_answer}
        
    return {}

async def worker_dispatch_node(state: AgentState) -> Dict[str, Any]:
    session_id = state["session_id"]
    session_state = get_or_create_session(session_id)
    current_idx = state["current_task_idx"]

    tasks = [t.copy() for t in state["tasks"]]
    tasks[current_idx]["status"] = "running"
    session_state.current_tasks = tasks

    task_desc = tasks[current_idx]["description"]
    engine = TaskExecutionEngine(session_id)
    result = await engine.execute_task(task_desc)

    tasks[current_idx]["status"] = "completed" if result["success"] else "failed"
    session_state.current_tasks = tasks

    worker_results = list(state["worker_results"]) + [result]

    return {
        "tasks": tasks,
        "worker_results": worker_results,
        "current_task_idx": current_idx + 1
    }

def router_node(state: AgentState) -> Literal["worker", "end"]:
    """Determines whether to trigger the next worker or finish."""
    if state["current_task_idx"] < len(state["tasks"]):
        return "worker"
    return "end"

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("worker", worker_dispatch_node)
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    router_node,
    {
        "worker": "worker",
        "end": END
    }
)
workflow.add_edge("worker", "supervisor")
agent_graph = workflow.compile()

# Execution Entrypoint

async def run_agent_loop(session_id: str):
    """Asynchronously executes the supervisor-worker graph for a session."""
    session_state = get_or_create_session(session_id)
    if session_state.is_running:
        return

    session_state.is_running = True
    session_state.current_operation = OperationType.USER_PROMPT

    try:
        messages = session_state.context_manager.get_messages()
        
        initial_state = {
            "session_id": session_id,
            "messages": messages,
            "tasks": [],
            "current_task_idx": 0,
            "worker_results": [],
            "final_response": ""
        }
        
        await agent_graph.ainvoke(initial_state)
    
    except Exception as e:
        error_msg = str(e)
        error_details = traceback.format_exc()
        await session_state.push_event(
            EventType.ERROR,
            {"message": error_msg, "details": error_details}
        )
    finally:
        session_state.is_running = False
        session_state.current_operation = None
    
