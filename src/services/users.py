from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.tables import User
from src.services.repository import SQLAlchemyRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = SQLAlchemyRepository(model=User, session=session)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repo.get_one_or_none(id=user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repo.get_one_or_none(email=email)

    async def create_user(
        self, email: str, password: str, full_name: str | None = None
    ) -> User:
        # Здесь бизнес-логика: мы хешируем пароль перед сохранением
        hashed_pwd = hash_password(password)
        return await self.repo.create(
            email=email,
            full_name=full_name,
            hashed_password=hashed_pwd,
            is_admin=False,  # Обычные пользователи не могут создавать админов
        )

    # Другие методы (update, delete) мы добавим, когда они понадобятся админу
