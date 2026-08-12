import asyncio
import time
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from agent.context.manager import ContextManager

class OperationType(str, Enum):
    USER_PROMPT = "user_prompt"
    RECOVERY = "recovery"
    INTERRUPT = "interrupt"
    UNDO = "undo"

class EventType(str, Enum):
    PROCESSING = "processing" 
    WORKER_SPAWNED = "worker_spawned"
    CODE_EXECUTED = "code_executed"
    TURN_COMPLETE = "turn_complete"
    UNDO_COMPLETE = "undo_complete"
    ERROR = "error"
    INTERRUPTED = "interrupted"

class AgentEvent(BaseModel):
    event_type: EventType
    session_id: str
    payload: Dict[str, Any] = {}
    timestamp: float

class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.is_running: bool = False
        self.current_operation: Optional[OperationType] = None

        # e.g., [{"id": 1, "description": "EDA on diabetes.csv", "status": "pending" | "running" | "completed" | "failed"}]
        self.current_tasks: List[Dict[str, Any]] = []
        self.context_manager = ContextManager(session_id)

        self.event_queue: asyncio.Queue[AgentEvent] = asyncio.Queue()

    async def push_event(self, event_type: EventType, payload: Dict[str, Any] = {}):
        """Pushes an operational event onto the queue to stream to the client."""
        event = AgentEvent(
            event_type=event_type,
            session_id=self.session_id,
            payload=payload,
            timestamp=time.time()
        )
        await self.event_queue.put(event)

# In-memory registry to persist active session states during server execution
_active_sessions: Dict[str, SessionState] = {}

def get_or_create_session(session_id: str) -> SessionState:
    """Helper function to fetch or initialize a session's state."""
    if session_id not in _active_sessions:
        _active_sessions[session_id] = SessionState(session_id)
    return _active_sessions[session_id]

def delete_session(session_id: str):
    """Clean up a session when it is deleted."""
    if session_id in _active_sessions:
        del _active_sessions[session_id]