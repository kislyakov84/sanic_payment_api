from sqlalchemy import select  # <--- ДОБАВЛЕНО
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas import UserUpdate
from src.core.security import hash_password
from src.models.tables import User
from src.services.repository import SQLAlchemyRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = SQLAlchemyRepository(model=User, session=session)
        self.session = session  # <--- Добавим self.session для удобства

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repo.get_one_or_none(id=user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repo.get_one_or_none(email=email)

    async def create_user(
        self, email: str, password: str, full_name: str | None = None
    ) -> User:
        hashed_pwd = hash_password(password)
        new_user = await self.repo.create(
            email=email,
            full_name=full_name,
            hashed_password=hashed_pwd,
            is_admin=False,
        )
        await self.session.commit()  # <--- ДОБАВЛЕН КОММИТ
        return new_user

    async def get_all_users(self) -> list[User]:
        # query = select(User).options(selectinload(User.accounts))
        # result = await self.repo.session.execute(query) <-- было так, но repo.session устарело
        query = select(User).options(selectinload(User.accounts))
        result = await self.session.execute(query)  # <--- используем self.session
        users = result.scalars().unique().all()
        return list(users)

    async def update_user(self, user_id: int, update_data: UserUpdate) -> User | None:
        update_dict = update_data.model_dump(exclude_unset=True)
        if "password" in update_dict:
            update_dict["hashed_password"] = hash_password(update_dict.pop("password"))

        if not update_dict:
            return await self.get_user_by_id(user_id)

        updated_user = await self.repo.update(pk=user_id, **update_dict)
        await self.session.commit()  # <--- ДОБАВЛЕН КОММИТ
        return updated_user

    async def delete_user(self, user_id: int) -> None:
        await self.repo.delete(id=user_id)
        await self.session.commit()  # <--- ДОБАВЛЕН КОММИТ
