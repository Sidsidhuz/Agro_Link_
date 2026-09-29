from io import BytesIO
from datetime import date

from fastapi.testclient import TestClient
from PIL import Image

import database
import main
import ml
import planner


def photo():
    stream = BytesIO()
    Image.new("RGB", (12, 12), "green").save(stream, "PNG")
    return stream.getvalue()


def signup(client, name, phone, latitude, longitude):
    response = client.post("/api/register", json={"username": name, "phone": phone,
        "password": "good-password", "place": "Kannur, Kerala", "crops": "Banana,Corn",
        "latitude": latitude, "longitude": longitude, "irrigation": False})
    assert response.status_code == 201, response.text
    return response.json()


def test_community_and_nearby_alerts(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr(main, "UPLOADS", tmp_path / "uploads")
    main.UPLOADS.mkdir()
    model = tmp_path / "Banana_disease.pth"
    model.write_bytes(b"test placeholder")
    monkeypatch.setattr(ml, "weight_path", lambda crop: model if crop == "Banana" else tmp_path / "missing.pth")
    monkeypatch.setattr(ml, "predict", lambda crop, path: {"prediction": "sigatoka", "confidence": 0.94})

    with TestClient(main.app) as author, TestClient(main.app) as near, TestClient(main.app) as far:
        assert author.get("/api/feed").status_code == 401
        farmer = signup(author, "Farmer One", "1111111111", 11.8745, 75.3704)
        signup(near, "Nearby", "2222222222", 11.89, 75.38)
        signup(far, "Faraway", "3333333333", 12.2, 75.8)
        assert author.get("/").status_code == 200
        assert author.get("/api/me").json()["id"] == farmer["id"]
        assert author.get("/api/planner").json()["windows"][0]["supported"] is True
        assert author.get("/api/users?q=Near").json()["users"][0]["username"] == "Nearby"
        assert "phone" not in author.get("/api/users?q=Near").text

        result = author.post("/api/posts", data={"caption": "My banana crop", "crop": "Banana"},
            files={"image": ("leaf.png", photo(), "image/png")})
        assert result.status_code == 201
        assert near.get("/api/feed").json()["posts"][0]["caption"] == "My banana crop"
        post_id = result.json()["id"]
        assert near.post(f"/api/posts/{post_id}/like").json() == {"liked": True, "count": 1}
        assert near.post(f"/api/posts/{post_id}/comments", json={"body": "Looks great"}).status_code == 201
        assert author.get(f"/api/posts/{post_id}/comments").json()["comments"][0]["body"] == "Looks great"
        assert author.get("/api/feed").json()["posts"][0]["likes_count"] == 1
        assert author.post("/api/posts", files={"image": ("fake.png", b"not an image", "image/png")}).status_code == 400
        assert author.post("/api/diary", json={"crop": "Banana", "event_date": "2026-09-29", "note": "Checked leaves"}).status_code == 201
        assert author.get("/api/diary").json()["entries"][0]["note"] == "Checked leaves"
        diagnosis = author.post("/api/predict", data={"crop": "Banana"},
            files={"image": ("leaf.png", photo(), "image/png")})
        assert diagnosis.status_code == 200, diagnosis.text
        assert diagnosis.json()["guidance"]["status"] == "source_matched"
        diagnosis_id = diagnosis.json()["id"]
        assert near.post(f"/api/diagnoses/{diagnosis_id}/report").status_code == 404
        reported = author.post(f"/api/diagnoses/{diagnosis_id}/report")
        assert reported.json()["sent"] == 1
        assert author.post(f"/api/diagnoses/{diagnosis_id}/report").status_code == 409
        assert len(near.get("/api/alerts").json()["alerts"]) == 1
        assert far.get("/api/alerts").json()["alerts"] == []
        alert = near.get("/api/alerts").json()["alerts"][0]
        assert "latitude" not in alert and "longitude" not in alert
        assert near.post(f"/api/alerts/{alert['id']}/read").status_code == 200
        assert near.get("/api/alerts").json()["alerts"][0]["is_read"] == 1
        second = author.post("/api/predict", data={"crop": "Banana"},
            files={"image": ("leaf.png", photo(), "image/png")}).json()
        assert author.post(f"/api/diagnoses/{second['id']}/report").json()["sent"] == 0
        assert author.post(f"/api/messages/{far.get('/api/me').json()['id']}", json={"body": "Hello"}).status_code == 201
        assert len(far.get("/api/conversations").json()["users"]) == 1
        author.post("/api/logout")
        assert author.get("/api/me").status_code == 401
        assert author.post("/api/login", json={"phone": "1111111111", "password": "good-password"}).status_code == 200


def test_planting_window():
    result = planner.next_window("Banana", False, date(2026, 3, 10))
    assert result["start"] == "2026-04-01" and result["prepare_now"] is True
    assert planner.next_window("Grapes", False)["supported"] is False
    assert main.distance_km(11.8745, 75.3704, 11.8745, 75.4104) < 5
    assert main.distance_km(11.8745, 75.3704, 11.8745, 75.4204) > 5
