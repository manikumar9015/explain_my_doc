# backend/core/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# Import our vector store to call its delete method
from backend.vector_store.chroma import vector_store_instance

class SessionManager:
    def __init__(self, expiry_minutes: int = 60):
        # A dictionary to store session IDs and their creation timestamps
        self.active_sessions = {}
        self.expiry_delta = timedelta(minutes=expiry_minutes)
        print(f"Session manager initialized. Sessions will expire after {expiry_minutes} minutes.")

    def register_session(self, session_id: str):
        """Adds a new session to the tracker."""
        self.active_sessions[session_id] = datetime.now()
        print(f"Session registered: {session_id}")

    def cleanup_expired_sessions(self):
        """Finds and deletes expired sessions and their corresponding collections."""
        now = datetime.now()
        expired_ids = []
        
        print("Running cleanup job...")
        for session_id, creation_time in self.active_sessions.items():
            if now - creation_time > self.expiry_delta:
                expired_ids.append(session_id)
        
        if not expired_ids:
            print("No expired sessions found.")
            return

        for session_id in expired_ids:
            print(f"Session {session_id} has expired. Deleting...")
            try:
                # Tell ChromaDB to delete the entire collection
                vector_store_instance.delete_collection(collection_name=session_id)
                # Remove from our tracking dictionary
                del self.active_sessions[session_id]
                print(f"Successfully deleted collection and session: {session_id}")
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")

# Create global instances
session_manager = SessionManager()
scheduler = AsyncIOScheduler()