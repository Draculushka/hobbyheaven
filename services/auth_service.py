from sqlalchemy.orm import Session
from models import User, Persona
from core.security import get_password_hash, verify_password
from core.config import REDIS_URL
import redis
import secrets
import hmac

# Инициализация Redis клиента
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_persona_by_username(db: Session, username: str) -> Persona | None:
    return db.query(Persona).filter(Persona.username == username).first()

def create_user(db: Session, username: str, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    # Создаем мастер-аккаунт
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.flush()

    # Сразу создаем дефолтную персону
    default_persona = Persona(
        user_id=new_user.id,
        username=username,
        is_default=True
    )
    db.add(default_persona)
    db.commit()

    return new_user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None),
    ).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def request_verification_code(email: str) -> str:
    """Генерирует и сохраняет код в Redis. Возвращает код (или None если кулдаун)."""
    cooldown_key = f"cooldown_{email}"
    code_key = f"code_{email}"

    if redis_client.exists(cooldown_key):
        return None  # Кулдаун еще действует

    # Генерация 6-значного кода
    code = f"{secrets.randbelow(900000) + 100000}"

    # Сохраняем код на 10 минут
    redis_client.setex(code_key, 600, code)
    # Ставим кулдаун на 60 секунд
    redis_client.setex(cooldown_key, 60, "1")

    return code

def verify_code(db: Session, email: str, code: str) -> bool:
    """Проверяет код из Redis и активирует пользователя."""
    code_key = f"code_{email}"
    attempts_key = f"attempts_{email}"

    # Check attempt limit
    attempts = redis_client.get(attempts_key)
    if attempts and int(attempts) >= 5:
        redis_client.delete(code_key)
        redis_client.delete(attempts_key)
        return False

    stored_code = redis_client.get(code_key)

    if stored_code and hmac.compare_digest(stored_code, code):
        user = get_user_by_email(db, email)
        if user:
            user.is_active = True
            db.commit()
            redis_client.delete(code_key)
            redis_client.delete(attempts_key)
            return True
    else:
        # Increment attempts on wrong code
        redis_client.incr(attempts_key)
        redis_client.expire(attempts_key, 600)
    return False
