import os
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.config import settings

# Ensure data directory exists if using local SQLite file
if "sqlite" in settings.DATABASE_URL and not settings.DATABASE_URL.startswith("sqlite+aiosqlite:///:memory:"):
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    parent_dir = Path(db_path).parent
    parent_dir.mkdir(parents=True, exist_ok=True)

# Build engine with database-appropriate parameters
engine_kwargs = {
    "echo": settings.DB_ECHO,
    "future": True,
}

if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL pooling parameters
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
    engine_kwargs["pool_pre_ping"] = True

async_engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an isolated async database session with automatic cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    # Ensure all domain models are imported so SQLModel metadata registers all tables
    import backend.app.auth.models  # noqa: F401
    import backend.app.learning_state.models  # noqa: F401
    import backend.app.curriculum.models  # noqa: F401
    import backend.app.rag.models  # noqa: F401
    import backend.app.questions.models  # noqa: F401
    import backend.app.mastery.models  # noqa: F401
    import backend.app.errors.models  # noqa: F401
    import backend.app.tutor.models  # noqa: F401
    import backend.app.revision.models  # noqa: F401
    import backend.app.teach_back.models  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)



