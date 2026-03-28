from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User
from schemas.interaction import CommentCreate, CommentResponse, ReactionCreate, ReactionResponse, CommentUpdate, CommentReactionResponse
from core.security import get_current_user
from services import interaction_service

router = APIRouter()

@router.post("/{hobby_id}/comments", response_model=CommentResponse)
def add_comment(
    hobby_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.add_comment(db, hobby_id, current_user.id, comment.text, comment.persona_id)

@router.patch("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.update_comment(db, comment_id, current_user.id, comment.text)

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    interaction_service.delete_comment(db, comment_id, current_user.id)

@router.post("/{hobby_id}/reactions", response_model=Optional[ReactionResponse])
def toggle_reaction(
    hobby_id: int,
    reaction: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.toggle_reaction(db, hobby_id, current_user.id, reaction.emoji_type)

@router.post("/comments/{comment_id}/reactions", response_model=Optional[CommentReactionResponse])
def toggle_comment_reaction(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.toggle_comment_reaction(db, comment_id, current_user.id)
