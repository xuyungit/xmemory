import os
import json
import time
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import settings

class SessionManager:
    def __init__(self):
        self.session_dir = Path(settings.SESSION_DIR)
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(self, user_id: str) -> str:
        """Create a new session and return the session ID"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=settings.SESSION_EXPIRY_DAYS)).isoformat()
        }
        
        session_file = self.session_dir / f"{session_id}.json"
        with open(session_file, "w") as f:
            json.dump(session_data, f)
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if a session exists and is not expired"""
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return False
            
        with open(session_file, "r") as f:
            session_data = json.load(f)
            
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now() > expires_at:
            self.delete_session(session_id)
            return False
            
        return True
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        session_file = self.session_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    def cleanup_expired_sessions(self):
        """Clean up all expired sessions"""
        for session_file in self.session_dir.glob("*.json"):
            with open(session_file, "r") as f:
                session_data = json.load(f)
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.now() > expires_at:
                    session_file.unlink()

session_manager = SessionManager() 