# HobbyHeaven

Backend API для платформы публикации хобби.
Пользователи могут создавать посты, описывать свои хобби и делиться ими с другими.

---

## 🚀 О проекте

HobbyHeaven — это REST API сервис, который позволяет:

* создавать посты о хобби
* хранить данные в базе
* получать список постов
* обновлять и удалять посты

Проект создан как учебный backend-проект.

---

## 🧱 Технологии

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Uvicorn

База данных работает через **PostgreSQL**.

---

## 📂 Структура проекта

```
hobbyheaven/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── routers/
│
├── requirements.txt
└── README.md
```

Описание:

* **main.py** — точка входа приложения
* **database.py** — подключение к базе данных
* **models.py** — модели базы данных
* **routers/** — API маршруты

---

## ⚙️ Установка

Клонируйте репозиторий:

```
git clone https://github.com/yourusername/hobbyheaven.git
cd hobbyheaven
```

Создайте виртуальное окружение:

```
python -m venv venv
```

Активируйте его:

Linux / Mac

```
source venv/bin/activate
```

Windows

```
venv\Scripts\activate
```

Установите зависимости:

```
pip install -r requirements.txt
```

---

## 🗄 Настройка базы данных

Создайте базу данных в PostgreSQL:

```
CREATE DATABASE hobbyheaven;
```

Укажите строку подключения в файле:

```
database.py
```

Пример:

```
DATABASE_URL = "postgresql://user:password@localhost/hobbyheaven"
```

---

## ▶️ Запуск сервера

```
uvicorn app.main:app --reload
```

После запуска API будет доступно по адресу:

```
http://127.0.0.1:8000
```

---

## 📚 API документация

FastAPI автоматически генерирует документацию:

Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## 🧪 Пример запроса

Получить список постов:

```
GET /posts
```

Создать пост:

```
POST /posts
```

Пример JSON:

```
{
  "title": "Photography",
  "description": "My favorite hobby"
}
```

---

## 📌 Планы развития

* авторизация пользователей
* загрузка изображений
* лайки и комментарии
* пагинация постов

---

## 👤 Автор

Dr.Aculushka
