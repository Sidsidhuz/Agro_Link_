"""AgroLink web app and API. Start with ``uvicorn main:app --reload``."""
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import os
import secrets

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import database

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
UPLOADS = BASE / "data" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)


def session_secret():
    configured = os.getenv("AGROLINK_SESSION_SECRET")
    if configured:
        return configured
    secret_file = BASE / "data" / "session.key"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if not secret_file.exists():
        try:
            with secret_file.open("x") as stream:
                stream.write(secrets.token_urlsafe(48))
            secret_file.chmod(0o600)
        except FileExistsError:
            pass
    return secret_file.read_text().strip()


def distance_km(lat1, lon1, lat2, lon2):
    a = sin(radians(lat2 - lat1) / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * asin(min(1, sqrt(a)))


from app.main import create_app

app = create_app(initialize_legacy_database=database.init_db, development_secret=session_secret, legacy_database_path=lambda: database.DB_PATH)
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
