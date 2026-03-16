"""
database.py — Async SQLAlchemy Database Session
=================================================

Provides:
  - async engine + session factory
  - PostGIS extension initialization on startup
  - Dependency injection helper: `get_db()`

Usage in route handlers:
    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from config import settings


# ---- Engine & Session Factory ----

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---- Startup ----

async def init_db() -> None:
    """
    Create all tables and enable PostGIS extension.
    Call on application startup.
    """
    from models.db_models import Base  # import here to avoid circular imports

    async with engine.begin() as conn:
        # Enable PostGIS if not already
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the engine pool on shutdown."""
    await engine.dispose()


# ---- Dependency ----

async def get_db() -> AsyncSession:  # type: ignore[return]
    """
    Async database session dependency for FastAPI route handlers.

    Automatically commits on success, rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
