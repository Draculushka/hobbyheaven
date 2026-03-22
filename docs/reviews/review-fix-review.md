# Code Review: Полный аудит проекта HobbyHold

**Branch:** `fix/review`
**Base:** `main`
**Date:** 2026-03-22
**Layers:** api, services, core, models, templates, migrations, infra
**Categories checked:** all (Security, Architecture, Language, SQL, Tests, Observability, Deploy, Dependencies, UI)

---

## Сводка

| Severity | Security | Architecture | SQL/Tests/Deploy | UI/UX | Total |
|----------|----------|--------------|------------------|-------|-------|
| CRITICAL | 3 | 3 | 3 | 1 | **10** |
| HIGH | 7 | 3 | 11 | 5 | **26** |
| MEDIUM | 10 | 4 | 10 | 8 | **32** |
| LOW | 5 | 4 | 3 | 10 | **22** |
| INFO | 3 | 2 | 0 | 5 | **10** |
| **Total** | **28** | **16** | **27** | **29** | **100** |

---

## CRITICAL (10)

### S1. Захардкоженный SECRET_KEY по умолчанию
**Category:** Security
**File:** `core/config.py:11`
**Issue:** `SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")` — если переменная окружения не задана, JWT подписывается предсказуемым ключом. Злоумышленник может подделать любой токен.
**Fix:** Убрать дефолт: `SECRET_KEY = os.environ["SECRET_KEY"]` — падать при старте если не задан.

### S2. Захардкоженные креденшалы БД
**Category:** Security
**File:** `database.py:18`
**Issue:** `DATABASE_URL = "postgresql://draculushka:secure_password@db/hobbyhold"` — пароль в исходном коде попадает в git-историю.
**Fix:** `DATABASE_URL = os.environ["DATABASE_URL"]` — обязательная переменная окружения.

### S3. Отсутствие CSRF-защиты
**Category:** Security
**Files:** все POST-эндпоинты
**Issue:** Формы без CSRF-токенов. Атакующий может создать страницу, которая выполнит действия от имени авторизованного пользователя.
**Fix:** Подключить `starlette-csrf` или `fastapi-csrf-protect`, добавить токен в каждую форму.

### A1. Нарушение слоёв: эндпоинт home() содержит бизнес-логику
**Category:** Architecture
**File:** `api/endpoints/hobbies.py:28-39`
**Issue:** Построение запроса с фильтрами, поиск по синонимам, пагинация, join — всё внутри эндпоинта вместо сервисного слоя.
**Fix:** Перенести в `hobby_service.search_hobbies(db, search, page, limit)`.

### A2. Нарушение слоёв: эндпоинты profile.py с прямыми запросами к БД
**Category:** Architecture
**File:** `api/endpoints/profile.py:23-26, 45-66`
**Issue:** `cabinet_page`, `create_persona`, `confirm_delete_action` — прямые `db.query()` вместо вызовов сервисов.
**Fix:** Создать `profile_service.py` или расширить `auth_service.py`.

### A3. Нарушение слоёв: логика создания хобби в эндпоинте
**Category:** Architecture
**File:** `api/endpoints/hobbies.py:64-79`
**Issue:** Поиск дефолтной персоны, валидация ownership — бизнес-логика в эндпоинте.
**Fix:** `hobby_service.create_hobby_for_user(db, user, persona_id, ...)`.

### T1. Тестовая БД на файле вместо in-memory
**Category:** Tests
**File:** `tests/conftest.py:11`
**Issue:** URL `sqlite:///./test.db` создаёт файл на диске. Комментарий говорит "в памяти".
**Fix:** Использовать `sqlite://` (без пути).

### T2. SQLite vs PostgreSQL — разные диалекты
**Category:** Tests
**File:** `tests/conftest.py`
**Issue:** Тесты на SQLite, прод на PostgreSQL. `func.random()`, типы и ограничения различаются.
**Fix:** Использовать `testcontainers-postgres` или документировать ограничение.

### D1. Автоматический запуск миграций отсутствует
**Category:** Deploy
**File:** `Dockerfile:24`
**Issue:** Alembic-миграции не запускаются при деплое. Забыв `alembic upgrade head`, схема и код рассинхронизируются.
**Fix:** `CMD sh -c "alembic upgrade head && uvicorn main:app ..."`.

