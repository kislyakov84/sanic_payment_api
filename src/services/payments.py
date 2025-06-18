import hashlib
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.models.tables import Account, Payment, User
from src.services.repository import SQLAlchemyRepository


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_repo = SQLAlchemyRepository(model=Payment, session=session)
        self.account_repo = SQLAlchemyRepository(model=Account, session=session)

    def verify_signature(self, data: dict) -> bool:
        """Проверяет подпись вебхука."""
        signature = data.pop("signature")

        # Сортируем ключи и конкатенируем значения
        sorted_keys = sorted(data.keys())
        message = "".join(str(data[key]) for key in sorted_keys)

        # Добавляем секретный ключ
        message += settings.SECRET_KEY

        # Считаем хеш
        expected_signature = hashlib.sha256(message.encode()).hexdigest()

        return signature == expected_signature

    async def process_webhook(self, data: dict) -> None:
        """Обрабатывает входящий платеж."""
        # 1. Проверяем, была ли уже такая транзакция
        existing_payment = await self.payment_repo.get_one_or_none(
            transaction_id=data["transaction_id"]
        )
        if existing_payment:
            # Транзакция уже обработана, ничего не делаем
            return

        # 2. Находим пользователя и его счет
        # Используем JOIN, чтобы убедиться, что счет принадлежит пользователю
        query = (
            select(Account)
            .join(User)
            .where(User.id == data["user_id"], Account.id == data["account_id"])
        )
        result = await self.session.execute(query)
        account = result.scalar_one_or_none()

        # 3. Если счета нет - создаем его
        if not account:
            account = await self.account_repo.create(user_id=data["user_id"])

        # 4. Сохраняем транзакцию и начисляем средства
        # Начисляем средства
        account.balance += Decimal(data["amount"])
        self.session.add(
            account
        )  # Добавляем измененный объект в сессию для отслеживания

        # Сохраняем платеж
        await self.payment_repo.create(
            transaction_id=data["transaction_id"],
            amount=Decimal(data["amount"]),
            account_id=account.id,
        )
        # А вот теперь коммитим все изменения ОДНОЙ транзакцией
        await self.session.commit()
