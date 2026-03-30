from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, Index
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

Index('ix_hobby_tags_tag_id', hobby_tags.c.tag_id)

class User(Base):
    """Мастер-аккаунт пользователя, используется только для авторизации и системных настроек."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    tokens = Column(Integer, default=100)
    active_persona_id = Column(Integer, ForeignKey("personas.id", name="fk_user_active_persona", use_alter=True), nullable=True)
    deleted_at = Column(DateTime, nullable=True) # Для мягкого удаления (холд 30 дней)

    # Связь с альтер-эго (персонами)
    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan", foreign_keys="Persona.user_id")
    active_persona = relationship("Persona", foreign_keys=[active_persona_id])

class Persona(Base):
    """Альтер-эго (Профиль). У одного пользователя может быть несколько персон."""
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String, unique=True, index=True, nullable=False) # Уникальное имя на всю платформу
    bio = Column(Text, nullable=True)
    avatar_path = Column(String, nullable=True)
    is_default = Column(Boolean, default=False) # Флаг основной персоны

    # Обратная связь с аккаунтом
    user = relationship("User", back_populates="personas", foreign_keys=[user_id])
    # Связь с хобби (постами)
    hobbies = relationship("Hobby", back_populates="author_persona")
    comments = relationship("Comment", back_populates="author_persona", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="author_persona", cascade="all, delete-orphan")
    comment_reactions = relationship("CommentReaction", back_populates="author_persona", cascade="all, delete-orphan")

    # Подписки
    following = relationship("Follow", foreign_keys="Follow.follower_persona_id", back_populates="follower_persona", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.followed_persona_id", back_populates="followed_persona", cascade="all, delete-orphan")

class Hobby(Base):
    """Пост о хобби, привязанный к конкретной Персоне."""
    __tablename__ = "hobbies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    image_path = Column(String)
    video_path = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Связь с автором-персоной
    author_persona = relationship("Persona", back_populates="hobbies")

    # Связь с тегами
    tags = relationship("Tag", secondary=hobby_tags, back_populates="hobbies")
    comments = relationship("Comment", back_populates="hobby", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="hobby", cascade="all, delete-orphan")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Обратная связь
    hobbies = relationship("Hobby", secondary=hobby_tags, back_populates="tags")

class Comment(Base):
    """Комментарий к посту."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    hobby_id = Column(Integer, ForeignKey("hobbies.id"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    hobby = relationship("Hobby", back_populates="comments")
    author_persona = relationship("Persona", back_populates="comments")
    reactions = relationship("CommentReaction", back_populates="comment", cascade="all, delete-orphan")

class Reaction(Base):
    """Реакция/Лайк к посту."""
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    hobby_id = Column(Integer, ForeignKey("hobbies.id"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    emoji_type = Column(String(50), default="heart", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    hobby = relationship("Hobby", back_populates="reactions")
    author_persona = relationship("Persona", back_populates="reactions")

class CommentReaction(Base):
    """Лайк к комментарию."""
    __tablename__ = "comment_reactions"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    comment = relationship("Comment", back_populates="reactions")
    author_persona = relationship("Persona", back_populates="comment_reactions")

class Follow(Base):
    """Связь подписки между Персонами."""
    __tablename__ = "follows"

    follower_persona_id = Column(Integer, ForeignKey("personas.id"), primary_key=True)
    followed_persona_id = Column(Integer, ForeignKey("personas.id"), primary_key=True)
    follower_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    followed_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    follower_persona = relationship("Persona", foreign_keys=[follower_persona_id], back_populates="following")
    followed_persona = relationship("Persona", foreign_keys=[followed_persona_id], back_populates="followers")
