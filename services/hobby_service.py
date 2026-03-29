import os
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from models import Hobby, Tag, Comment, Reaction
from core.config import UPLOAD_DIR
from core.templates import sanitize_html

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024 # 50 MB (для примера)

from services.video_service import process_video_hls  # noqa: E402

def save_upload_video(file) -> str | None:
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Недопустимый формат видео.")

    # Сохраняем оригинал временно для обработки
    filename = f"raw_{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / filename

    try:
        content = file.file.read()
        if len(content) > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=400, detail="Видео слишком тяжелое. Максимум 50 МБ")

        with open(path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при сохранении видео: {str(e)}")

    return filename


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

from services.s3_service import upload_file_to_s3, delete_file_from_s3  # noqa: E402

def save_upload_image(file) -> str | None:
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены: JPG, PNG, GIF, WebP")

    try:
        # Read and check size
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Файл слишком большой. Максимум 5 МБ")
        if not _check_magic_bytes(content, ext):
            raise HTTPException(status_code=400, detail="Содержимое файла не соответствует формату")

        file.file.seek(0)
        filename = f"{uuid.uuid4().hex}{ext}"

        # Upload to S3 instead of local disk
        content_type = file.content_type if hasattr(file, "content_type") else None

        # upload_file_to_s3 returns the full public URL
        public_url = upload_file_to_s3(file.file, filename, content_type)
        return public_url
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при загрузке изображения: {str(e)}")


def delete_image(image_url: str):
    if not image_url:
        return

    # If it's a full URL, extract just the object name (filename)
    if image_url.startswith("http"):
        filename = image_url.split("/")[-1]
    else:
        filename = image_url

    delete_file_from_s3(filename)
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


def create_hobby(db: Session, persona_id: int, title: str, description: str, tags_input: str, image, video=None) -> Hobby:
    image_filename = save_upload_image(image)
    video_filename = save_upload_video(video)
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

    # Если загружено видео — запускаем асинхронную обработку
    if video_filename:
        # Задача Celery для транскодирования видео в HLS
        process_video_hls.delay(hobby.id, video_filename)

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


def search_hobbies(db: Session, search: str, cursor: int | None, limit: int):
    """Returns (hobbies, next_cursor)"""
    from models import Hobby, Persona, User, Comment, Reaction, CommentReaction
    from core.config import HOBBY_SYNONYMS

    limit = max(1, min(limit, 100))
    query = db.query(Hobby).join(Persona, Hobby.persona_id == Persona.id).join(Persona.user).filter(User.deleted_at.is_(None))

    if search:
        search_lower = search.lower().strip()
        search_terms = HOBBY_SYNONYMS.get(search_lower, [search_lower])
        escaped_terms = [t.replace('%', '/%').replace('_', '/_') for t in search_terms]
        filters = [Hobby.title.ilike(f"%{term}%", escape='/') for term in escaped_terms]
        query = query.filter(or_(*filters))

    if cursor:
        query = query.filter(Hobby.id < cursor)

    hobbies = (query
        .options(
            joinedload(Hobby.author_persona),
            joinedload(Hobby.tags),
            joinedload(Hobby.comments).joinedload(Comment.author_persona),
            joinedload(Hobby.comments).joinedload(Comment.reactions),
            joinedload(Hobby.reactions).joinedload(Reaction.author_persona)
        )
        .order_by(Hobby.id.desc())
        .limit(limit).all())

    next_cursor = hobbies[-1].id if hobbies and len(hobbies) == limit else None
    return hobbies, next_cursor


def get_random_hobby_title(db: Session) -> str | None:
    """Returns a random hobby title for redirect, or None"""
    from models import Hobby
    import urllib.parse
    hobby = db.query(Hobby.title).order_by(func.random()).limit(1).first()
    if not hobby:
        return None
    return urllib.parse.quote(hobby.title)
