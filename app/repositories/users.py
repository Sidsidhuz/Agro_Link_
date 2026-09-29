from sqlalchemy import select
from app.models.user import User

class UserRepository:
    def __init__(self, session):
        self.session = session

    async def by_id(self, user_id):
        return await self.session.get(User, user_id)

    async def by_phone(self, phone):
        return await self.session.scalar(select(User).where(User.phone == phone))

    async def add(self, values):
        user = User(**values)
        self.session.add(user)
        await self.session.flush()
        return user
