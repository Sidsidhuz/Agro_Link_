# Architecture status

## Fully migrated (async, endpoint → service → repository)

All routes now use async SQLAlchemy through the layered architecture:

- **Accounts**: register, login, logout, profile reads, profile updates
- **Feed**: posts feed, create post, toggle like, get/add comments
- **Users**: avatar upload, user search, public profiles
- **Planner**: planting windows, crop model list
- **Diagnosis**: ML prediction, disease reporting to nearby farmers
- **Alerts**: view and mark-read disease alerts
- **Diary**: create and list farm diary entries
- **Weather**: async weather fetch via httpx
- **Messages**: conversations list, chat threads, send messages

Routes are served at both `/api/v1` (versioned) and `/api` (backward-compatible).

## Architecture layers

```
app/api/v1/endpoints/  →  API routers (auth.py, features.py)
app/api/dependencies.py  →  DI factories for services
app/schemas/            →  Pydantic request/response models
app/services/           →  Business logic, transaction boundaries
app/repositories/       →  Data access via async SQLAlchemy
app/models/             →  SQLAlchemy ORM models
app/core/               →  Config, database, exceptions, error handlers
main.py                 →  Entry point: app factory, static mounts, index route
```

## Database

The legacy SQLite schema created by `database.init_db()` is still the source of
truth. All async routes share the same database file via the transitional bridge
in `create_app`. Alembic is configured but no migrations have run yet.

## Frontend

Dark-mode visual redesign using Inter + Outfit fonts, emerald-green accent
palette, glassmorphism effects, gradient branding, and responsive layout.

## Remaining work

- CSRF enforcement
- Shared rate limiting
- Alembic baseline migration against a database copy
- Durable background job design
- Deployment validation (HTTPS, production session settings, content moderation)

Run as before: `.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000`
