from sanic import Blueprint, Request, json
from sanic.exceptions import InvalidUsage, ServerError

from src.services.payments import PaymentService

webhook_bp = Blueprint("webhooks", url_prefix="/webhooks")


@webhook_bp.post("/payment")
async def handle_payment_webhook(request: Request):
    payload = request.json
    if not payload:
        raise InvalidUsage("Empty payload")

    payment_service = PaymentService(request.ctx.session)

    # 1. Проверить подпись
    if not payment_service.verify_signature(
        payload.copy()
    ):  # передаем копию, т.к. функция меняет dict
        raise InvalidUsage("Invalid signature")

    try:
        # 2. Обработать вебхук
        await payment_service.process_webhook(payload)
    except Exception as e:
        # Логируем ошибку и возвращаем 500
        print(f"Error processing webhook: {e}")
        raise ServerError("Failed to process payment")

    return json({"status": "ok"})
