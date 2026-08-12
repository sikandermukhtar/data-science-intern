import json
import uuid
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.configs.config import backend_settings
from agent.core.session import get_or_create_session, OperationType, EventType
from agent.core.agent_loop import run_agent_loop
from agent.context.manager import ContextManager
from agent.tools.sandbox import PythonSandbox
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
def list_sessions():
    """Reads the session folders and returns all saved session metadata."""
    sessions_dir = backend_settings.BASE_DIR / "sessions"
    if not sessions_dir.exists():
        return []
        
    sessions = []
    for path in sessions_dir.iterdir():
        if path.is_dir():
            session_id = path.name
            context_file = path / "context.json"
            title = "New Session"
            updated_at = path.stat().st_mtime * 1000 
            
            if context_file.exists():
                try:
                    with open(context_file, "r") as f:
                        messages = json.load(f)
                    # Find the first user message content to use as the sidebar title
                    user_msgs = [m for m in messages if m["role"] == "user"]
                    if user_msgs:
                        first_content = user_msgs[0]["content"]
                        title = first_content[:40] + ("..." if len(first_content) > 40 else "")
                except Exception:
                    pass
            
            sessions.append({
                "id": session_id,
                "title": title,
                "updatedAt": updated_at
            })
            
    sessions.sort(key=lambda s: s["updatedAt"], reverse=True)
    return sessions

@app.post("/api/sessions")
def create_session():
    """Generates a new UUID, initializes its ContextManager, and returns the session ID."""
    session_id = str(uuid.uuid4())
    ContextManager(session_id) 
    return {"id": session_id}

@app.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    """Loads chat messages for the given session ID."""
    manager = ContextManager(session_id)
    return manager.get_messages()

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
