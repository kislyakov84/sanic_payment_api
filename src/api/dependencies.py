from functools import wraps
from typing import Callable

from sanic import Request
from sanic.exceptions import Unauthorized, Forbidden
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_access_token
from src.models.tables import User
from src.services.users import UserService


def protected(admin_only: bool = False):
    def decorator(f: Callable):
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            # 1. Получаем сессию из контекста
            session: AsyncSession = request.ctx.session

            # 2. Проверяем токен
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise Unauthorized("Authorization header is missing or invalid")

            token = auth_header.split(" ")[1]
            token_data = decode_access_token(token)
            if not token_data or not token_data.get("sub"):
                raise Unauthorized("Invalid token")

            # 3. Находим пользователя
            email = token_data["sub"]
            user_service = UserService(session)

            user: User | None = await user_service.get_user_by_email(email=email)

            if user is None:
                raise Unauthorized("User not found")

            # 4. Проверяем права администратора, если требуется
            # --- ИСПРАВЛЕНО (еще раз!) ---
            # Используем явное сравнение, чтобы помочь Pylance
            if admin_only and user.is_admin is False:
                raise Forbidden("You do not have permission to access this resource")

            # 5. КЛАДЕМ пользователя в контекст запроса
            request.ctx.user = user

            # 6. Вызываем оригинальный обработчик роута
            response = await f(request, *args, **kwargs)
            return response

        return decorated_function

    return decorator
