from fastapi import Depends
from app.core.database import get_session
from app.services.users import UserService
from app.services.features import (
    FeedService, ProfileService, DiagnoseService,
    AlertService, DiaryService, MessageService,
)


def user_service(session=Depends(get_session)):
    return UserService(session)


def feed_service(session=Depends(get_session)):
    return FeedService(session)


def profile_service(session=Depends(get_session)):
    return ProfileService(session)


def diagnose_service(session=Depends(get_session)):
    return DiagnoseService(session)


def alert_service(session=Depends(get_session)):
    return AlertService(session)


def diary_service(session=Depends(get_session)):
    return DiaryService(session)


def message_service(session=Depends(get_session)):
    return MessageService(session)
