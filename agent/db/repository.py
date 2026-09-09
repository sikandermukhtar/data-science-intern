import uuid
import json
import time
from typing import List, Dict, Any, Optional
from agent.db.database import get_db, init_db
from agent.db.models import SessionModel, MessageModel, SubagentTaskModel


class SessionRepository:
    def __init__(self):
        init_db()

    def create_session(self, session_id: Optional[str] = None, title: str = "New Session") -> SessionModel:
        sid = session_id or str(uuid.uuid4())
        now = time.time()
        session = SessionModel(id=sid, title=title, created_at=now, updated_at=now, is_archived=False)
        with get_db() as conn:
            conn.execute("""
                INSERT INTO sessions (id, title, created_at, updated_at, is_archived, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session.id, session.title, session.created_at, session.updated_at, 0, json.dumps(session.metadata)))
        return session
        
    def get_session(self, session_id: str) -> Optional[SessionModel]:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if not row:
                return None
            return SessionModel(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                is_archived=bool(row["is_archived"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )

    def list_sessions(self, include_archived: bool = False, archived_only: bool = False) -> List[SessionModel]:
        with get_db() as conn:
            if archived_only:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE is_archived = 1 ORDER BY updated_at DESC"
                ).fetchall()
            elif not include_archived:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE is_archived = 0 ORDER BY updated_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sessions ORDER BY updated_at DESC"
                ).fetchall()
            return [
                SessionModel(
                    id=r["id"],
                    title=r["title"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_archived=bool(r["is_archived"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                )
                for r in rows
            ]

    def archive_session(self, session_id: str) -> bool:
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE sessions SET is_archived = 1, updated_at = ? WHERE id = ?",
                (time.time(), session_id)
            )
            return cursor.rowcount > 0

    def unarchive_session(self, session_id: str) -> bool:
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE sessions SET is_archived = 0, updated_at = ? WHERE id = ?",
                (time.time(), session_id)
            )
            return cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        with get_db() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0

    def update_session_title(self, session_id: str, title: str):
        with get_db() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, time.time(), session_id)
            )

    def touch_session(self, session_id: str):
        with get_db() as conn:
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (time.time(), session_id))

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        files: Optional[List[Dict[str, Any]]] = None,
        turn_id: Optional[str] = None,
        sender: str = "supervisor",
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageModel:
        # Ensure session exists
        if not self.get_session(session_id):
            self.create_session(session_id)
        msg_id = str(uuid.uuid4())
        now = time.time()
        files_json = json.dumps(files) if files else None
        meta_json = json.dumps(metadata or {})
        with get_db() as conn:
            conn.execute("""
                INSERT INTO messages (id, session_id, turn_id, role, sender, content, files, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (msg_id, session_id, turn_id, role, sender, content, files_json, meta_json, now))
            
            # If user message and title is default, update session title
            if role == "user":
                current_session = self.get_session(session_id)
                if current_session and current_session.title == "New Session":
                    snippet = content[:40] + ("..." if len(content) > 40 else "")
                    conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (snippet, session_id))
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        return MessageModel(
            id=msg_id,
            session_id=session_id,
            turn_id=turn_id,
            role=role,
            sender=sender,
            content=content,
            files=files,
            metadata=metadata or {},
            created_at=now
        )

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns messages in LiteLLM standard dict format ordered chronologically."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, role, content, files, created_at 
                FROM messages 
                WHERE session_id = ? 
                ORDER BY created_at ASC
            """, (session_id,)).fetchall()
            result = []
            for r in rows:
                item = {
                    "id": r["id"],
                    "role": r["role"],
                    "content": r["content"],
                    "timestamp": r["created_at"] * 1000  # ms for frontend
                }
                if r["files"]:
                    item["files"] = json.loads(r["files"])
                result.append(item)
            return result

    def clear_messages(self, session_id: str):
        """Clears all non-system messages for a session."""
        with get_db() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ? AND role != 'system'", (session_id,))
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (time.time(), session_id))
    
    def record_subagent_task(
        self,
        session_id: str,
        task_index: int,
        task_description: str,
        status: str,
        turn_id: Optional[str] = None,
        code: Optional[str] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        attempts: int = 1
    ) -> SubagentTaskModel:
        task_id = str(uuid.uuid4())
        now = time.time()
        files_json = json.dumps(files) if files else None
        with get_db() as conn:
            conn.execute("""
                INSERT INTO subagent_tasks (
                    id, session_id, turn_id, task_index, task_description,
                    status, code, stdout, stderr, files, attempts, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id, session_id, turn_id, task_index, task_description,
                status, code, stdout, stderr, files_json, attempts, now, now
            ))
        return SubagentTaskModel(
            id=task_id,
            session_id=session_id,
            turn_id=turn_id,
            task_index=task_index,
            task_description=task_description,
            status=status,
            code=code,
            stdout=stdout,
            stderr=stderr,
            files=files,
            attempts=attempts,
            created_at=now,
            updated_at=now
        )

# Global singleton repository instance
session_repo = SessionRepository()