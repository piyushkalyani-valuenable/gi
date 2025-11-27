"""
SQLAlchemy database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from config.settings import settings


class Database:
    """SQLAlchemy database manager"""

    _engine = None
    _SessionLocal = None

    @classmethod
    def get_database_url(cls) -> str:
        """
        Build database URL based on environment
        
        - local/development/dev → Use local MySQL
        - production/staging/any other → Use AWS Secrets Manager
        """
        # Simple check: if environment is local/dev, use local DB, else use AWS
        if settings.is_local:
            print(f"🏠 LOCAL database: {settings.local_db_host}/{settings.local_db_name}")
            return (
                f"mysql+mysqlconnector://"
                f"{settings.local_db_user}:{settings.local_db_password}"
                f"@{settings.local_db_host}:{settings.local_db_port}"
                f"/{settings.local_db_name}"
            )
        
        # Production: Use AWS Secrets Manager
        print(f"☁️ AWS database (region: {settings.aws_region})")
        from config.aws_config import DatabaseConfig
        
        return (
            f"mysql+mysqlconnector://"
            f"{DatabaseConfig.get_username()}:{DatabaseConfig.get_password()}"
            f"@{DatabaseConfig.get_host()}:{DatabaseConfig.get_port()}"
            f"/{DatabaseConfig.get_database()}"
        )

    @classmethod
    def get_engine(cls):
        """Get or create SQLAlchemy engine"""
        if cls._engine is None:
            url = cls.get_database_url()
            cls._engine = create_engine(
                url,
                pool_size=5,
                pool_recycle=3600,
                pool_pre_ping=True,
            )
            print(f"✅ SQLAlchemy engine created")
        return cls._engine

    @classmethod
    def get_session_local(cls):
        """Get SessionLocal class"""
        if cls._SessionLocal is None:
            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls.get_engine(),
            )
        return cls._SessionLocal

    @classmethod
    @contextmanager
    def get_session(cls) -> Generator[Session, None, None]:
        """
        Get database session with context manager

        Usage:
            with Database.get_session() as db:
                db.query(Model).all()
        """
        SessionLocal = cls.get_session_local()
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def create_tables(cls):
        """Create all tables from models"""
        from database.models import Base

        engine = cls.get_engine()
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created/verified")


# Convenience function for FastAPI dependency injection
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    with Database.get_session() as session:
        yield session
