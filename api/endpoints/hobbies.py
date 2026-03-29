from fastapi import APIRouter, Depends, Form, Request, status, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from database import get_db
from models import Hobby, Persona, CommentReaction
from services import hobby_service
from core.security import get_current_user
from core.templates import templates
from models import User

router = APIRouter()


@router.get("/debug-p")
def debug_p():
    return {"status": "ok", "message": "Hobbies router is active"}


@router.get("/p/{hobby_id}")
def post_detail(
    hobby_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import Comment, Reaction
    if current_user:
        db.refresh(current_user)
        current_user = db.query(User).options(
            joinedload(User.active_persona),
            joinedload(User.personas)
        ).filter(User.id == current_user.id).first()

    hobby = db.query(Hobby).options(
        joinedload(Hobby.author_persona),
        joinedload(Hobby.tags),
        joinedload(Hobby.comments).joinedload(Comment.author_persona),
        joinedload(Hobby.comments).joinedload(Comment.reactions),
        joinedload(Hobby.reactions).joinedload(Reaction.author_persona)
    ).filter(Hobby.id == hobby_id).first()

    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")

    return templates.TemplateResponse(
        "post_detail.html",
        {"request": request, "hobby": hobby, "user": current_user}
    )


@router.get("/")
def home(
    request: Request,
    cursor: Optional[int] = None,
    search: str = "",
    error: Optional[str] = None,
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
        {"request": request, "hobbies": hobbies, "next_cursor": next_cursor, "search": search, "user": current_user, "error": error}
    )


@router.get("/random")
def get_random_hobby(request: Request, db: Session = Depends(get_db)):
    from models import Hobby
    from sqlalchemy.sql.expression import func
    from sqlalchemy import or_

    # Fetch 20 random hobbies that have either an image or a video
    random_hobbies = db.query(Hobby).filter(
        or_(Hobby.image_path.isnot(None), Hobby.video_path.isnot(None))
    ).order_by(func.random()).limit(20).all()

    return templates.TemplateResponse(
        "explore.html",
        {"request": request, "hobbies": random_hobbies}
    )


@router.post("/create-hobby")
def create_hobby(
    title: str = Form(..., max_length=255),
    description: str = Form(..., max_length=3000),
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

    try:
        hobby_service.create_hobby(db, persona_id, title, description, tags_input, image, video)
    except HTTPException as e:
        return RedirectResponse(f"/?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return RedirectResponse(f"/?error=Произошла системная ошибка: {str(e)}", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/edit/{hobby_id}")
def edit_hobby_page(
    hobby_id: int,
    request: Request,
    error: Optional[str] = None,
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
        {"request": request, "hobby": hobby, "tags_str": tags_str, "user": current_user, "error": error}
    )


@router.post("/update/{hobby_id}")
def update_hobby(
    hobby_id: int,
    title: str = Form(..., max_length=255),
    description: str = Form(..., max_length=3000),
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

    try:
        hobby_service.update_hobby(db, hobby, title, description, tags_input, image)
    except HTTPException as e:
        return RedirectResponse(f"/edit/{hobby_id}?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return RedirectResponse(f"/edit/{hobby_id}?error=Ошибка обновления: {str(e)}", status_code=status.HTTP_303_SEE_OTHER)

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
