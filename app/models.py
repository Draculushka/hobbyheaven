from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
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
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0) # Using Integer for boolean-like behavior if SQLite, or use Boolean
    
    # Связь с хобби
    hobbies = relationship("Hobby", back_populates="author_user")

class Hobby(Base):
    __tablename__ = "hobbies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    author = Column(String) # Сохраняем для обратной совместимости или убираем
    author_id = Column(Integer, ForeignKey("users.id"))
    image_path = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Связь с автором
    author_user = relationship("User", back_populates="hobbies")
    
    # Связь с тегами
    tags = relationship("Tag", secondary=hobby_tags, back_populates="hobbies")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Обратная связь
    hobbies = relationship("Hobby", secondary=hobby_tags, back_populates="tags")
