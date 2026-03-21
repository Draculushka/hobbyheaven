from fastapi import APIRouter, Depends, Form, Request, HTTPException, status, Response, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import auth_service
from services.notification_service import send_mock_email
from core.security import create_access_token
from core.templates import templates

router = APIRouter()


@router.get("/register")
def register_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": error})


@router.post("/register")
def register_user(
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(..., min_length=6, max_length=64),
    db: Session = Depends(get_db)
):
    if auth_service.get_persona_by_username(db, username):
        return RedirectResponse(f"/register?error=Это имя уже занято", status_code=status.HTTP_303_SEE_OTHER)
    if auth_service.get_user_by_email(db, email):
        return RedirectResponse(f"/register?error=Email уже зарегистрирован", status_code=status.HTTP_303_SEE_OTHER)

    auth_service.create_user(db, username, email, password)
    code = auth_service.request_verification_code(email)

    if code:
        background_tasks.add_task(send_mock_email, email, code)

    return RedirectResponse(f"/verify-email?email={email}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/verify-email")
def verify_email_page(request: Request, email: str, error: Optional[str] = None):
    return templates.TemplateResponse("verify.html", {"request": request, "email": email, "error": error})


@router.post("/verify-email")
def verify_email(
    email: str = Form(...),
    code: str = Form(...),
    db: Session = Depends(get_db)
):
    success = auth_service.verify_code(db, email, code)
    if not success:
        return RedirectResponse(f"/verify-email?email={email}&error=Неверный или просроченный код", status_code=status.HTTP_303_SEE_OTHER)

    access_token = create_access_token(data={"sub": email})
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, secure=True, samesite="lax")
    return response


@router.get("/login")
def login_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = auth_service.authenticate_user(db, email, password)
    if not user:
        return RedirectResponse("/login?error=Invalid credentials", status_code=status.HTTP_303_SEE_OTHER)

    if user.deleted_at:
        return RedirectResponse("/login?error=Ваш аккаунт в процессе удаления. Обратитесь в поддержку для восстановления.", status_code=status.HTTP_303_SEE_OTHER)

    if not user.is_active:
        return RedirectResponse(f"/verify-email?email={user.email}&error=Активируйте аккаунт перед входом", status_code=status.HTTP_303_SEE_OTHER)

    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, secure=True, samesite="lax")
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
