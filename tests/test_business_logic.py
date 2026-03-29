from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models import User, Persona, Hobby
from core.security import get_password_hash
from services.hobby_service import search_hobbies

def test_persona_limit_regular_user(db: Session, client: TestClient):
    # Создаем обычного пользователя
    user = User(email="limit@test.com", hashed_password=get_password_hash("pw"), is_active=True, is_premium=False)
    db.add(user)
    db.commit()

    # Добавляем 2 маски (максимум для обычного)
    db.add(Persona(user_id=user.id, username="mask1"))
    db.add(Persona(user_id=user.id, username="mask2"))
    db.commit()

    # Пытаемся добавить третью через API (надо замокать current_user или войти)
    # Для простоты используем client и обходим авторизацию через dependency override
    from core.security import get_current_user
    from main import app
    
    app.dependency_overrides[get_current_user] = lambda: user

    client.post("/cabinet/persona/create", data={"username": "mask3", "bio": ""})
    
    # Ожидаем, что нас перенаправит обратно с ошибкой (или вернет 400, если бы это было JSON API)
    # В нашем случае эндпоинт возвращает RedirectResponse, но внутри проверяет лимит
    # Если мы посмотрим в профиль контроллер, там лимит 4/2
    # Давайте проверим, что 3-я маска НЕ создалась
    
    db.refresh(user)
    assert len(user.personas) == 2
    
    app.dependency_overrides.clear()

def test_persona_limit_premium_user(db: Session, client: TestClient):
    user = User(email="limit_prem@test.com", hashed_password="pw", is_active=True, is_premium=True)
    db.add(user)
    db.commit()

    db.add(Persona(user_id=user.id, username="p_mask1"))
    db.add(Persona(user_id=user.id, username="p_mask2"))
    db.commit()

    from core.security import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = lambda: user

    # Третья маска
    client.post("/cabinet/persona/create", data={"username": "p_mask3", "bio": ""})
    db.refresh(user)
    assert len(user.personas) == 3

    # Четвертая маска
    client.post("/cabinet/persona/create", data={"username": "p_mask4", "bio": ""})
    db.refresh(user)
    assert len(user.personas) == 4

    # Пятая маска (не должна создаться)
    client.post("/cabinet/persona/create", data={"username": "p_mask5", "bio": ""})
    db.refresh(user)
    assert len(user.personas) == 4

    app.dependency_overrides.clear()

def test_soft_delete_user(db: Session, client: TestClient):
    user = User(email="soft_delete@test.com", hashed_password=get_password_hash("pw"), is_active=True)
    db.add(user)
    db.commit()
    
    p = Persona(user_id=user.id, username="soft_p")
    db.add(p)
    db.commit()
    
    h = Hobby(persona_id=p.id, title="Test Hobby", description="Desc")
    db.add(h)
    db.commit()

    # Soft delete
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()

    # Проверяем, что в search_hobbies этот пост не выводится
    hobbies, _ = search_hobbies(db, search="", cursor=None, limit=10)
    assert len([h for h in hobbies if h.author_persona.user_id == user.id]) == 0

def test_search_synonyms(db: Session):
    user = User(email="syn@test.com", hashed_password="pw")
    db.add(user)
    db.commit()
    
    p = Persona(user_id=user.id, username="syn_p")
    db.add(p)
    db.commit()
    
    # Создаем хобби с названием "шахматы"
    h1 = Hobby(persona_id=p.id, title="Играю в шахматы", description="Desc")
    db.add(h1)
    db.commit()

    # Поиск по слову "chess" должен найти "шахматы" (согласно HOBBY_SYNONYMS)
    hobbies, _ = search_hobbies(db, search="chess", cursor=None, limit=10)
    
    assert len(hobbies) == 1
    assert hobbies[0].id == h1.id
