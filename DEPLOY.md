# Руководство по развертыванию (Deployment)

Это руководство предназначено для запуска проекта HobbyHold на сервере (например, VPS с Ubuntu).

---

## 1. Подготовка сервера

Убедитесь, что на сервере установлены **Docker** и **Docker Compose**.

### Установка (для Ubuntu/Debian):
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable --now docker
```

---

## 2. Клонирование и настройка

```bash
git clone https://github.com/yourusername/hobbyhold.git
cd hobbyhold
```

### Настройка переменных окружения:
Создайте файл `.env` в корне проекта на основе вашего конфига:
```bash
Создайте файл `.env` в корне проекта (на основе `.env.example`) и укажите там свои данные:
```bash
POSTGRES_USER=hobby_user
POSTGRES_PASSWORD=ваш_надежный_пароль
POSTGRES_DB=hobbyhold
SECRET_KEY=длинная_случайная_строка
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db/hobbyhold
```

---

## 3. Запуск приложения

```bash
# Сборка и запуск в фоновом режиме
docker-compose up -d --build
```

### Проверка состояния:
```bash
docker-compose ps
docker-compose logs -f web
```

---

## 4. Обновление базы данных (Миграции)

После первого запуска (или обновления кода) необходимо применить миграции внутри контейнера:

```bash
docker-compose exec web alembic upgrade head
```

---

## 5. Обновление проекта

Когда вы вносите изменения в код:
1.  **Стяните изменения:** `git pull origin main`
2.  **Пересоберите контейнеры:** `docker-compose up -d --build`
3.  **Примените миграции:** `docker-compose exec web alembic upgrade head`

---

## 6. Безопасность и HTTPS (Опционально)

Для полноценной работы в сети рекомендуется настроить SSL-сертификат (HTTPS) с помощью **Certbot**.

1.  Установите Certbot: `sudo apt install certbot python3-certbot-nginx`
2.  Настройте конфиг Nginx (потребуется доменное имя).
3.  Получите сертификат: `sudo certbot --nginx -d example.com`
