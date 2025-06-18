from datetime import timedelta

# from typing import Annotated

from sanic import Blueprint, Request, json
from sanic.exceptions import Unauthorized, NotFound

# from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import UserCreate, UserPublic, UserWithAccounts

# from src.core.database import get_async_session
from src.core.security import create_access_token, verify_password
from src.services.users import UserService

# from src.api.dependencies import get_current_user
from src.api.dependencies import protected
from src.api.schemas import AccountPublic  # Нам понадобится эта схема

from src.models.tables import User

from src.api.schemas import UserUpdate, UserWithAccounts

# Создаем Blueprint для пользователей
# url_prefix добавит '/users' ко всем роутам в этом файле
users_bp = Blueprint("users", url_prefix="/users")


# --- Эндпоинт для авторизации ---
@users_bp.post("/login")
async def login_for_access_token(request: Request):  # Убираем session
    session: AsyncSession = request.ctx.session  # Берем сессию из контекста

    email = request.json.get("email")
    password = request.json.get("password")

    if not email or not password:
        raise Unauthorized("Missing email or password")

    user_service = UserService(session)
    user = await user_service.get_user_by_email(email=email)

    if not user or not verify_password(password, user.hashed_password):
        raise Unauthorized("Incorrect email or password")

    # Создаем токен
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return json({"access_token": access_token, "token_type": "bearer"})


# --- Эндпоинты для текущего пользователя ---


@users_bp.get("/me")
@protected()  # <--- ПРИМЕНЯЕМ ДЕКОРАТОР
async def read_users_me(request: Request):
    # Берем пользователя прямо из контекста
    current_user: User = request.ctx.user

    response_data = UserPublic.model_validate(current_user)
    return json(response_data.model_dump())


@users_bp.get("/me/accounts")
@protected()  # <--- ПРИМЕНЯЕМ ДЕКОРАТОР
async def read_my_accounts(request: Request):
    current_user: User = request.ctx.user

    accounts_data = [AccountPublic.model_validate(acc) for acc in current_user.accounts]
    return json([acc.model_dump() for acc in accounts_data])


@users_bp.get("/me/payments")
@protected()  # <--- ПРИМЕНЯЕМ ДЕКОРАТОР
async def read_my_payments(request: Request):
    current_user: User = request.ctx.user

    all_payments = []
    for account in current_user.accounts:
        all_payments.extend(account.payments)

    return json([p.id for p in all_payments])


# --- Эндпоинты для Админа ---


@users_bp.get("/")
@protected(admin_only=True)
async def get_all_users(request: Request):
    user_service = UserService(request.ctx.session)
    users = await user_service.get_all_users()
    # Конвертируем пользователей и их счета в Pydantic-схемы
    response_data = [UserWithAccounts.model_validate(u) for u in users]
    return json([user.model_dump() for user in response_data])


@users_bp.post("/")
@protected(admin_only=True)
async def create_new_user(request: Request):
    user_data = UserCreate.model_validate(request.json)
    user_service = UserService(request.ctx.session)
    # Проверим, не занят ли email
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        return json({"error": "Email already registered"}, status=400)

    new_user = await user_service.create_user(**user_data.model_dump())
    return json(UserPublic.model_validate(new_user).model_dump(), status=201)


@users_bp.patch("/{user_id:int}")
@protected(admin_only=True)
async def update_existing_user(request: Request, user_id: int):
    update_data = UserUpdate.model_validate(request.json)
    user_service = UserService(request.ctx.session)
    updated_user = await user_service.update_user(user_id, update_data)
    if not updated_user:
        raise NotFound(f"User with id {user_id} not found")
    return json(UserPublic.model_validate(updated_user).model_dump())


@users_bp.delete("/{user_id:int}")
@protected(admin_only=True)
async def delete_existing_user(request: Request, user_id: int):
    user_service = UserService(request.ctx.session)
    # Сначала проверим, существует ли пользователь
    user_to_delete = await user_service.get_user_by_id(user_id)
    if not user_to_delete:
        raise NotFound(f"User with id {user_id} not found")

    await user_service.delete_user(user_id)
    return json({}, status=204)  # 204 No Content - успешное удаление
