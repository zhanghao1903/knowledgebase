"""Initialize database tables directly (for development without Alembic)."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database import engine, Base
import app.models  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
