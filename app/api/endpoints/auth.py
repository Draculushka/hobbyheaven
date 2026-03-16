from fastapi import APIRouter, Depends, Form, Request, status, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ...database import get_db
from ...services import auth_service
from ...core.security import create_access_token
from ...core.config import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_user(
    username: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    if auth_service.get_user_by_username(db, username):
        # В идеале тут нужно вернуть страницу с ошибкой, но пока сохраним логику оригинала
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Username already registered")
    
    auth_service.create_user(db, username, email, password)
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login")
def login_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.post("/login")
def login(
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = auth_service.authenticate_user(db, username, password)
    if not user:
        return RedirectResponse("/login?error=Invalid credentials", status_code=status.HTTP_303_SEE_OTHER)
    
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
