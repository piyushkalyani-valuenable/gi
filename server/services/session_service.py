"""
Session management service using SQLAlchemy
"""
import uuid
from typing import Optional, Dict, Any
from database.connection import Database
from database.models import ChatSession, SessionStatus, DocumentChoice


class SessionService:
    """Manages chat sessions in database"""

    @staticmethod
    def create_session() -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())

        with Database.get_session() as db:
            chat_session = ChatSession(
                id=session_id,
                status=SessionStatus.AWAITING_POLICY,
            )
            db.add(chat_session)

        return session_id

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID as dict"""
        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

            if not session:
                return None

            return {
                "id": session.id,
                "status": session.status.value if session.status else None,
                "document_choice": session.document_choice.value if session.document_choice else None,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "policy_bond_filename": session.policy_bond_filename,
                "bill_filename": session.bill_filename,
                "prescription_filename": session.prescription_filename,
                "bill_extraction": session.bill_extraction,
                "bond_extraction": session.bond_extraction,
                "prescription_extraction": session.prescription_extraction,
                "calculation_result": session.calculation_result,
            }

    @staticmethod
    def update_status(session_id: str, status: str) -> bool:
        """Update session status"""
        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.status = SessionStatus(status)
                return True
            return False

    @staticmethod
    def set_document_choice(session_id: str, choice: str) -> bool:
        """Set the document choice"""
        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.document_choice = DocumentChoice(choice)
                return True
            return False

    @staticmethod
    def save_extraction(session_id: str, extraction_type: str, data: Dict[str, Any]) -> bool:
        """Save extracted JSON data"""
        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                setattr(session, extraction_type, data)
                return True
            return False

    @staticmethod
    def get_extraction(session_id: str, extraction_type: str) -> Optional[Dict[str, Any]]:
        """Get saved extraction data"""
        with Database.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                return getattr(session, extraction_type, None)
            return None
