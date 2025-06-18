from sanic import Sanic
from sanic.response import json
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем нашу "фабрику" сессий
from src.core.database import async_session_maker
from src.api.users import users_bp
from src.api.webhooks import webhook_bp

app = Sanic("PaymentApp")


# --- Middleware для управления сессией БД ---
@app.middleware("request")
async def inject_session(request):
    """
    Создает сессию для каждого запроса и кладет ее в контекст.
    """
    request.ctx.session = async_session_maker()
    request.ctx.session_ctx_token = request.ctx.session.info.get("ctx_token")


@app.middleware("response")
async def close_session(request, response):
    """
    Закрывает сессию после того, как ответ был сформирован.
    """
    if hasattr(request.ctx, "session_ctx_token"):
        await request.ctx.session.close()


# --- Регистрация Blueprints ---
app.blueprint(users_bp)
app.blueprint(webhook_bp)


@app.get("/")
async def health_check(request):
    return json({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, auto_reload=True)
