"""
Gestione delle sessioni di chat in memoria.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import uuid
import threading


@dataclass
class ChatMessage:
    role: str  # "user" o "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ChatSession:
    id: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        self.last_activity = datetime.now()
        return msg

    def get_history_for_gemini(self) -> List[dict]:
        """Converte la history nel formato richiesto da Gemini."""
        history = []
        for msg in self.messages:
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [msg.content]})
        return history


class SessionManager:
    """Gestisce le sessioni chat in memoria con cleanup automatico."""

    def __init__(self, session_timeout_minutes: int = 30):
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = threading.Lock()
        self._timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(self) -> ChatSession:
        """Crea una nuova sessione."""
        session_id = str(uuid.uuid4())
        session = ChatSession(id=session_id)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Recupera una sessione esistente."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                # Verifica timeout
                if datetime.now() - session.last_activity > self._timeout:
                    del self._sessions[session_id]
                    return None
                return session
        return None

    def get_or_create_session(self, session_id: Optional[str]) -> ChatSession:
        """Recupera una sessione o ne crea una nuova."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        return self.create_session()

    def delete_session(self, session_id: str) -> bool:
        """Elimina una sessione."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
        return False

    def cleanup_expired(self) -> int:
        """Rimuove le sessioni scadute. Ritorna il numero di sessioni rimosse."""
        now = datetime.now()
        removed = 0
        with self._lock:
            expired = [
                sid for sid, sess in self._sessions.items()
                if now - sess.last_activity > self._timeout
            ]
            for sid in expired:
                del self._sessions[sid]
                removed += 1
        return removed


# Singleton del session manager
session_manager = SessionManager()
