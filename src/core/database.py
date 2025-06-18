from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from .config import settings


# Создаем асинхронный "движок" для SQLAlchemy на основе URL из наших настроек
async_engine = create_async_engine(
    settings.database_url_asyncpg,
    echo=True,  # Включаем логирование SQL-запросов. Полезно для отладки.
)

# Создаем фабрику асинхронных сессий
async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Важно для асинхронного кода
)


# Базовый класс для всех наших моделей SQLAlchemy
class Base(DeclarativeBase):  # <--- НОВЫЙ, ТИПИЗИРОВАННЫЙ СПОСОБ
    # Объявляем id как обязательное поле для всех наших моделей
    id: Mapped[int] = mapped_column(primary_key=True, index=True)


# Зависимость для получения сессии БД в эндпоинтах
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
