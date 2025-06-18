from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.tables import User
from src.services.repository import SQLAlchemyRepository
from src.api.schemas import UserUpdate


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

    async def get_all_users(self) -> list[User]:
        # Мы добавим ленивую загрузку счетов, чтобы не делать лишний JOIN
        # опция "selectinload" делает отдельный SELECT IN (...) для связанных счетов
        # Это эффективнее, чем JOIN для "один-ко-многим"
        from sqlalchemy.orm import selectinload

        query = select(User).options(selectinload(User.accounts))
        result = await self.repo.session.execute(query)
        return [row[0] for row in result.all()]

    async def update_user(self, user_id: int, update_data: UserUpdate) -> User | None:
        # Pydantic-модель .model_dump(exclude_unset=True) вернет dict только с теми полями,
        # которые были переданы в запросе. Это очень удобно для частичного обновления.
        update_dict = update_data.model_dump(exclude_unset=True)
        if "password" in update_dict:
            # Если в данных есть пароль, хешируем его
            update_dict["hashed_password"] = hash_password(update_dict.pop("password"))

        if not update_dict:
            # Если нечего обновлять, вернем пользователя как есть
            return await self.get_user_by_id(user_id)

        return await self.repo.update(pk=user_id, **update_dict)

    async def delete_user(self, user_id: int) -> None:
        await self.repo.delete(id=user_id)
