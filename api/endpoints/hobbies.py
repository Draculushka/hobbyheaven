from fastapi import APIRouter, Depends, Form, Request, status, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from database import get_db
from models import Hobby, Persona
from services import hobby_service
from core.security import get_current_user
from core.templates import templates
from models import User

router = APIRouter()


@router.get("/")
def home(
    request: Request,
    cursor: Optional[int] = None,
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user:
        # Убедимся, что данные пользователя (токены и т.д.) актуальны
        db.refresh(current_user)
        current_user = db.query(User).options(
            joinedload(User.active_persona),
            joinedload(User.personas)
        ).filter(User.id == current_user.id).first()

    limit = 10

    hobbies, next_cursor = hobby_service.search_hobbies(db, search, cursor, limit)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "hobbies": hobbies, "next_cursor": next_cursor, "search": search, "user": current_user}
    )


@router.get("/random")
def get_random_hobby(db: Session = Depends(get_db)):
    title = hobby_service.get_random_hobby_title(db)
    if not title:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f"/?search={title}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/create-hobby")
def create_hobby(
    title: str = Form(..., max_length=255),
    description: str = Form(..., max_length=50000),
    tags_input: str = Form("", max_length=500),
    persona_id: Optional[int] = Form(None),
    image: UploadFile = File(None),
    video: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    # Если persona_id не передана, используем активную персону пользователя
    if not persona_id:
        persona_id = current_user.active_persona_id
        if not persona_id:
            # Фолбэк на дефолтную или любую
            persona = db.query(Persona).filter(Persona.user_id == current_user.id, Persona.is_default.is_(True)).first()
            if not persona:
                persona = db.query(Persona).filter(Persona.user_id == current_user.id).first()
            if not persona:
                raise HTTPException(status_code=400, detail="No persona found for user")
            persona_id = persona.id
            current_user.active_persona_id = persona_id
            db.commit()
    else:
        # Проверяем, что выбранная персона принадлежит текущему юзеру
        persona = db.query(Persona).filter(Persona.id == persona_id, Persona.user_id == current_user.id).first()
        if not persona:
            raise HTTPException(status_code=403, detail="Invalid persona")

    hobby_service.create_hobby(db, persona_id, title, description, tags_input, image, video)
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

    hobby = db.query(Hobby).options(joinedload(Hobby.author_persona)).filter(Hobby.id == hobby_id).first()
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
    title: str = Form(..., max_length=255),
    description: str = Form(..., max_length=50000),
    tags_input: str = Form("", max_length=500),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    hobby = db.query(Hobby).options(joinedload(Hobby.author_persona)).filter(Hobby.id == hobby_id).first()
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

    hobby = db.query(Hobby).options(joinedload(Hobby.author_persona)).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")

    if hobby.author_persona.user_id == current_user.id or current_user.is_admin:
        hobby_service.delete_hobby(db, hobby)
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

    raise HTTPException(status_code=403, detail="Not authorized to delete this hobby")
