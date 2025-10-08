"""
Database initialization script.
Run this to create all tables in the database.
"""
from db.base import Base
from db.session import engine
# Import all models here so they are registered with Base
from models.user import User


def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")


if __name__ == "__main__":
    init_db()
