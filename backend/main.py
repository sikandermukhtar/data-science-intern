import json
import uuid
import asyncio
import shutil
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.configs.config import backend_settings
from agent.core.session import get_or_create_session, delete_session, OperationType, EventType
from agent.core.agent_loop import run_agent_loop
from agent.context.manager import ContextManager
from agent.tools.sandbox import PythonSandbox
from agent.db.repository import session_repo


app = FastAPI(title="Data Science Intern Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static folder so frontend can load saved PNG charts via `/static/{session_id}/{filename}`
app.mount("/static", StaticFiles(directory=str(backend_settings.STATIC_DIR)), name="static")

@app.get("/api/sessions")
def list_sessions(
    include_archived: bool = Query(False, description="Include archived sessions"),
    archived_only: bool = Query(False, description="Fetch only archived sessions")

):
    """Fetches sessions from SQLite, supporting active and archived filtering."""
    sessions = session_repo.list_sessions(include_archived=include_archived, archived_only=archived_only)
    return [
        {
            "id": s.id,
            "title": s.title,
            "updatedAt": s.updated_at * 1000,
            "createdAt": s.created_at * 1000,
            "isArchived": s.is_archived
        }
        for s in sessions
    ]

@app.post("/api/sessions")
def create_session():
    """Generates a new session in SQLite and initializes its context."""
    session = session_repo.create_session()
    ContextManager(session.id)
    return {"id": session.id}

@app.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    """Loads chat messages for the given session ID."""
    manager = ContextManager(session_id)
    return manager.get_messages()

@app.post("/api/sessions/{session_id}/archive")
def archive_session(session_id: str):
    """Marks a session as archived in SQLite."""
    success = session_repo.archive_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "archived", "session_id": session_id}
@app.post("/api/sessions/{session_id}/unarchive")
def unarchive_session(session_id: str):
    """Restores an archived session back to active."""
    success = session_repo.unarchive_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "unarchived", "session_id": session_id}

@app.post("/api/sessions/{session_id}/upload")
async def upload_dataset(session_id: str, file: UploadFile = File(...)):
    """Receives a multipart file upload and saves it directly to the session sandbox directory."""
    try:
        content = await file.read()
        sandbox = PythonSandbox(session_id)
        sandbox.add_file(file.filename, content)
        return {"filename": file.filename, "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@app.delete("/api/sessions/{session_id}")
def remove_session(session_id: str):
    """Permanently deletes a session from SQLite, in-memory state, and disk sandbox."""
    # Clean up active in-memory session state
    delete_session(session_id)
    # Delete from SQLite DB (cascades to messages and subagent_tasks)
    success = session_repo.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    # Clean up sandbox and static files for this session
    sandbox_path = backend_settings.BASE_DIR / "sandbox" / session_id
    if sandbox_path.exists():
        shutil.rmtree(sandbox_path, ignore_errors=True)
    static_session_path = backend_settings.STATIC_DIR / session_id
    if static_session_path.exists():
        shutil.rmtree(static_session_path, ignore_errors=True)
    return {"status": "deleted", "session_id": session_id}

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint that receives user inputs and streams execution events."""
    await websocket.accept()
    session_state = get_or_create_session(session_id)

    # Background task to fetch events from Queue and write them to the WebSocket connection
    async def event_sender():
        try:
            while True:
                event = await session_state.event_queue.get()
                await websocket.send_json(event.model_dump())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in websocket event sender loop: {e}")

    sender_task = asyncio.create_task(event_sender())
    try:
        while True:
            # Wait for text prompts sent from frontend client
            data = await websocket.receive_text()
            payload = json.loads(data)
            if payload.get("type") == "message":
                user_content = payload["content"]
                files_payload = payload.get("files", [])
                session_state.context_manager.add_message(
                    role="user",
                    content=user_content,
                    files=files_payload if files_payload else None
                )
                asyncio.create_task(run_agent_loop(session_id))
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session: {session_id}")
    finally:
        sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass
