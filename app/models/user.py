from sqlalchemy import Integer, String, Float, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(60))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    place: Mapped[str] = mapped_column(String, default="")
    crops: Mapped[str] = mapped_column(String, default="")
    about: Mapped[str] = mapped_column(String, default="")
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    irrigation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String, server_default=text("CURRENT_TIMESTAMP"))

