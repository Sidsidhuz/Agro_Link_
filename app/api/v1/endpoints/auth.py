from fastapi import APIRouter, Depends, Request
from app.api.dependencies import user_service
from app.schemas.auth import Register, Login, ProfileUpdate, UserPrivate

router = APIRouter()

@router.post('/register', response_model=UserPrivate, status_code=201)
async def register(data: Register, request: Request, service=Depends(user_service)):
    user = await service.register(data)
    request.session.clear()
    request.session['user_id'] = user.id
    return user

@router.post('/login', response_model=UserPrivate)
async def login(data: Login, request: Request, service=Depends(user_service)):
    user = await service.login(data)
    request.session.clear()
    request.session['user_id'] = user.id
    return user

@router.post('/logout')
async def logout(request: Request):
    request.session.clear()
    return {'ok': True}

@router.get('/me', response_model=UserPrivate)
async def me(request: Request, service=Depends(user_service)):
    return await service.current(request.session.get('user_id'))

@router.patch('/me', response_model=UserPrivate)
async def update_me(data: ProfileUpdate, request: Request, service=Depends(user_service)):
    return await service.update(request.session.get('user_id'), data)
