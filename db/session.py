from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Add connection pooling optimized for remote databases (like Render)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using them (crucial for remote DBs)
    pool_size=2,             # Smaller pool for free tier databases
    max_overflow=3,          # Limited overflow for free tier
    pool_recycle=300,        # Recycle connections after 5 minutes (remote DBs timeout faster)
    pool_timeout=60,         # Wait up to 60 seconds for a connection (important for cold starts)
    connect_args={
        "connect_timeout": 10,  # 10 second timeout for initial connection
        "options": "-c statement_timeout=30000"  # 30 second query timeout
    },
    echo=False               # Set to True for SQL query debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
