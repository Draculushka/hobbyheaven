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

class Hobby(Base):
    __tablename__ = "hobbies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    author = Column(String)
    image_path = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Связь с тегами
    tags = relationship("Tag", secondary=hobby_tags, back_populates="hobbies")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Обратная связь
    hobbies = relationship("Hobby", secondary=hobby_tags, back_populates="tags")
