from sqlalchemy import select, func, text, delete, and_
from app.models.user import User
from app.models.post import Post, Like, Comment, Diagnosis, Alert, Diary, Message


class PostRepository:
    def __init__(self, session):
        self.session = session

    async def feed(self, viewer_id, limit=100):
        query = text("""
            SELECT p.id, p.image, p.caption, p.crop, p.prediction, p.created_at,
                u.id AS user_id, u.username, u.avatar,
                (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) AS likes_count,
                EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=:viewer) AS liked_by_me,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id) AS comments_count
            FROM posts p JOIN users u ON u.id=p.user_id
            ORDER BY p.created_at DESC, p.id DESC LIMIT :lim
        """)
        result = await self.session.execute(query, {"viewer": viewer_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def user_posts(self, user_id, viewer_id, limit=100):
        query = text("""
            SELECT p.id, p.image, p.caption, p.crop, p.prediction, p.created_at,
                u.id AS user_id, u.username, u.avatar,
                (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) AS likes_count,
                EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=:viewer) AS liked_by_me,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id) AS comments_count
            FROM posts p JOIN users u ON u.id=p.user_id
            WHERE p.user_id=:uid ORDER BY p.created_at DESC, p.id DESC LIMIT :lim
        """)
        result = await self.session.execute(query, {"uid": user_id, "viewer": viewer_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def exists(self, post_id):
        return await self.session.scalar(text("SELECT 1 FROM posts WHERE id=:pid"), {"pid": post_id}) is not None

    async def add(self, user_id, image, caption, crop, prediction):
        result = await self.session.execute(
            text("INSERT INTO posts (user_id, image, caption, crop, prediction) VALUES (:uid, :img, :cap, :crop, :pred)"),
            {"uid": user_id, "img": image, "cap": caption, "crop": crop, "pred": prediction})
        await self.session.commit()
        return result.lastrowid

    async def toggle_like(self, post_id, user_id):
        current = await self.session.scalar(
            text("SELECT 1 FROM likes WHERE post_id=:pid AND user_id=:uid"),
            {"pid": post_id, "uid": user_id})
        if current:
            await self.session.execute(
                text("DELETE FROM likes WHERE post_id=:pid AND user_id=:uid"),
                {"pid": post_id, "uid": user_id})
        else:
            await self.session.execute(
                text("INSERT INTO likes (post_id, user_id) VALUES (:pid, :uid)"),
                {"pid": post_id, "uid": user_id})
        count = await self.session.scalar(
            text("SELECT COUNT(*) FROM likes WHERE post_id=:pid"), {"pid": post_id})
        await self.session.commit()
        return not bool(current), count

    async def comments(self, post_id, limit=200):
        result = await self.session.execute(text("""
            SELECT c.id, c.body, c.created_at, u.username FROM comments c
            JOIN users u ON u.id=c.user_id WHERE c.post_id=:pid ORDER BY c.id ASC LIMIT :lim
        """), {"pid": post_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def add_comment(self, post_id, user_id, body):
        result = await self.session.execute(
            text("INSERT INTO comments (post_id, user_id, body) VALUES (:pid, :uid, :body)"),
            {"pid": post_id, "uid": user_id, "body": body})
        await self.session.commit()
        return result.lastrowid


class DiagnosisRepository:
    def __init__(self, session):
        self.session = session

    async def add(self, user_id, crop, prediction, confidence, image):
        result = await self.session.execute(
            text("INSERT INTO diagnoses (user_id, crop, prediction, confidence, image) VALUES (:uid, :crop, :pred, :conf, :img)"),
            {"uid": user_id, "crop": crop, "pred": prediction, "conf": confidence, "img": image})
        await self.session.commit()
        return result.lastrowid

    async def by_id_and_owner(self, diagnosis_id, user_id):
        result = await self.session.execute(
            text("SELECT * FROM diagnoses WHERE id=:did AND user_id=:uid"),
            {"did": diagnosis_id, "uid": user_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def mark_reported(self, diagnosis_id):
        await self.session.execute(
            text("UPDATE diagnoses SET reported_at=CURRENT_TIMESTAMP WHERE id=:did"),
            {"did": diagnosis_id})

    async def has_recent_alert(self, recipient_id, crop, prediction):
        return await self.session.scalar(text("""
            SELECT 1 FROM alerts a JOIN diagnoses d ON d.id=a.diagnosis_id
            WHERE a.recipient_id=:rid AND d.crop=:crop AND d.prediction=:pred
            AND a.created_at>=datetime('now', '-48 hours') LIMIT 1
        """), {"rid": recipient_id, "crop": crop, "pred": prediction}) is not None

    async def add_alert(self, recipient_id, diagnosis_id, distance_km):
        await self.session.execute(
            text("INSERT INTO alerts (recipient_id, diagnosis_id, distance_km) VALUES (:rid, :did, :dist)"),
            {"rid": recipient_id, "did": diagnosis_id, "dist": distance_km})


class AlertRepository:
    def __init__(self, session):
        self.session = session

    async def for_user(self, user_id, limit=100):
        result = await self.session.execute(text("""
            SELECT a.id, a.distance_km, a.is_read, a.created_at,
                d.crop, d.prediction FROM alerts a JOIN diagnoses d ON d.id=a.diagnosis_id
            WHERE a.recipient_id=:uid ORDER BY a.id DESC LIMIT :lim
        """), {"uid": user_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def mark_read(self, alert_id, user_id):
        await self.session.execute(
            text("UPDATE alerts SET is_read=1 WHERE id=:aid AND recipient_id=:uid"),
            {"aid": alert_id, "uid": user_id})
        await self.session.commit()


class DiaryRepository:
    def __init__(self, session):
        self.session = session

    async def for_user(self, user_id, limit=100):
        result = await self.session.execute(text(
            "SELECT id, crop, event_date, note FROM diary WHERE user_id=:uid ORDER BY event_date DESC, id DESC LIMIT :lim"),
            {"uid": user_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def add(self, user_id, crop, event_date, note):
        result = await self.session.execute(
            text("INSERT INTO diary (user_id, crop, event_date, note) VALUES (:uid, :crop, :date, :note)"),
            {"uid": user_id, "crop": crop, "date": event_date, "note": note})
        await self.session.commit()
        return result.lastrowid


class MessageRepository:
    def __init__(self, session):
        self.session = session

    async def conversations(self, user_id):
        result = await self.session.execute(text("""
            SELECT u.id, u.username, u.avatar, MAX(m.id) AS latest_id
            FROM messages m JOIN users u ON u.id=CASE WHEN m.sender_id=:uid THEN m.receiver_id ELSE m.sender_id END
            WHERE m.sender_id=:uid OR m.receiver_id=:uid GROUP BY u.id ORDER BY latest_id DESC
        """), {"uid": user_id})
        return [dict(row._mapping) for row in result.fetchall()]

    async def thread(self, user_id, other_id, limit=300):
        result = await self.session.execute(text("""
            SELECT id, sender_id, receiver_id, body, created_at FROM messages
            WHERE (sender_id=:uid AND receiver_id=:oid) OR (sender_id=:oid AND receiver_id=:uid)
            ORDER BY id ASC LIMIT :lim
        """), {"uid": user_id, "oid": other_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def send(self, sender_id, receiver_id, body):
        result = await self.session.execute(
            text("INSERT INTO messages (sender_id, receiver_id, body) VALUES (:sid, :rid, :body)"),
            {"sid": sender_id, "rid": receiver_id, "body": body})
        await self.session.commit()
        return result.lastrowid


class UserQueryRepository:
    """Read-only queries for public user profiles and search."""
    def __init__(self, session):
        self.session = session

    async def search(self, term, exclude_id, limit=20):
        result = await self.session.execute(text(
            "SELECT id, username, place, crops, about, avatar FROM users WHERE username LIKE :term AND id!=:eid ORDER BY username LIMIT :lim"),
            {"term": f"%{term}%", "eid": exclude_id, "lim": limit})
        return [dict(row._mapping) for row in result.fetchall()]

    async def public_profile(self, user_id):
        result = await self.session.execute(text(
            "SELECT id, username, place, crops, about, avatar FROM users WHERE id=:uid"),
            {"uid": user_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def by_id_basic(self, user_id):
        result = await self.session.execute(text(
            "SELECT id, username, avatar FROM users WHERE id=:uid"), {"uid": user_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def neighbors_with_location(self, exclude_id):
        result = await self.session.execute(text(
            "SELECT id, latitude, longitude FROM users WHERE id!=:eid AND latitude IS NOT NULL AND longitude IS NOT NULL"),
            {"eid": exclude_id})
        return [dict(row._mapping) for row in result.fetchall()]

    async def update_avatar(self, user_id, avatar_path):
        await self.session.execute(
            text("UPDATE users SET avatar=:path WHERE id=:uid"),
            {"path": avatar_path, "uid": user_id})
        await self.session.commit()
