from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Hobby
from schemas.hobby import PaginatedHobbyResponse, HobbyResponse
from services import hobby_service

router = APIRouter(prefix="/hobbies")

@router.get("/", response_model=PaginatedHobbyResponse)
def get_hobbies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = "",
    db: Session = Depends(get_db)
):
    hobbies, total_pages = hobby_service.search_hobbies(db, search=search, page=page, limit=limit)
    return {
        "items": hobbies,
        "total_pages": total_pages,
        "current_page": page
    }

@router.get("/{hobby_id}", response_model=HobbyResponse)
def get_hobby(hobby_id: int, db: Session = Depends(get_db)):
    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hobby not found")
    return hobby
