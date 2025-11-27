"""
Database setup script - Creates tables using SQLAlchemy
"""
from database.connection import Database


def create_tables():
    """Create all tables from SQLAlchemy models"""
    Database.create_tables()


def drop_tables():
    """Drop all tables (use with caution!)"""
    from database.models import Base

    engine = Database.get_engine()
    Base.metadata.drop_all(bind=engine)
    print("🗑️ All tables dropped")


def reset_tables():
    """Drop and recreate all tables"""
    drop_tables()
    create_tables()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("⚠️ Resetting database tables...")
        reset_tables()
    else:
        print("📦 Setting up database tables...")
        create_tables()

    print("✅ Database setup complete!")