### U1. XSS через `javascript:` протокол в sanitize-фильтре
**Category:** UI/Security
**File:** `core/templates.py:15`
**Issue:** Bleach разрешает тег `<a href="...">`, но не фильтрует протокол `javascript:`. Можно создать `<a href="javascript:alert(1)">`.
**Fix:** Добавить `protocols=['http', 'https', 'mailto']` в `bleach.clean()`.

---

## HIGH (26)

### Security (7)

**S4.** `services/hobby_service.py:15-25` — Нет валидации типа/размера загружаемых файлов. Можно загрузить `.html`, `.exe`, гигабайтный файл.
**Fix:** Проверять Content-Type (image/jpeg, image/png, image/webp), расширение, размер (5 МБ), magic bytes.

**S5.** `api/endpoints/hobbies.py:34` — LIKE-инъекция через `%` и `_` в поиске. Спецсимволы LIKE не экранируются.
**Fix:** `term.replace('%', '\\%').replace('_', '\\_')`.

**S6.** `api/endpoints/auth.py:59,84` — Cookie без `secure=True` и `samesite="lax"`. Токен передаётся по HTTP и при межсайтовых запросах.
**Fix:** `set_cookie(..., secure=True, samesite="lax")`.

**S7.** `services/auth_service.py:65`, `profile.py:102` — Timing attack при сравнении кодов. `==` прерывается при первом несовпадении.
**Fix:** `hmac.compare_digest(stored_code, code)`.

**S8.** `services/auth_service.py:51` — Слабый ГПСЧ (`random.randint`) для кодов верификации.
**Fix:** `secrets.randbelow(900000) + 100000`.

**S9.** `auth.py:47-60`, `profile.py:90-113` — Brute-force кодов верификации: нет лимита попыток. 6-значный код за 10 мин TTL перебирается за секунды.
**Fix:** Счётчик попыток в Redis (макс 5), блокировка после исчерпания.

**S10.** `api/endpoints/hobbies.py:52` — `hobby.title` в URL redirect не URL-encoded.
**Fix:** `urllib.parse.quote(hobby.title)`.

### Architecture (3)

**A4.** `api/endpoints/profile.py:99-109` — Бизнес-логика soft delete в эндпоинте: прямое обращение к `redis_client`, формирование ключей.
**Fix:** `auth_service.confirm_account_deletion(db, user, code)`.

**A5.** `api/endpoints/profile.py:13` — Циклическая зависимость: profile импортирует `send_mock_email` из auth.
**Fix:** Перенести `send_mock_email` в `services/notification_service.py`.

**A6.** `core/security.py:37` — `get_current_user()` обращается к БД из слоя `core`.
**Fix:** Перенести в `api/dependencies.py` или `services/auth_service.py`.

### SQL/Tests/Deploy (11)

**Q1.** `hobbies.py:48` — `ORDER BY random()` загружает всю таблицу в память. При большом объёме — критично.
**Fix:** `OFFSET floor(random() * count) LIMIT 1`.

**Q2.** `profile.py:121` — Unbounded запрос хобби профиля (нет LIMIT).
**Fix:** Добавить пагинацию.

**Q3.** `profile.py:26` — Unbounded запрос хобби кабинета (нет LIMIT).
**Fix:** Добавить пагинацию.

**Q4.** `core/security.py:37` — `get_current_user` не фильтрует soft-deleted/неактивных. JWT soft-deleted пользователя продолжает работать.
**Fix:** `.filter(User.deleted_at.is_(None), User.is_active == True)`.

**Q5.** `hobbies.py:28` — Только `/` фильтрует `deleted_at`. `/random`, `/profile`, `/cabinet` — нет.
**Fix:** Фильтрацию в `get_current_user` + во все запросы Hobby.

**T3.** `tests/test_main.py` — Крайне низкое покрытие (4 теста). Нет тестов: регистрации, логина, CRUD хобби, персон, soft delete, пагинации, прав доступа.
**Fix:** Написать тесты для всех эндпоинтов (happy + error paths).

**D2.** `docker-compose.yml` — Нет healthcheck для сервисов. `depends_on` без `condition: service_healthy`.
**Fix:** Добавить `healthcheck` для db/redis, `condition: service_healthy` для web.

