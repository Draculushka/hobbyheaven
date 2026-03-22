import logging
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        # Пытаемся получить из заголовка Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        return None
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError as e:
        logger.warning("JWT validation error: %s", e)
        return None
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None), User.is_active.is_(True)).first()
    if user and not user.active_persona_id:
        from models import Persona
        default_persona = db.query(Persona).filter(Persona.user_id == user.id, Persona.is_default == True).first()
        if not default_persona:
            default_persona = db.query(Persona).filter(Persona.user_id == user.id).first()
        if default_persona:
            user.active_persona_id = default_persona.id
            db.commit()
            db.refresh(user)
    return user
