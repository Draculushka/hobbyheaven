from fastapi import APIRouter, Depends, Form, Request, status, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional

from database import get_db
from models import Hobby, User, Persona
from services import hobby_service
from core.security import get_current_user
from core.config import HOBBY_SYNONYMS
from core.templates import templates

router = APIRouter()

@router.get("/")
async def home(
    request: Request, 
    page: int = 1, 
    search: str = "", 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    limit = 10
    offset = (page - 1) * limit
    
    # Исключаем посты удаленных пользователей
    query = db.query(Hobby).join(Persona).join(User).filter(User.deleted_at.is_(None))
    
    if search:
        search_lower = search.lower().strip()
        search_terms = HOBBY_SYNONYMS.get(search_lower, [search_lower])
        
        filters = [Hobby.title.ilike(f"%{term}%") for term in search_terms]
        query = query.filter(or_(*filters))
        
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    hobbies = query.order_by(Hobby.created_at.desc()).offset(offset).limit(limit).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "hobbies": hobbies, "page": page, "total_pages": total_pages, "search": search, "user": current_user}
    )

@router.get("/random")
def get_random_hobby(db: Session = Depends(get_db)):
    # Выбираем случайное хобби
    hobby = db.query(Hobby).order_by(func.random()).first()
    if not hobby:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    # Редирект на главную с поиском по этому хобби
    return RedirectResponse(f"/?search={hobby.title}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/create-hobby")
async def create_hobby(
    title: str = Form(...),
    description: str = Form(...),
    tags_input: str = Form(""),
    persona_id: Optional[int] = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    # Если persona_id не передана, используем дефолтную персону пользователя
    if not persona_id:
        persona = db.query(Persona).filter(Persona.user_id == current_user.id, Persona.is_default == True).first()
        if not persona:
            persona = db.query(Persona).filter(Persona.user_id == current_user.id).first()
        if not persona:
            raise HTTPException(status_code=400, detail="No persona found for user")
        persona_id = persona.id
    else:
        # Проверяем, что выбранная персона принадлежит текущему юзеру
        persona = db.query(Persona).filter(Persona.id == persona_id, Persona.user_id == current_user.id).first()
        if not persona:
            raise HTTPException(status_code=403, detail="Invalid persona")

    hobby_service.create_hobby(db, persona_id, title, description, tags_input, image)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit/{hobby_id}")
def edit_hobby_page(
    hobby_id: int, 
    request: Request, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")
    
    # Проверяем, принадлежит ли хобби одной из персон юзера
    if hobby.author_persona.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this hobby")

    tags_str = ", ".join([t.name for t in hobby.tags])
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "hobby": hobby, "tags_str": tags_str, "user": current_user}
    )

@router.post("/update/{hobby_id}")
def update_hobby(
    hobby_id: int,
    title: str = Form(...),
    description: str = Form(...),
    tags_input: str = Form(""),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby or hobby.author_persona.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    hobby_service.update_hobby(db, hobby, title, description, tags_input, image)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/delete-hobby/{hobby_id}")
def delete_hobby(
    hobby_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")
        
    if hobby.author_persona.user_id == current_user.id or current_user.is_admin:
        hobby_service.delete_hobby(db, hobby)
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    raise HTTPException(status_code=403, detail="Not authorized to delete this hobby")
