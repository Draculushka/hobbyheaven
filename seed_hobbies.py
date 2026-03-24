import random
from database import SessionLocal
from models import User, Persona, Hobby, Tag
from datetime import datetime, timezone
from core.security import get_password_hash

# Категории и примеры хобби
categories = {
    "Спорт": [
        "Футбол", "Баскетбол", "Волейбол", "Теннис", "Настольный теннис", "Плавание", "Бег", "Велоспорт",
        "Бокс", "Дзюдо", "Каратэ", "Йога", "Пилатес", "Фитнес", "Гимнастика", "Скалолазание", "Серфинг",
        "Сноубординг", "Лыжи", "Хоккей", "Гольф", "Бадминтон", "Сквош", "Гребля", "Парусный спорт",
        "Конный спорт", "Фехтование", "Стрельба из лука", "Дартс", "Бильярд", "Боулинг"
    ],
    "Музыка": [
        "Игра на гитаре", "Пианино", "Скрипка", "Барабаны", "Флейта", "Саксофон", "Виолончель", "Арфа",
        "Пение", "Вокал", "Диджеинг", "Написание песен", "Битмейкинг", "Хор", "Опера", "Джаз", "Рок",
        "Классическая музыка", "Музыкальная теория", "Игра на укулеле", "Аккордеон", "Гармоника"
    ],
    "Настольные игры": [
        "Шахматы", "Шашки", "Нарды", "Го", "Монополия", "Мафия", "Каркассон", "Колонизаторы", "Билет на поезд",
        "Пандемия", "Взрывные котята", "Имаджинариум", "Диксит", "Покер", "Бридж", "Преферанс", "Dungeons & Dragons",
        "Warhammer", "Magic: The Gathering", "Скрабл", "Эрудит", "Манчкин"
    ],
    "Искусство": [
        "Рисование", "Живопись", "Скульптура", "Керамика", "Гончарное дело", "Фотография", "Видеосъемка",
        "Анимация", "Графический дизайн", "Каллиграфия", "Граффити", "Архитектура", "Дизайн интерьера",
        "Актерское мастерство", "Танцы", "Балет", "Кинематограф", "История искусств"
    ],
    "Рукоделие": [
        "Вязание", "Шитьё", "Вышивание", "Макламе", "Оригами", "Скрапбукинг", "Квиллинг", "Бисероплетение",
        "Мыловарение", "Изготовление свечей", "Резьба по дереву", "Ковка", "Ювелирное дело", "Декупаж", "Пэчворк"
    ],
    "Технологии": [
        "Программирование", "Разработка игр", "Робототехника", "3D-печать", "Электроника", "Астрономия",
        "Киберспорт", "Дроны", "Моделирование", "Сборка ПК", "Веб-дизайн", "Анализ данных", "Искусственный интеллект"
    ],
    "Природа": [
        "Садоводство", "Цветоводство", "Ландшафтный дизайн", "Походы", "Туризм", "Альпинизм", "Спелеология",
        "Орнитология", "Рыбалка", "Охота", "Сбор грибов", "Пчеловодство", "Содержание домашних животных"
    ],
    "Еда и Напитки": [
        "Кулинария", "Выпечка", "Кондитерское дело", "Кофе", "Бариста", "Виноделие", "Пивоварение",
        "Дегустация", "Веганство", "Сыроварение", "Огород на подоконнике"
    ],
    "Интеллектуальное": [
        "Чтение", "Писательство", "Поэзия", "Изучение языков", "История", "Философия", "Психология",
        "Генеалогия", "Нумизматика", "Филателия", "Коллекционирование", "Решение кроссвордов", "Викторины"
    ]
}

authors = ["Alexey", "Maria", "Dmitry", "Elena", "Ivan", "Olga", "Sergey", "Anna", "Petr", "Natalya"]

def seed_data():
    db = SessionLocal()
    try:
        # 1. Создаем системного пользователя для сид-данных
        seed_user = db.query(User).filter(User.email == "seed@hobbyhold.com").first()
        if not seed_user:
            seed_user = User(
                email="seed@hobbyhold.com",
                hashed_password=get_password_hash("seedpassword"),
                is_active=True,
                tokens=1000
            )
            db.add(seed_user)
            db.flush()

        # 2. Создаем персоны
        persona_objects = []
        for name in authors:
            persona = db.query(Persona).filter(Persona.username == name).first()
            if not persona:
                persona = Persona(
                    user_id=seed_user.id,
                    username=name,
                    bio=f"Я {name}, и я люблю делиться своими увлечениями!"
                )
                db.add(persona)
                db.flush()
            persona_objects.append(persona)

        # 3. Сначала создадим теги категорий
        tag_objects = {}
        for cat_name in categories.keys():
            tag = db.query(Tag).filter(Tag.name == cat_name).first()
            if not tag:
                tag = Tag(name=cat_name)
                db.add(tag)
                db.flush()
            tag_objects[cat_name] = tag

        # Добавим дополнительные теги
        extra_tags = ["Для начинающих", "Профи", "Дома", "На улице", "Активно", "Спокойно"]
        for tag_name in extra_tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            tag_objects[tag_name] = tag

        total_needed = 100 # Уменьшим до 100 для быстроты, но можно и 500
        current_count = 0

        # Собираем все базовые хобби
        all_base_hobbies = []
        for cat, items in categories.items():
            for item in items:
                all_base_hobbies.append((item, cat))

        # Наполняем
        while current_count < total_needed:
            base_hobby, cat = random.choice(all_base_hobbies)

            if current_count >= len(all_base_hobbies):
                prefix = random.choice(["Продвинутый", "Любительский", "Экстремальный", "Утренний", "Вечерний", "Профессиональный"])
                title = f"{prefix} {base_hobby}"
            else:
                title = base_hobby

            description = f"Это увлекательное занятие в категории {cat}. Помогает расслабиться и найти единомышленников. " \
                          f"Многие выбирают {title} как основной способ самовыражения."

            hobby = Hobby(
                title=title,
                description=description,
                persona_id=random.choice(persona_objects).id,
                created_at=datetime.now(timezone.utc)
            )

            # Привязываем теги
            hobby.tags.append(tag_objects[cat])
            hobby.tags.append(tag_objects[random.choice(extra_tags)])

            db.add(hobby)
            current_count += 1
            if current_count % 50 == 0:
                print(f"Добавлено {current_count} хобби...")

        db.commit()
        print(f"База успешно наполнена {current_count} хобби!")

    except Exception as e:
        print(f"Ошибка при наполнении: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
