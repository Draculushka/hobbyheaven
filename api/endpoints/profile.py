from fastapi import APIRouter, Depends, Form, Request, status, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from typing import Optional

from database import get_db
from models import User, Persona, Hobby
from core.security import get_current_user
from core.templates import templates
from services.hobby_service import save_upload_image
from services import auth_service
from services.notification_service import send_mock_email

router = APIRouter()

@router.get("/cabinet")
def cabinet_page(request: Request, page: int = 1, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    # Убедимся, что активная персона загружена
    db.refresh(current_user)
    _ = current_user.active_persona

    # Получаем все персоны пользователя
    personas = db.query(Persona).filter(Persona.user_id == current_user.id).all()
    # Получаем все посты этих персон
    persona_ids = [p.id for p in personas]
    limit = 10
    page = max(1, page)
    offset = (page - 1) * limit
    total = db.query(Hobby).filter(Hobby.persona_id.in_(persona_ids)).count()
    total_pages = max(1, (total + limit - 1) // limit)
    hobbies = db.query(Hobby).filter(Hobby.persona_id.in_(persona_ids)).options(joinedload(Hobby.author_persona), joinedload(Hobby.tags)).order_by(Hobby.created_at.desc()).offset(offset).limit(limit).all()

    return templates.TemplateResponse(
        "cabinet.html",
        {"request": request, "user": current_user, "personas": personas, "hobbies": hobbies, "page": page, "total_pages": total_pages}
    )

@router.post("/cabinet/persona/create")
def create_persona(
    username: str = Form(..., max_length=30),
    bio: str = Form(None, max_length=500),
    avatar: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401)

    # Проверяем лимит персон (стандарт 2, премиум 4)
    persona_count = db.query(Persona).filter(Persona.user_id == current_user.id).count()
    limit = 4 if current_user.is_premium else 2
    if persona_count >= limit:
        msg = f"Достигнут лимит: максимум {limit} альтер-эго на аккаунт"
        if not current_user.is_premium:
            msg += ". Купите Premium для увеличения лимита до 4."
        raise HTTPException(status_code=400, detail=msg)

    # Проверяем уникальность
    existing = db.query(Persona).filter(Persona.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Имя уже занято")

    avatar_path = None
    if avatar and avatar.filename:
        avatar_path = save_upload_image(avatar)

    new_persona = Persona(
        user_id=current_user.id,
        username=username,
        bio=bio,
        avatar_path=avatar_path,
        is_default=False
    )
    db.add(new_persona)
    db.commit()

    return RedirectResponse("/cabinet", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/cabinet/persona/switch/{persona_id}")
def switch_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401)

    # Проверяем, что персона принадлежит юзеру
    persona = db.query(Persona).filter(Persona.id == persona_id, Persona.user_id == current_user.id).first()
    if not persona:
        raise HTTPException(status_code=403, detail="Неверная персона")

    current_user.active_persona_id = persona_id
    db.commit()
    db.refresh(current_user)

    return RedirectResponse("/cabinet", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/cabinet/delete")
def request_delete_account(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401)

    code = auth_service.request_verification_code(current_user.email)
    if code:
        background_tasks.add_task(send_mock_email, current_user.email, code)

    return RedirectResponse("/cabinet/delete/confirm", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/cabinet/delete/confirm")
def confirm_delete_page(request: Request, error: Optional[str] = None, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("confirm_delete.html", {"request": request, "error": error, "email": current_user.email})

@router.post("/cabinet/delete/confirm")
def confirm_delete_action(
    code: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401)

    if not auth_service.verify_deletion_code(current_user.email, code):
        return RedirectResponse("/cabinet/delete/confirm?error=Неверный или просроченный код", status_code=status.HTTP_303_SEE_OTHER)

    # Soft delete
    current_user.deleted_at = datetime.now(timezone.utc)
    current_user.is_active = False
    db.commit()

    response = RedirectResponse("/?deleted=true", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/profile/{username}")
def public_profile(username: str, request: Request, page: int = 1, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    persona = db.query(Persona).join(Persona.user).filter(
        Persona.username == username,
        User.deleted_at.is_(None)
    ).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    limit = 10
    page = max(1, page)
    offset = (page - 1) * limit
    total = db.query(Hobby).filter(Hobby.persona_id == persona.id).count()
    total_pages = max(1, (total + limit - 1) // limit)
    hobbies = db.query(Hobby).filter(Hobby.persona_id == persona.id).options(joinedload(Hobby.author_persona), joinedload(Hobby.tags)).order_by(Hobby.created_at.desc()).offset(offset).limit(limit).all()

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "persona": persona, "hobbies": hobbies, "user": current_user, "page": page, "total_pages": total_pages, "total_count": total}
    )
