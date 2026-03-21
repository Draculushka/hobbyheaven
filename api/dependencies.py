from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from core.security import get_current_user
from models import User


async def require_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_current_user_or_redirect(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    user = await get_current_user(request, db)
    if not user:
        # This will be caught by the endpoint to redirect
        raise HTTPException(status_code=401, detail="redirect_login")
    return user
