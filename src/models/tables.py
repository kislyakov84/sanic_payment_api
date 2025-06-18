from decimal import Decimal
import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base

Money = sa.Numeric(precision=10, scale=2)


class User(Base):
    __tablename__ = "users"

    # Используем Mapped и mapped_column для явного указания типов
    # id будет унаследован от Base
    email: Mapped[str] = mapped_column(
        sa.String, unique=True, index=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(sa.String)
    hashed_password: Mapped[str] = mapped_column(sa.String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    # Связи остаются прежними
    accounts: Mapped[list["Account"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Вот ключевое изменение для Pylance!
    # Он теперь знает, что balance у экземпляра - это Decimal.
    balance: Mapped[Decimal] = mapped_column(
        Money, nullable=False, server_default="0.00"
    )
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="accounts")
    payments: Mapped[list["Payment"]] = relationship(back_populates="account")

    def __repr__(self):
        return (
            f"<Account(id={self.id}, user_id={self.user_id}, balance={self.balance})>"
        )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(
        sa.String, unique=True, index=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    account_id: Mapped[int] = mapped_column(
        sa.ForeignKey("accounts.id"), nullable=False
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.TIMESTAMP, server_default=func.now(), nullable=False
    )

    account: Mapped["Account"] = relationship(back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, transaction_id='{self.transaction_id}', amount={self.amount})>"
