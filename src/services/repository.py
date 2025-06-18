from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class AbstractRepository(ABC):
    @abstractmethod
    async def get_one_or_none(self, **filter_by):
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, **filter_by):
        raise NotImplementedError

    @abstractmethod
    async def create(self, **data):
        raise NotImplementedError

    @abstractmethod
    async def update(self, pk: Any, **data):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, **filter_by):
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository, Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_one_or_none(self, **filter_by) -> ModelType | None:
        stmt = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, **filter_by) -> list[ModelType]:
        stmt = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def create(self, **data) -> ModelType:
        stmt = insert(self.model).values(**data).returning(self.model)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def update(self, pk: Any, **data) -> ModelType | None:
        stmt = (
            update(self.model)
            .where(self.model.id == pk)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, **filter_by) -> None:
        stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(stmt)
        await self.session.commit()
