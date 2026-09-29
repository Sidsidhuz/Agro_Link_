"""Async migration runner. Baseline mapping must precede autogeneration."""
import asyncio
from alembic import context
from app.core.config import Settings
from app.core.database import build_engine
from app.models import Base


def run(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def online():
    engine = build_engine(Settings().database)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run)
    finally:
        await engine.dispose()


if not Base.metadata.tables:
    raise RuntimeError('Migration baseline is not mapped yet. Do not migrate or autogenerate against the existing database.')
if context.is_offline_mode():
    context.configure(url=Settings().database.url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(online())
