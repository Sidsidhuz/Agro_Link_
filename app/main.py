"""Application factory. Legacy business routes are migrated incrementally."""
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import Settings
from app.core.database import build_engine, build_session_factory
from app.core.exception_handlers import register_exception_handlers


def create_app(*, initialize_legacy_database, development_secret, settings=None, legacy_database_path=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        # Temporary bridge: existing routes still use the original SQLite schema.
        await run_in_threadpool(initialize_legacy_database)
        database_settings = settings.database
        if legacy_database_path:
            # All migrated and legacy routes must use the same database during transition.
            database_settings = database_settings.model_copy(update={'url': 'sqlite+aiosqlite:///' + legacy_database_path().as_posix()})
        engine = build_engine(database_settings)
        app.state.session_factory = build_session_factory(engine)
        try:
            async with httpx.AsyncClient(timeout=5, limits=httpx.Limits(
                    max_connections=50, max_keepalive_connections=10)) as client:
                app.state.http_client = client
                yield
        finally:
            await engine.dispose()

    app = FastAPI(title='AgroLink', version='2.1', lifespan=lifespan)
    app.state.settings = settings
    secret = settings.auth.secret.get_secret_value() if settings.auth.secret else development_secret()
    app.add_middleware(SessionMiddleware, secret_key=secret, same_site='lax',
                       https_only=settings.auth.secure_cookie, max_age=settings.auth.max_age)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=True, allow_methods=['GET', 'POST', 'PATCH'],
                       allow_headers=['Content-Type', 'X-CSRF-Token'])
    register_exception_handlers(app)

    from app.api.v1.endpoints.auth import router as auth_router
    from app.api.v1.endpoints.features import router as features_router

    # Versioned routes
    app.include_router(auth_router, prefix='/api/v1', tags=['Accounts'])
    app.include_router(features_router, prefix='/api/v1', tags=['Features'])

    # Backward-compatible aliases at /api
    app.include_router(auth_router, prefix='/api', include_in_schema=False)
    app.include_router(features_router, prefix='/api', include_in_schema=False)

    return app
