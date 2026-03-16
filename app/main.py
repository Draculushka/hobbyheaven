from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from .database import engine
from .models import Base
from .core.config import UPLOAD_DIR
from .api.endpoints import auth, hobbies

# Убедимся, что папка для загрузок существует
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Hobby Heaven")

# Подключение статики
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Подключение роутеров
app.include_router(auth.router, tags=["auth"])
app.include_router(hobbies.router, tags=["hobbies"])
