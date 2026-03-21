import shutil
import uuid
from pathlib import Path
from typing import List
import bleach
from sqlalchemy.orm import Session
from models import Hobby, Tag, User
from core.config import UPLOAD_DIR
from datetime import datetime, timezone

def sanitize_description(description: str) -> str:
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li', 'br']
    return bleach.clean(description, tags=allowed_tags, strip=True)

def save_upload_image(image) -> str | None:
    if not image or not image.filename:
        return None
    
    safe_filename = Path(image.filename).name
    image_filename = f"{uuid.uuid4()}_{safe_filename}"
    path = UPLOAD_DIR / image_filename
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    return image_filename

def delete_image(filename: str):
    if not filename:
        return
    path = UPLOAD_DIR / filename
    if path.is_file():
        path.unlink()

def process_tags(db: Session, tags_input: str) -> List[Tag]:
    if not tags_input:
        return []
    
    tag_names = [name.strip() for name in tags_input.split(",") if name.strip()]
    tags = []
    for name in tag_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
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
        created_at=datetime.now(timezone.utc)
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
