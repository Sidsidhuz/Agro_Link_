from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DatabaseSettings


def build_engine(settings: DatabaseSettings):
    options = dict(pool_pre_ping=True, pool_recycle=settings.pool_recycle)
    if ':memory:' not in settings.url:
        options.update(pool_size=settings.pool_size, max_overflow=settings.max_overflow,
                       pool_timeout=settings.pool_timeout)
    engine = create_async_engine(settings.url, **options)
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine.sync_engine, 'connect')
        def configure_sqlite(connection, _record):
            cursor = connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.execute('PRAGMA busy_timeout=5000')
            cursor.close()
    return engine


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Services own commit boundaries; unfinished transactions are rolled back."""
    async with request.app.state.session_factory() as session:
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()


def build_session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
