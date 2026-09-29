import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from sqlalchemy import text

from app.core.config import Settings, DatabaseSettings
from app.core.database import build_engine, build_session_factory
from app.core.exception_handlers import register_exception_handlers


def test_production_requires_secret_and_secure_cookie():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment='production')


def test_error_responses_do_not_echo_secrets():
    app = FastAPI()
    register_exception_handlers(app)

    class Payload(BaseModel):
        password: int

    @app.post('/validate')
    def validate(payload: Payload):
        return {}

    @app.get('/fail')
    def fail():
        raise RuntimeError('private database credentials')

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post('/validate', json={'password': 'secret-value'})
        assert response.status_code == 422
        assert 'secret-value' not in response.text
        response = client.get('/fail')
        assert response.status_code == 500
        assert response.json() == {'status': 'error', 'message': 'An unexpected error occurred', 'details': []}


def test_async_session_rolls_back_uncommitted_work():
    async def check():
        engine = build_engine(DatabaseSettings(url='sqlite+aiosqlite:///:memory:'))
        try:
            async with engine.begin() as connection:
                await connection.execute(text('CREATE TABLE sample (id INTEGER)'))
            sessions = build_session_factory(engine)
            async with sessions() as session:
                await session.execute(text('INSERT INTO sample VALUES (1)'))
            async with sessions() as session:
                assert await session.scalar(text('SELECT COUNT(*) FROM sample')) == 0
        finally:
            await engine.dispose()
    asyncio.run(check())
