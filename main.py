import logging
import os
import re
import http.cookies
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders
from starlette_csrf import CSRFMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

from core.config import UPLOAD_DIR, SECRET_KEY  # noqa: E402
from api.endpoints import auth, hobbies, profile  # noqa: E402

# Убедимся, что папка для загрузок существует
os.makedirs(UPLOAD_DIR, exist_ok=True)

from starlette.types import Scope, Receive, Send, Message

class CustomCSRFMiddleware(CSRFMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        csrf_cookie = request.cookies.get(self.cookie_name)

        # Всегда прокидываем текущий токен в scope для использования в шаблонах
        scope["csrftoken"] = csrf_cookie

        # Если куки нет, генерируем токен заранее
        if not csrf_cookie:
            csrf_cookie = self._generate_csrf_token()
            scope["csrftoken"] = csrf_cookie
            # Мы пометим scope, что куку НУЖНО установить
            scope["csrftoken_new"] = True

        if self._url_is_required(request.url) or (
            request.method not in self.safe_methods
            and not self._url_is_exempt(request.url)
            and self._has_sensitive_cookies(request.cookies)
        ):
            # Читаем тело запроса один раз
            body = await request.body()
            
            # Подменяем receive, чтобы приложение могло прочитать тело еще раз
            async def new_receive() -> Message:
                return {"type": "http.request", "body": body}

            # Создаем временный запрос для получения токена из формы
            temp_request = Request(scope, receive=new_receive)
            submitted_csrf_token = await self._get_submitted_csrf_token(temp_request)
            
            # Внимание: для проверки используем ТОТ ЖЕ csrf_cookie, который достали выше
            if (
                not csrf_cookie
                or not submitted_csrf_token
                or not self._csrf_tokens_match(csrf_cookie, submitted_csrf_token)
            ):
                response = self._get_error_response(request)
                await response(scope, receive, send)
                return

            # Для продолжения работы приложения тоже подменяем receive
            await self.app(scope, new_receive, send)
        else:
            # Оборачиваем send, чтобы подставить нашу новую куку, если нужно
            async def custom_send(message: Message) -> None:
                if message["type"] == "http.response.start" and scope.get("csrftoken_new"):
                    headers = MutableHeaders(scope=message)
                    cookie: http.cookies.BaseCookie = http.cookies.SimpleCookie()
                    cookie[self.cookie_name] = scope["csrftoken"]
                    cookie[self.cookie_name]["path"] = self.cookie_path
                    cookie[self.cookie_name]["secure"] = self.cookie_secure
                    cookie[self.cookie_name]["httponly"] = self.cookie_httponly
                    cookie[self.cookie_name]["samesite"] = self.cookie_samesite
                    headers.append("set-cookie", cookie.output(header="").strip())
                await send(message)

            await self.app(scope, receive, custom_send)

    async def _get_submitted_csrf_token(self, request: Request) -> Optional[str]:
        # Сначала пробуем из заголовка
        token = request.headers.get(self.header_name)
        if token:
            return token
        
        # Затем из формы
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            try:
                form = await request.form()
                return form.get("csrftoken")
            except Exception:
                return None
        return None

app = FastAPI(title="Hobby Hold")

# CSRF-защита (double-submit cookie)
app.add_middleware(
    CustomCSRFMiddleware,
    secret=SECRET_KEY,
    cookie_name="csrftoken",
    cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    cookie_samesite="lax",
    exempt_urls=[
        re.compile(r"^/api/v1/.*"),
        re.compile(r"^/login$"),
        re.compile(r"^/register$"),
        re.compile(r"^/verify-email$"),
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
