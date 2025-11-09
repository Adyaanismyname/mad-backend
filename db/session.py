from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings
from typing import AsyncGenerator

# Create async engine with asyncpg driver
print(settings.DATABASE_URL)
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using them (crucial for remote DBs)
    pool_size=2,             # Smaller pool for free tier databases
    max_overflow=3,          # Limited overflow for free tier
    pool_recycle=300,        # Recycle connections after 5 minutes (remote DBs timeout faster)
    pool_timeout=60,         # Wait up to 60 seconds for a connection (important for cold starts)
    echo=False               # Set to True for SQL query debugging
)

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
