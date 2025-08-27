"""
Database connection and session management
"""

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=not settings.PRODUCTION,  # SQL logging in development
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass

async def init_db():
    """Initialize database connection and verify connectivity"""
    try:
        async with engine.begin() as conn:
            # Test the connection
            await conn.execute("SELECT 1")
        logger.info("✅ Database connection established successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with get_db_session() as session:
        yield session

# Direct connection for raw queries when needed
async def get_db_connection():
    """Get direct asyncpg connection for raw SQL queries"""
    return await asyncpg.connect(settings.DATABASE_URL)