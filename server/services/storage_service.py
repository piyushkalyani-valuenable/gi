"""
Storage service for file handling using SQLAlchemy
Currently stores as blob in DB, interface ready for S3 swap
"""
from typing import Optional, Tuple
from database.connection import Database
from database.models import ChatSession


class StorageService:
    """
    File storage service - blob storage now, S3-ready interface
    Just swap the internal implementation later without changing callers
    """

    @staticmethod
    def store_file(session_id: str, file_type: str, file_data: bytes, filename: str) -> bool:
        """
        Store file for a session

        Args:
            session_id: UUID of the session
            file_type: 'policy_bond', 'bill', or 'prescription'
            file_data: Raw file bytes
            filename: Original filename

        Returns:
            True if successful
        """
        file_column = f"{file_type}_file"
        name_column = f"{file_type}_filename"

        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                setattr(session, file_column, file_data)
                setattr(session, name_column, filename)
                return True
            return False

    @staticmethod
    def get_file(session_id: str, file_type: str) -> Optional[Tuple[bytes, str]]:
        """
        Retrieve file for a session

        Args:
            session_id: UUID of the session
            file_type: 'policy_bond', 'bill', or 'prescription'

        Returns:
            Tuple of (file_bytes, filename) or None
        """
        file_column = f"{file_type}_file"
        name_column = f"{file_type}_filename"

        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                file_data = getattr(session, file_column, None)
                filename = getattr(session, name_column, None)
                if file_data and filename:
                    return (file_data, filename)
            return None
