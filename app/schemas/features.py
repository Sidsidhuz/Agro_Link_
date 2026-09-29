from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    caption: str = Field(default="", max_length=1000)
    crop: str = Field(default="", max_length=40)
    prediction: str = Field(default="", max_length=120)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image: str
    caption: str
    crop: str | None
    prediction: str | None
    created_at: str
    user_id: int
    username: str
    avatar: str | None
    likes_count: int
    liked_by_me: bool
    comments_count: int


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    body: str = Field(min_length=1, max_length=500)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    body: str
    created_at: str
    username: str


class DiaryCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    crop: str = Field(min_length=1, max_length=40)
    event_date: date
    note: str = Field(min_length=1, max_length=1000)


class DiaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop: str
    event_date: str
    note: str


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    body: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_id: int
    receiver_id: int
    body: str
    created_at: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    distance_km: float
    is_read: int
    created_at: str
    crop: str
    prediction: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    place: str
    crops: str
    about: str
    avatar: str | None


class CropInfo(BaseModel):
    name: str
    available: bool
