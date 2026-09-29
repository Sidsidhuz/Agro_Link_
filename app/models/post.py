from sqlalchemy import Integer, String, Float, Boolean, Text, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    caption: Mapped[str] = mapped_column(String, default="")
    crop: Mapped[str | None] = mapped_column(String, nullable=True)
    prediction: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))


class Like(Base):
    __tablename__ = "likes"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), primary_key=True)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    crop: Mapped[str] = mapped_column(String, nullable=False)
    prediction: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    reported_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    diagnosis_id: Mapped[int] = mapped_column(Integer, ForeignKey("diagnoses.id"), nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    is_read: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))


class Diary(Base):
    __tablename__ = "diary"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    crop: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))
