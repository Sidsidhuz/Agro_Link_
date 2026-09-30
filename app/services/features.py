"""Business logic for all features migrated from root main.py."""
from io import BytesIO
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import uuid

from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError
from app.repositories.features import (
    PostRepository, DiagnosisRepository, AlertRepository,
    DiaryRepository, MessageRepository, UserQueryRepository,
)

MAX_IMAGE = 8 * 1024 * 1024


def _distance_km(lat1, lon1, lat2, lon2):
    a = sin(radians(lat2 - lat1) / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * asin(min(1, sqrt(a)))


async def _store_image(image, uploads_dir):
    """Validate and persist an uploaded image. Returns the public URL path."""
    payload = await run_in_threadpool(image.file.read, MAX_IMAGE + 1)
    if len(payload) > MAX_IMAGE:
        raise AppError("Image must be 8 MB or smaller", 413)
    try:
        with Image.open(BytesIO(payload)) as picture:
            picture.verify()
            format_name = picture.format
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError):
        raise AppError("Please choose a valid JPG, PNG, or WebP image", 400)
    extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(format_name)
    if extension is None:
        raise AppError("Please choose a JPG, PNG, or WebP image", 400)
    filename = f"{uuid.uuid4().hex}{extension}"
    await run_in_threadpool((uploads_dir / filename).write_bytes, payload)
    return f"/uploads/{filename}"


class FeedService:
    def __init__(self, session):
        self.posts = PostRepository(session)

    async def feed(self, user_id):
        return await self.posts.feed(user_id)

    async def add_post(self, user_id, image, caption, crop, prediction, uploads_dir):
        if len(caption) > 1000:
            raise AppError("Caption is too long", 400)
        if len(crop) > 40 or len(prediction) > 120:
            raise AppError("Crop or result is too long", 400)
        image_path = await _store_image(image, uploads_dir)
        post_id = await self.posts.add(user_id, image_path, caption.strip(), crop.strip(), prediction.strip())
        return {"id": post_id, "image": image_path}

    async def toggle_like(self, post_id, user_id):
        if not await self.posts.exists(post_id):
            raise AppError("Post not found", 404)
        liked, count = await self.posts.toggle_like(post_id, user_id)
        return {"liked": liked, "count": count}

    async def comments(self, post_id, user_id):
        if not await self.posts.exists(post_id):
            raise AppError("Post not found", 404)
        return await self.posts.comments(post_id)

    async def add_comment(self, post_id, user_id, body):
        body = body.strip()
        if not body:
            raise AppError("Comment cannot be blank", 400)
        if not await self.posts.exists(post_id):
            raise AppError("Post not found", 404)
        comment_id = await self.posts.add_comment(post_id, user_id, body)
        return {"id": comment_id}


class ProfileService:
    def __init__(self, session):
        self.users = UserQueryRepository(session)
        self.posts = PostRepository(session)

    async def search_users(self, query, user_id):
        term = query.strip()
        if not term:
            return []
        return await self.users.search(term, user_id)

    async def public_profile(self, user_id, viewer_id):
        user = await self.users.public_profile(user_id)
        if not user:
            raise AppError("User not found", 404)
        posts = await self.posts.user_posts(user_id, viewer_id)
        return {"user": user, "posts": posts}

    async def upload_avatar(self, user_id, image, uploads_dir):
        image_path = await _store_image(image, uploads_dir)
        await self.users.update_avatar(user_id, image_path)
        return {"avatar": image_path}


class DiagnoseService:
    def __init__(self, session):
        self.diagnoses = DiagnosisRepository(session)
        self.users = UserQueryRepository(session)

    async def predict(self, user_id, crop, image, uploads_dir, ml_module, guidance_module):
        if crop not in ml_module.LABELS:
            raise AppError("Choose Banana, Corn, or Grapes", 400)
        if not ml_module.weight_path(crop).is_file():
            raise AppError(f"{crop} model is not installed yet", 503)
        image_path = await _store_image(image, uploads_dir)
        try:
            result = await run_in_threadpool(
                ml_module.predict, crop, uploads_dir / Path(image_path).name)
        except (ImportError, ModuleNotFoundError):
            raise AppError("Install requirements-ml.txt to enable diagnosis", 503)
        except (RuntimeError, ValueError, OSError):
            raise AppError("Model could not be loaded; check the weight file and architecture", 503)
        diag_id = await self.diagnoses.add(user_id, crop, result["prediction"], result["confidence"], image_path)
        return {
            "id": diag_id, "crop": crop, "image": image_path,
            "guidance": guidance_module.for_result(crop, result["prediction"]),
            **result,
        }

    async def report(self, diagnosis_id, user):
        if user.latitude is None or user.longitude is None:
            raise AppError("Set your farm location in Profile before reporting", 400)
        diagnosis = await self.diagnoses.by_id_and_owner(diagnosis_id, user.id)
        if not diagnosis:
            raise AppError("Diagnosis not found", 404)
        if "healthy" in diagnosis["prediction"].lower():
            raise AppError("Healthy results cannot create disease alerts", 400)
        if diagnosis["reported_at"]:
            raise AppError("This result was already reported", 409)
        await self.diagnoses.mark_reported(diagnosis_id)
        neighbors = await self.users.neighbors_with_location(user.id)
        sent = 0
        for neighbor in neighbors:
            distance = _distance_km(user.latitude, user.longitude, neighbor["latitude"], neighbor["longitude"])
            if distance > 5:
                continue
            if await self.diagnoses.has_recent_alert(neighbor["id"], diagnosis["crop"], diagnosis["prediction"]):
                continue
            await self.diagnoses.add_alert(neighbor["id"], diagnosis_id, round(distance, 1))
            sent += 1
        from sqlalchemy.ext.asyncio import AsyncSession
        session = self.diagnoses.session
        await session.commit()
        return {"sent": sent, "message": "Nearby farmers were notified of a suspected disease"}


