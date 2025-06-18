from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr


# --- Базовые схемы для моделей SQLAlchemy ---
# Эта конфигурация говорит Pydantic, что нужно читать данные
# не только из dict, но и из атрибутов объектов (наших моделей SQLAlchemy)
class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Схемы для сущности Account ---
class AccountPublic(OrmBase):
    id: int
    balance: Decimal


# --- Схемы для сущности User ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserPublic(OrmBase):
    id: int
    email: EmailStr
    full_name: str | None


# Эта схема будет использоваться для вывода списка пользователей с их счетами
class UserWithAccounts(UserPublic):
    accounts: list[AccountPublic] = []


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None


# --- Схемы для сущности Payment ---
class PaymentPublic(OrmBase):
    id: int
    transaction_id: str
    amount: Decimal
    account_id: int


# --- Схемы для аутентификации ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
