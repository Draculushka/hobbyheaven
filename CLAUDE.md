# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HobbyHeaven — веб-приложение для публикации и обмена хобби. Python 3.12, FastAPI, PostgreSQL (SQLAlchemy ORM), Jinja2 + Tailwind CSS, Redis для кэширования и верификации.

## Commands

```bash
# Запуск dev-сервера
uvicorn main:app --reload

# Docker (PostgreSQL, Redis, Nginx, FastAPI)
docker-compose up --build

# Тесты (pytest, SQLite in-memory)
export PYTHONPATH=$PYTHONPATH:.
pytest tests/

# Миграции (Alembic)
export PYTHONPATH=$PYTHONPATH:.
alembic revision --autogenerate -m "описание"
alembic upgrade head
alembic downgrade -1
```

## Architecture

Трёхслойная архитектура:

- **api/endpoints/** — HTTP-обработчики (auth, hobbies, profile). Маршруты FastAPI, рендер Jinja2 шаблонов
- **services/** — бизнес-логика (auth_service, hobby_service). Работа с БД, Redis, загрузка изображений, санитизация HTML (bleach)
- **core/** — конфигурация (config.py) и безопасность (security.py). JWT в HttpOnly cookies, bcrypt хэширование

Поддерживающие слои:
- **models/** — SQLAlchemy модели: User → Persona (до 3 на пользователя) → Hobby ↔ Tag (many-to-many)
- **schemas/** — Pydantic-схемы для валидации запросов/ответов
- **templates/** — Jinja2 HTML-шаблоны
- **migrations/versions/** — Alembic миграции

Точка входа: `main.py` — создаёт FastAPI app, подключает роутеры и статику.

## Key Patterns

- **Soft delete** для пользователей: поле `deleted_at`, 30-дневный период восстановления
- **Multi-persona**: один User может иметь до 3 Persona, каждая со своим username и хобби
- **Synonym search**: `HOBBY_SYNONYMS` в `core/config.py` — маппинг синонимов для умного поиска
- **Email 2FA через Redis**: коды верификации с TTL 10 минут и cooldown 60 секунд
- **UUID-имена файлов** для загруженных изображений в `uploads/`

## Commit Convention

Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

## Branch Naming

`feature/`, `bugfix/`, `docs/` префиксы

## Infrastructure

Docker Compose сервисы: PostgreSQL 16 (`hobby_db`), FastAPI (`hobby_web`), Redis (`hobby_redis`), Nginx (`hobby_nginx`). Nginx лимит загрузки: 10MB.

## Testing

Тесты используют SQLite in-memory через dependency override в `tests/conftest.py`. Фикстуры — function-scoped (таблицы создаются/удаляются для каждого теста). Новые эндпоинты должны проверяться в Swagger UI (`/docs`).
