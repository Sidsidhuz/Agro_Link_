from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from werkzeug.security import generate_password_hash, check_password_hash
from app.core.exceptions import AppError
from app.repositories.users import UserRepository

class UserService:
    def __init__(self, session):
        self.session = session
        self.users = UserRepository(session)

    async def current(self, user_id):
        user = await self.users.by_id(user_id) if user_id else None
        if user is None:
            raise AppError('Please log in', 401)
        return user

    async def register(self, data):
        values = data.model_dump(exclude={'password'})
        for key in ('username', 'phone', 'place', 'crops', 'about'):
            values[key] = values[key].strip()
        if not values['phone']:
            raise AppError('Phone is required')
        values['password_hash'] = await run_in_threadpool(generate_password_hash, data.password)
        try:
            user = await self.users.add(values)
            await self.session.commit()
            return user
        except IntegrityError:
            await self.session.rollback()
            if await self.users.by_phone(values['phone']):
                raise AppError('Phone number is already registered', 409)
            raise

    async def login(self, data):
        user = await self.users.by_phone(data.phone.strip())
        if not user or not await run_in_threadpool(check_password_hash, user.password_hash, data.password):
            raise AppError('Invalid phone number or password', 401)
        return user

    async def update(self, user_id, data):
        user = await self.current(user_id)
        for key, value in data.model_dump().items():
            setattr(user, key, value.strip() if isinstance(value, str) else value)
        await self.session.commit()
        return user
