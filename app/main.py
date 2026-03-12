from fastapi import FastAPI, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Base, Post
from . import schemas
import shutil
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
Base.metadata.create_all(bind=engine)

@app.get("/")
def home(request: Request, page: int = 1, db: Session = Depends(get_db)):
    limit = 5
    offset = (page - 1) * limit
    posts = db.query(Post).offset(offset).limit(limit).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "posts": posts, "page": page}
    )

@app.get("/edit/{post_id}")
def edit_post_page(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "post": post}
    )

@app.post("/create-post")
def create_post_form(
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_name = None
    if image and image.filename:
        image_name = f"{uuid.uuid4()}_{image.filename}"
        file_path = f"app/uploads/{image_name}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    db_post = Post(title=title, description=description, image_path=image_name)
    db.add(db_post)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/update/{post_id}")
def update_post_form(
    post_id: int,
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        post.title = title
        post.description = description
        if image and image.filename:
            image_name = f"{uuid.uuid4()}_{image.filename}"
            file_path = f"app/uploads/{image_name}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            post.image_path = image_name
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/delete-post/{post_id}")
def delete_post_form(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/posts", response_model=list[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()

@app.get("/posts/{post_id}", response_model=schemas.Post)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
