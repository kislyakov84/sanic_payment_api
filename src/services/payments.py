import hashlib
from decimal import Decimal
from sqlalchemy import select  # <--- ДОБАВЛЕНО
from sqlalchemy.ext.asyncio import AsyncSession

# from sqlalchemy.orm import selectinload <--- УДАЛЕНО

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
        sorted_keys = sorted(data.keys())
        message = "".join(str(data[key]) for key in sorted_keys)
        message += settings.SECRET_KEY
        expected_signature = hashlib.sha256(message.encode()).hexdigest()
        return signature == expected_signature

    async def process_webhook(self, data: dict) -> None:
        """Обрабатывает входящий платеж."""
        # 1. Проверяем, была ли уже такая транзакция
        existing_payment = await self.payment_repo.get_one_or_none(
            transaction_id=data["transaction_id"]
        )
        if existing_payment:
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
        # ВАЖНО: Как мы обсуждали, эта логика может быть спорной.
        # Оставляем ее, т.к. она соответствует ТЗ.
        if not account:
            # Создаем счет для пользователя, но без коммита.
            # Коммит будет один общий в конце.
            account = await self.account_repo.create(
                user_id=data["user_id"],
                id=data["account_id"],  # Попробуем создать с нужным ID
                balance=Decimal("0.00"),
            )

        # 4. Начисляем средства и сохраняем платеж в ОДНОЙ транзакции
        account.balance += Decimal(data["amount"])
        self.session.add(account)

        await self.payment_repo.create(
            transaction_id=data["transaction_id"],
            amount=Decimal(data["amount"]),
            account_id=account.id,
        )

        await self.session.commit()
