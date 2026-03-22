# Используем официальный легковесный образ Python
FROM python:3.12-slim

# Устанавливаем системные зависимости (если нужны для psycopg2 и т.д.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Сначала копируем только файл зависимостей
# Это позволит Docker кэшировать установку библиотек
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем остальной код проекта
COPY . .

# Создаём непривилегированного пользователя
RUN adduser --disabled-password --no-create-home --gecos "" appuser
USER appuser

# Команда для запуска (uvicorn)
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4"]
