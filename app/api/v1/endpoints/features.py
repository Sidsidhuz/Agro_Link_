"""All feature routes migrated from root main.py to async endpoints."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.api.dependencies import (
    feed_service, profile_service, diagnose_service,
    alert_service, diary_service, message_service, user_service,
)
from app.schemas.features import CommentCreate, DiaryCreate, MessageCreate

import guidance
import ml
import planner

router = APIRouter()

BASE = Path(__file__).resolve().parents[4]
UPLOADS = BASE / "data" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

async def _current_user(request: Request, service=Depends(user_service)):
    return await service.current(request.session.get("user_id"))


# ── avatar & user search ────────────────────────────────────────────────────

@router.post("/me/avatar")
async def upload_avatar(image: UploadFile = File(...),
                        user=Depends(_current_user),
                        service=Depends(profile_service)):
    return await service.upload_avatar(user.id, image, UPLOADS)


@router.get("/users")
async def search_users(q: str = "", user=Depends(_current_user),
                       service=Depends(profile_service)):
    return {"users": await service.search_users(q, user.id)}


@router.get("/users/{user_id}")
async def profile(user_id: int, user=Depends(_current_user),
                  service=Depends(profile_service)):
    return await service.public_profile(user_id, user.id)


# ── feed & posts ─────────────────────────────────────────────────────────────

@router.get("/feed")
async def feed(user=Depends(_current_user), service=Depends(feed_service)):
    return {"posts": await service.feed(user.id)}


@router.post("/posts", status_code=201)
async def add_post(image: UploadFile = File(...),
                   caption: str = Form(""), crop: str = Form(""),
                   prediction: str = Form(""),
                   user=Depends(_current_user),
                   service=Depends(feed_service)):
    return await service.add_post(user.id, image, caption, crop, prediction, UPLOADS)


@router.post("/posts/{post_id}/like")
async def toggle_like(post_id: int, user=Depends(_current_user),
                      service=Depends(feed_service)):
    return await service.toggle_like(post_id, user.id)


@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: int, user=Depends(_current_user),
                       service=Depends(feed_service)):
    return {"comments": await service.comments(post_id, user.id)}


@router.post("/posts/{post_id}/comments", status_code=201)
async def add_comment(post_id: int, data: CommentCreate,
                      user=Depends(_current_user),
                      service=Depends(feed_service)):
    return await service.add_comment(post_id, user.id, data.body)


# ── planner & crops ──────────────────────────────────────────────────────────

@router.get("/crops")
async def crops(user=Depends(_current_user)):
    return {"crops": [{"name": crop, "available": ml.weight_path(crop).is_file()} for crop in ml.LABELS]}


@router.get("/planner")
async def planting_plan(user=Depends(_current_user)):
    selected = [name.strip() for name in user.crops.split(",") if name.strip()]
    return {
        "windows": [planner.next_window(crop, bool(user.irrigation)) for crop in selected],
        "region": "Kerala guidance; confirm field conditions locally",
    }


# ── diagnosis & alerts ───────────────────────────────────────────────────────

@router.post("/predict")
async def predict(crop: str = Form(...), image: UploadFile = File(...),
                  user=Depends(_current_user),
                  service=Depends(diagnose_service)):
    return await service.predict(user.id, crop, image, UPLOADS, ml, guidance)


@router.post("/diagnoses/{diagnosis_id}/report")
async def report_diagnosis(diagnosis_id: int, user=Depends(_current_user),
                           service=Depends(diagnose_service)):
    return await service.report(diagnosis_id, user)


@router.get("/alerts")
async def alerts(user=Depends(_current_user), service=Depends(alert_service)):
    return {"alerts": await service.for_user(user.id)}


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, user=Depends(_current_user),
                          service=Depends(alert_service)):
    return await service.mark_read(alert_id, user.id)


# ── diary ────────────────────────────────────────────────────────────────────

@router.get("/diary")
async def diary(user=Depends(_current_user), service=Depends(diary_service)):
    return {"entries": await service.for_user(user.id)}


@router.post("/diary", status_code=201)
async def add_diary(data: DiaryCreate, user=Depends(_current_user),
                    service=Depends(diary_service)):
    return await service.add(user.id, data)


# ── weather ──────────────────────────────────────────────────────────────────

@router.get("/weather")
async def weather(request: Request, user=Depends(_current_user)):
    from app.services.features import WeatherService
    return await WeatherService.fetch(user, request.app.state.http_client)


@router.get("/weather/forecast")
async def weather_forecast(request: Request, user=Depends(_current_user)):
    from app.services.features import WeatherService
    return await WeatherService.forecast(user, request.app.state.http_client)


# ── messages ─────────────────────────────────────────────────────────────────

@router.get("/conversations")
async def conversations(user=Depends(_current_user),
                        service=Depends(message_service)):
    return {"users": await service.conversations(user.id)}


@router.get("/messages/{other_id}")
async def messages(other_id: int, user=Depends(_current_user),
                   service=Depends(message_service)):
    return await service.thread(user.id, other_id)


@router.post("/messages/{other_id}", status_code=201)
async def send_message(other_id: int, data: MessageCreate,
                       user=Depends(_current_user),
                       service=Depends(message_service)):
    return await service.send(user.id, other_id, data.body)