class AlertService:
    def __init__(self, session):
        self.alerts = AlertRepository(session)

    async def for_user(self, user_id):
        return await self.alerts.for_user(user_id)

    async def mark_read(self, alert_id, user_id):
        await self.alerts.mark_read(alert_id, user_id)
        return {"ok": True}


class DiaryService:
    def __init__(self, session):
        self.diary = DiaryRepository(session)

    async def for_user(self, user_id):
        return await self.diary.for_user(user_id)

    async def add(self, user_id, data):
        entry_id = await self.diary.add(
            user_id, data.crop.strip(), data.event_date.isoformat(), data.note.strip())
        return {"id": entry_id}


class MessageService:
    def __init__(self, session):
        self.messages = MessageRepository(session)
        self.users = UserQueryRepository(session)

    async def conversations(self, user_id):
        return await self.messages.conversations(user_id)

    async def thread(self, user_id, other_id):
        other = await self.users.by_id_basic(other_id)
        if not other:
            raise AppError("User not found", 404)
        messages = await self.messages.thread(user_id, other_id)
        return {"user": other, "messages": messages}

    async def send(self, user_id, other_id, body):
        if other_id == user_id:
            raise AppError("Choose another user", 400)
        other = await self.users.by_id_basic(other_id)
        if not other:
            raise AppError("User not found", 404)
        msg_id = await self.messages.send(user_id, other_id, body.strip())
        return {"id": msg_id}


class WeatherService:
    _forecast_cache = {}

    @staticmethod
    async def fetch(user, http_client):
        from urllib.parse import quote
        place = user.place.strip() if user.place else ""
        if not place:
            return {"place": "", "weather": "Add your location in Profile"}
        try:
            response = await http_client.get(
                f"https://wttr.in/{quote(place, safe='')}?format=%C+%t", timeout=5)
            value = response.text.strip() if response.status_code == 200 else "Weather unavailable"
        except Exception:
            value = "Weather unavailable"
        return {"place": place, "weather": value[:100]}

    @classmethod
    async def forecast(cls, user, http_client):
        """Use a geocoded town centre for forecasts; never transmit farm coordinates."""
        import time
        place = user.place.strip() if user.place else ""
        if not place:
            return {"place": "", "forecast": [], "source": "Open-Meteo"}
        cache_key = place.casefold()
        cached = cls._forecast_cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        try:
            geocoding = await http_client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": place, "count": 1, "language": "en", "format": "json"},
                timeout=5,
            )
            geocoding.raise_for_status()
            locations = geocoding.json().get("results", [])
            if not locations:
                return {"place": place, "forecast": [], "source": "Open-Meteo"}
            location = locations[0]
            response = await http_client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location["latitude"], "longitude": location["longitude"],
                    "daily": "weather_code,precipitation_probability_max,precipitation_sum,temperature_2m_max,temperature_2m_min",
                    "forecast_days": 16, "timezone": "auto",
                }, timeout=5,
            )
            response.raise_for_status()
            daily = response.json().get("daily", {})
            dates = daily.get("time", [])
            forecast = [{
                "date": value,
                "weather_code": daily.get("weather_code", [None] * len(dates))[index],
                "chance_of_rain": daily.get("precipitation_probability_max", [None] * len(dates))[index],
                "precipitation_mm": daily.get("precipitation_sum", [None] * len(dates))[index],
                "max_c": daily.get("temperature_2m_max", [None] * len(dates))[index],
                "min_c": daily.get("temperature_2m_min", [None] * len(dates))[index],
            } for index, value in enumerate(dates)]
            result = {
                "place": location.get("name", place), "forecast": forecast,
                "source": "Open-Meteo", "range_days": len(forecast),
            }
            cls._forecast_cache[cache_key] = (time.monotonic() + 1800, result)
            return result
        except Exception:
            return {"place": place, "forecast": [], "source": "Open-Meteo"}