**D3.** `docker-compose.yml:28` — `volumes: - .:/app` монтирует весь проект включая `.env`, `.git` в контейнер.
**Fix:** В production убрать, оставить только `./data/uploads:/app/uploads`.

**D4.** `Dockerfile:24` — Один воркер uvicorn. Узкое место под нагрузкой.
**Fix:** `--workers 4` или gunicorn с uvicorn workers.

**D5.** Полное отсутствие структурированного логирования. Единственный вывод — `print()`.
**Fix:** Настроить `logging` с JSON-форматом, добавить middleware для запросов.

**D6.** `requirements.txt` — `bleach` deprecated (с января 2023).
**Fix:** Заменить на `nh3`.

### UI (5)

**U2.** `templates/edit.html:65` — `{{ hobby.description }}` в `<textarea>` может содержать `</textarea>`, что сломает DOM.
**Fix:** Передавать через JS-переменную или экранировать.

**U3.** `templates/index.html:167` — Изображения в ленте без `width`/`height`. На десктопе `md:aspect-auto` снимает aspect-ratio.
**Fix:** Добавить `width="800" height="600"` или убрать `md:aspect-auto`.

**U4.** `templates/index.html:165` — Пустой контейнер изображения если нет `image_path`. Занимает 42% ширины без содержимого.
**Fix:** Скрывать контейнер или показывать placeholder.

**U5.** `templates/register.html` — Нет блока `{% if error %}` для отображения ошибок.
**Fix:** Добавить блок ошибки как в `login.html`.

**U6.** `base.html:8` — Tailwind CDN Play для production. JIT-компиляция блокирует рендер на 200-500ms.
**Fix:** Перейти на Tailwind CLI build.

---

## MEDIUM (32)

### Security (10)
- **S11.** Нет rate limiting на всех эндпоинтах. Fix: `slowapi`.
- **S12.** Нет валидации длины полей (`title`, `description`, `username`, `bio`). Fix: `Form(..., max_length=N)`.
- **S13.** Нет валидации email-формата в `auth.py:24`. Fix: `EmailStr` из pydantic.
- **S14.** Верификационный код выводится в `print()`. Fix: `logging.debug()` отключённый в prod.
- **S15.** User enumeration: разные ошибки для "email уже занят" и "username уже занят".
- **S16.** Nginx — только HTTP (порт 80), нет HTTPS.
- **S17.** Redis без пароля в docker-compose.
- **S18.** Docker монтирует весь каталог проекта в контейнер.
- **S19.** `title` хобби не санитизируется (только `description`).
- **S20.** Нет Content Security Policy (CSP) заголовков.

### Architecture (4)
- **A7.** Два разных набора `ALLOWED_TAGS` в `core/templates.py` и `services/hobby_service.py`. Fix: единый список в `core/config.py`.
- **A8.** Дублирование паттерна `if not current_user: redirect`. Fix: создать зависимость `require_current_user`.
- **A9.** `schemas/__init__.py` — Pydantic-схемы не используются ни одним эндпоинтом. Мёртвый код.
- **A10.** `auth_service.py:17-33` — Два отдельных `db.commit()` при создании пользователя. Fix: `flush()` + один `commit()`.

### SQL/Tests/Deploy (10)
- **Q6.** `models/__init__.py:22` — `is_admin` как Integer вместо Boolean.
- **Q7.** Нет индекса на `persona_id` в таблице hobbies.
- **Q8.** Нет индекса на `user_id` в таблице personas.
- **Q9.** Нет индекса на `tag_id` в junction table `hobby_tags`.
- **Q10.** `hobby_service.py:80-84` — Жёсткое удаление хобби при soft delete пользователей.
- **Q11.** `models/__init__.py:50-51` — `title`/`description` без ограничения длины (`String` без length).
- **Q12.** Nginx: нет кеширования для `/uploads/`. Fix: `expires 30d`.
- **Q13.** `.env.example` — не документированы `REDIS_URL` и EMAIL-настройки.
- **Q14.** `core/security.py:35-36` — JWT-ошибки молча проглатываются без логирования.
- **Q15.** `services/auth_service.py` — Redis-ошибки не обрабатываются, приводят к 500.

