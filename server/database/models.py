"""
SQLAlchemy ORM models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    LargeBinary,
    DateTime,
    Enum,
    DECIMAL,
    Integer,
    JSON,
    create_engine,
)
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import declarative_base, sessionmaker
import enum

Base = declarative_base()


# Enums
class SessionStatus(str, enum.Enum):
    AWAITING_POLICY = "awaiting_policy"
    AWAITING_DOCUMENT_CHOICE = "awaiting_document_choice"
    AWAITING_BILL = "awaiting_bill"
    AWAITING_PRESCRIPTION = "awaiting_prescription"
    AWAITING_BOTH_BILL = "awaiting_both_bill"
    AWAITING_BOTH_PRESCRIPTION = "awaiting_both_prescription"
    COMPLETED = "completed"


class DocumentChoice(str, enum.Enum):
    BILL = "bill"
    PRESCRIPTION = "prescription"
    BOTH = "both"


# Models
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # File storage (LONGBLOB for large files, S3 path later)
    policy_bond_file = Column(LONGBLOB, nullable=True)
    policy_bond_filename = Column(String(255), nullable=True)
    bill_file = Column(LONGBLOB, nullable=True)
    bill_filename = Column(String(255), nullable=True)
    prescription_file = Column(LONGBLOB, nullable=True)
    prescription_filename = Column(String(255), nullable=True)

    # Extracted data (JSON for debugging)
    bill_extraction = Column(JSON, nullable=True)
    bond_extraction = Column(JSON, nullable=True)
    prescription_extraction = Column(JSON, nullable=True)
    calculation_result = Column(JSON, nullable=True)

    # Session state
    status = Column(
        Enum(SessionStatus),
        default=SessionStatus.AWAITING_POLICY,
        nullable=False,
    )
    document_choice = Column(Enum(DocumentChoice), nullable=True)


class InternalDatabase(Base):
    __tablename__ = "internal_database"

    id = Column(Integer, primary_key=True, autoincrement=True)
    procedure_name = Column(String(255), nullable=False, index=True)
    hospital_name = Column(String(255), nullable=True, index=True)
    price = Column(DECIMAL(15, 2), nullable=True)
    source = Column(String(50), default="Manual", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AbhaDatabase(Base):
    """Reference to existing ABHA database table"""
    __tablename__ = "abha_database"

    id = Column(Integer, primary_key=True)
    package_name = Column(String(255), nullable=True)
    total_package_price = Column(DECIMAL(15, 2), nullable=True)
    # Add other columns as needed
