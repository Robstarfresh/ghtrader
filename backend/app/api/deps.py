"""FastAPI dependencies shared across routes."""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

# Re-export the standard DB dependency so routes only need to import from deps.
DbSession = AsyncGenerator[AsyncSession, None]


async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Yield an async SQLAlchemy session."""
    return session
