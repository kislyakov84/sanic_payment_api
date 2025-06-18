import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base

# Важно: Numeric используется для денег, чтобы избежать проблем с плавающей точкой
# у типа Float. precision - общее кол-во цифр, scale - кол-во цифр после запятой.
Money = sa.Numeric(precision=10, scale=2)


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    email = sa.Column(sa.String, unique=True, index=True, nullable=False)
    full_name = sa.Column(sa.String, nullable=True)
    hashed_password = sa.Column(sa.String, nullable=False)
    is_admin = sa.Column(sa.Boolean, default=False, nullable=False)

    # Связь с таблицей счетов
    accounts = relationship("Account", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Account(Base):
    __tablename__ = "accounts"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    balance = sa.Column(Money, nullable=False, server_default="0.00")
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)

    # Связь с пользователем и платежами
    user = relationship("User", back_populates="accounts")
    payments = relationship("Payment", back_populates="account")

    def __repr__(self):
        return (
            f"<Account(id={self.id}, user_id={self.user_id}, balance={self.balance})>"
        )


class Payment(Base):
    __tablename__ = "payments"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    # UUID из внешней системы, должен быть уникальным
    transaction_id = sa.Column(sa.String, unique=True, index=True, nullable=False)
    amount = sa.Column(Money, nullable=False)
    account_id = sa.Column(sa.Integer, sa.ForeignKey("accounts.id"), nullable=False)
    created_at = sa.Column(sa.TIMESTAMP, server_default=func.now(), nullable=False)

    # Связь со счетом
    account = relationship("Account", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, transaction_id='{self.transaction_id}', amount={self.amount})>"
