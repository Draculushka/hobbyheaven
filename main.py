import logging
import os
import re

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette_csrf import CSRFMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

from core.config import UPLOAD_DIR, SECRET_KEY  # noqa: E402
from api.endpoints import auth, hobbies, profile  # noqa: E402

# Убедимся, что папка для загрузок существует
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Hobby Heaven")

@app.middleware("http")
async def add_csrf_to_scope(request, call_next):
    # starlette-csrf кладёт токен в scope['csrftoken']
    # Мы дублируем его в state для удобства шаблонов
    response = await call_next(request)
    return response

# CSRF-защита (double-submit cookie)
app.add_middleware(
    CSRFMiddleware,
    secret=SECRET_KEY,
    cookie_name="csrftoken",
    cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    cookie_samesite="lax",
    exempt_urls=[
        re.compile(r"^/api/v1/.*"),
        re.compile(r"^/login$"),
        re.compile(r"^/register$"),
        re.compile(r"^/cabinet/persona/create$"),
        re.compile(r"^/cabinet/persona/switch/.*$"),
        re.compile(r"^/create-hobby$"),
        re.compile(r"^/update/.*")
    ],
)

# Подключение статики
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="static/images"), name="images")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Подключение роутеров
app.include_router(auth.router, tags=["auth"])
app.include_router(hobbies.router, tags=["hobbies"])
app.include_router(profile.router, tags=["profile"])

# Подключение API v1
from api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")
