from fastapi import FastAPI, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Base, Hobby, Tag
from . import schemas
import shutil
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/")
def home(request: Request, page: int = 1, search: str = "", db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit
    
    query = db.query(Hobby)
    if search:
        query = query.filter(Hobby.title.ilike(f"%{search}%"))
        
    hobbies = query.order_by(Hobby.created_at.desc()).offset(offset).limit(limit).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "hobbies": hobbies, "page": page, "search": search}
    )

@app.get("/edit/{hobby_id}")
def edit_hobby_page(hobby_id: int, request: Request, db: Session = Depends(get_db)):
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")
    # Получаем все теги через запятую
    tags_str = ", ".join([t.name for t in hobby.tags])
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "hobby": hobby, "tags_str": tags_str}
    )

@app.post("/create-hobby")
async def create_hobby(
    author: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    tags_input: str = Form(""), # Поле для тегов через запятую
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_filename = None
    if image and image.filename:
        image_filename = f"{uuid.uuid4()}_{image.filename}"
        path = UPLOAD_DIR / image_filename
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    hobby = Hobby(
        author=author,
        title=title,
        description=description,
        image_path=image_filename,
        created_at=datetime.now(timezone.utc)
    )

    # Обработка тегов
    if tags_input:
        tag_names = [name.strip() for name in tags_input.split(",") if name.strip()]
        for name in tag_names:
            tag = db.query(Tag).filter(Tag.name == name).first()
            if not tag:
                tag = Tag(name=name)
                db.add(tag)
            hobby.tags.append(tag)

    db.add(hobby)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/update/{hobby_id}")
def update_hobby_form(
    hobby_id: int,
    author: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    tags_input: str = Form(""),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if hobby:
        hobby.author = author
        hobby.title = title
        hobby.description = description
        
        # Обновляем теги
        hobby.tags = []
        if tags_input:
            tag_names = [name.strip() for name in tags_input.split(",") if name.strip()]
            for name in tag_names:
                tag = db.query(Tag).filter(Tag.name == name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.add(tag)
                hobby.tags.append(tag)

        if image and image.filename:
            if hobby.image_path:
                old_path = UPLOAD_DIR / hobby.image_path
                if old_path.exists():
                    old_path.unlink()

            image_name = f"{uuid.uuid4()}_{image.filename}"
            file_path = UPLOAD_DIR / image_name
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            hobby.image_path = image_name
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/delete-hobby/{hobby_id}")
def delete_hobby_form(hobby_id: int, db: Session = Depends(get_db)):
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if hobby:
        if hobby.image_path:
            old_path = UPLOAD_DIR / hobby.image_path
            if old_path.exists():
                old_path.unlink()
        db.delete(hobby)
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/hobbies", response_model=List[schemas.Hobby])
def get_hobbies(db: Session = Depends(get_db)):
    return db.query(Hobby).all()

@app.get("/hobbies/{hobby_id}", response_model=schemas.Hobby)
def get_hobby(hobby_id: int, db: Session = Depends(get_db)):
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")
    return hobby
