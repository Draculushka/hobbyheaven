from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

# Таблица связи для хобби и тегов
hobby_tags = Table(
    "hobby_tags",
    Base.metadata,
    Column("hobby_id", Integer, ForeignKey("hobbies.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class User(Base):
    """Мастер-аккаунт пользователя, используется только для авторизации и системных настроек."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0) 
    is_active = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True) # Для мягкого удаления (холд 30 дней)
    
    # Связь с альтер-эго (персонами)
    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan")

class Persona(Base):
    """Альтер-эго (Профиль). У одного пользователя может быть несколько персон."""
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String, unique=True, index=True, nullable=False) # Уникальное имя на всю платформу
    bio = Column(Text, nullable=True)
    avatar_path = Column(String, nullable=True)
    is_default = Column(Boolean, default=False) # Флаг основной персоны
    
    # Обратная связь с аккаунтом
    user = relationship("User", back_populates="personas")
    # Связь с хобби (постами)
    hobbies = relationship("Hobby", back_populates="author_persona")

class Hobby(Base):
    """Пост о хобби, привязанный к конкретной Персоне."""
    __tablename__ = "hobbies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False)
    image_path = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Связь с автором-персоной
    author_persona = relationship("Persona", back_populates="hobbies")
    
    # Связь с тегами
    tags = relationship("Tag", secondary=hobby_tags, back_populates="hobbies")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Обратная связь
    hobbies = relationship("Hobby", secondary=hobby_tags, back_populates="tags")
