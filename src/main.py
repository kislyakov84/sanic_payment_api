from sanic import Sanic
from sanic.response import json

# Создаем экземпляр приложения Sanic
app = Sanic("PaymentApp")


# Создаем простой роут для проверки, что все работает
@app.get("/")
async def health_check(request):
    return json({"status": "ok"})


# Это нужно для запуска приложения напрямую через `python src/main.py`
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, auto_reload=True)
