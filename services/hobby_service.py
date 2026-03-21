import os
import uuid
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from models import Hobby, Tag
from core.config import UPLOAD_DIR
from core.templates import sanitize_html

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

MAGIC_BYTES = {
    b'\xff\xd8\xff': '.jpg',
    b'\x89PNG': '.png',
    b'GIF87a': '.gif',
    b'GIF89a': '.gif',
    b'RIFF': '.webp',
}


def _check_magic_bytes(content: bytes, ext: str) -> bool:
    # .jpeg и .jpg — один формат
    normalized = '.jpg' if ext == '.jpeg' else ext
    for magic, expected_ext in MAGIC_BYTES.items():
        if content.startswith(magic):
            return normalized == expected_ext
    return False


def sanitize_description(description: str) -> str:
    return str(sanitize_html(description))


def save_upload_image(file) -> str | None:
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены: JPG, PNG, GIF, WebP")
    # Read and check size
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой. Максимум 5 МБ")
    if not _check_magic_bytes(content, ext):
        raise HTTPException(status_code=400, detail="Содержимое файла не соответствует формату")
    file.file.seek(0)
    filename = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / filename
    with open(path, "wb") as f:
        f.write(content)
    return filename


def delete_image(filename: str):
    if not filename:
        return
    if '..' in filename or '/' in filename:
        return
    path = UPLOAD_DIR / filename
    if path.is_file():
        path.unlink()


def process_tags(db: Session, tags_input: str, max_tags: int = 10) -> list[Tag]:
    if not tags_input:
        return []

    tag_names = list(dict.fromkeys(name.strip() for name in tags_input.split(",") if name.strip()))[:max_tags]
    existing = {t.name: t for t in db.query(Tag).filter(Tag.name.in_(tag_names)).all()}
    tags = []
    for name in tag_names:
        if name in existing:
            tags.append(existing[name])
        else:
            tag = Tag(name=name)
            db.add(tag)
            tags.append(tag)
    return tags


def create_hobby(db: Session, persona_id: int, title: str, description: str, tags_input: str, image) -> Hobby:
    image_filename = save_upload_image(image)
    clean_description = sanitize_description(description)

    hobby = Hobby(
        persona_id=persona_id,
        title=title,
        description=clean_description,
        image_path=image_filename,
    )

    hobby.tags = process_tags(db, tags_input)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)
    return hobby


def update_hobby(db: Session, hobby: Hobby, title: str, description: str, tags_input: str, image) -> Hobby:
    hobby.title = title
    hobby.description = sanitize_description(description)
    hobby.tags = process_tags(db, tags_input)

    if image and image.filename:
        if hobby.image_path:
            delete_image(hobby.image_path)
        hobby.image_path = save_upload_image(image)

    db.commit()
    db.refresh(hobby)
    return hobby


def delete_hobby(db: Session, hobby: Hobby):
    if hobby.image_path:
        delete_image(hobby.image_path)
    db.delete(hobby)
    db.commit()


def search_hobbies(db: Session, search: str, page: int, limit: int):
    """Returns (hobbies, total_pages)"""
    from models import Hobby, Persona, User
    from core.config import HOBBY_SYNONYMS

    page = max(1, page)
    limit = max(1, min(limit, 100))
    offset = (page - 1) * limit
    query = db.query(Hobby).join(Persona).join(User).filter(User.deleted_at.is_(None))

    if search:
        search_lower = search.lower().strip()
        search_terms = HOBBY_SYNONYMS.get(search_lower, [search_lower])
        escaped_terms = [t.replace('%', '\\%').replace('_', '\\_') for t in search_terms]
        filters = [Hobby.title.ilike(f"%{term}%") for term in escaped_terms]
        query = query.filter(or_(*filters))

    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    hobbies = (query
        .options(joinedload(Hobby.author_persona), joinedload(Hobby.tags))
        .order_by(Hobby.created_at.desc())
        .offset(offset).limit(limit).all())
    return hobbies, total_pages


def get_random_hobby_title(db: Session) -> str | None:
    """Returns a random hobby title for redirect, or None"""
    from models import Hobby
    import urllib.parse
    hobby = db.query(Hobby.title).order_by(func.random()).limit(1).first()
    if not hobby:
        return None
    return urllib.parse.quote(hobby.title)