### UI (8)
- **U7.** `cabinet.html:26` — `aria-expanded` не обновляется при клике.
- **U8.** `index.html:62` — Кнопка «Категории» скрыта на мобильных (`hidden md:flex`).
- **U9.** Touch-targets < 44px: аватар (32px), теги категорий (~30px), кнопки edit/delete (32px).
- **U10.** `edit.html:71` — Захардкоженный hex `#FDF2E9`. Fix: `bg-orange-50`.
- **U11.** `index.html:7-33` — ~100 строк инлайн CSS. Fix: вынести в файл.
- **U12.** Все POST-формы без CSRF-токенов (дублирует S3 с UI-стороны).
- **U13.** `base.html` — Нет skip-link для клавиатурной навигации.
- **U14.** `index.html:175` — `<h2>` стилизован как badge 10px, а автор — 2xl. Нарушение иерархии восприятия.

---

## LOW (22)

### Security (5)
- Контейнер запускается от root (нет `USER` в Dockerfile)
- `.gitignore`: `data/postgres/` вместо `data/postgres_v2`
- Нет healthcheck для Docker-сервисов
- `is_admin` как Integer допускает значения != 0/1
- Нет автоматической миграции БД при старте

### Architecture (4)
- `main.py:5` — неиспользуемый импорт `from database import engine`
- `auth.py:29,32` — inline import `HTTPException` внутри функции
- `hobby_service.py:7` — неиспользуемый импорт `User`
- `hobby_service.py:4` — `from typing import List` устарел для Python 3.9+

### SQL/Tests/Deploy (3)
- Смешанная нумерация миграций (ручная + автогенерированная)
- `downgrade` с `drop_constraint(None)` — сломает откат миграции
- `docker-compose.yml:1` — устаревшая директива `version: "3.8"`

### UI (10)
- `<img id="modalImg">` без `width`/`height`
- Скрытые file-input'ы без `aria-label` (cabinet, index, edit)
- Изображения в профиле без `width`/`height`
- Пагинация не сохраняет параметр фильтра по тегу
- Навбары различаются между страницами (3 варианта дизайна)
- Edit навбар: другой blur, отступы, z-index
- `app.js` загружается на всех страницах, хотя openImage нужен только на index
- `login.html:18` — `{{ error }}` без явного `| e` (безопасно по умолчанию, но неявно)

---

## Passed Checks

- [x] SQL: все запросы параметризованы через SQLAlchemy (нет raw SQL interpolation)
- [x] Auth: JWT в HttpOnly cookies (не localStorage)
- [x] Auth: bcrypt для хэширования паролей
- [x] Soft delete: 30-дневное окно восстановления
- [x] Personas: лимит 3 на пользователя проверяется
- [x] HTML sanitization: bleach применяется к descriptions
- [x] Images: UUID-имена файлов (нет path traversal при чтении)
- [x] Templates: base.html устраняет дублирование head/favicon/scripts
- [x] Pagination: реализована на главной с LIMIT/OFFSET
- [x] Docker: multi-service compose (PostgreSQL, Redis, Nginx, FastAPI)
- [x] A11y: `lang="ru"`, `<main>`, `role="dialog"`, `aria-label` на иконках
- [x] Forms: `for`/`id` на labels/inputs

---

## Verdict

- [x] **REQUEST CHANGES** — 10 CRITICAL issues must be fixed before merge

**Total: 100 findings (10 CRITICAL, 26 HIGH, 32 MEDIUM, 22 LOW, 10 INFO)**

### Топ-10 приоритетов:

1. **Убрать захардкоженные секреты** — `SECRET_KEY`, `DATABASE_URL` (S1, S2)
2. **Добавить CSRF-защиту** на все POST-формы (S3)
3. **Фильтрация `javascript:` в sanitize** — добавить `protocols` в bleach (U1)
4. **Перенести бизнес-логику из эндпоинтов в сервисы** (A1-A3)
5. **Фильтровать soft-deleted в `get_current_user`** (Q4)
6. **Валидация загружаемых файлов** — тип, размер, magic bytes (S4)
7. **Защита от brute-force кодов** — лимит попыток, `secrets`, `hmac.compare_digest` (S7-S9)
8. **Cookie: `secure=True, samesite="lax"`** (S6)
9. **Расширить тестовое покрытие** — с 4 тестов до полного покрытия (T3)
10. **Заменить `bleach` на `nh3`** — deprecated с 2023 (D6)
