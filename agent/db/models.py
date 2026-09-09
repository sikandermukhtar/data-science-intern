import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SessionModel(BaseModel):
    id: str
    title: str = "New Session"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    is_archieved: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MessageModel(BaseModel):
    id: str
    session_id: str
    turn_id: Optional[str] = None
    role: str # "system" | "user" | "tool"
    sender: str = "supervisor" # "supervisor" | "user" | "worker" | "sandbox"
    content: str
    files: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

class SubagentTaskModel(BaseModel):
    id: str
    session_id: str
    turn_id: Optional[str] = None
    task_index: int
    task_description: str
    status: str  # "pending" | "running" | "completed" | "failed"
    code: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None
    attempts: int = 1
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)