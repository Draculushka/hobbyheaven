import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette_csrf import CSRFMiddleware

from core.config import UPLOAD_DIR, SECRET_KEY
from api.endpoints import auth, hobbies, profile

# Убедимся, что папка для загрузок существует
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Hobby Heaven")

# CSRF-защита (double-submit cookie)
app.add_middleware(
    CSRFMiddleware,
    secret=SECRET_KEY,
    cookie_name="csrftoken",
    cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    cookie_samesite="lax",
)

# Подключение статики
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="static/images"), name="images")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Подключение роутеров
app.include_router(auth.router, tags=["auth"])
app.include_router(hobbies.router, tags=["hobbies"])
app.include_router(profile.router, tags=["profile"])
