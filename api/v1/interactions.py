from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User
from schemas.interaction import (
    CommentCreate, CommentResponse, ReactionCreate, ReactionResponse, 
    CommentUpdate, CommentReactionResponse, FollowResponse, PersonaStatsResponse
)
from core.security import get_current_user
from services import interaction_service

router = APIRouter()

# --- Persona Interactions ---

@router.post("/personas/{persona_id}/follow", response_model=FollowResponse)
def follow_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return interaction_service.follow_persona(db, current_user.id, persona_id)

@router.delete("/personas/{persona_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    interaction_service.unfollow_persona(db, current_user.id, persona_id)

@router.get("/personas/{persona_id}/stats", response_model=PersonaStatsResponse)
def get_persona_stats(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    count = interaction_service.get_persona_followers_count(db, persona_id)
    following = False
    if current_user:
        following = interaction_service.is_following(db, current_user.id, persona_id)
    return {"followers_count": count, "is_following": following}

# --- Hobby Interactions ---

@router.post("/hobbies/{hobby_id}/comments", response_model=CommentResponse)
def add_comment(
    hobby_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.add_comment(db, hobby_id, current_user.id, comment.text, comment.persona_id)

@router.patch("/hobbies/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.update_comment(db, comment_id, current_user.id, comment.text)

@router.delete("/hobbies/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    interaction_service.delete_comment(db, comment_id, current_user.id)

@router.post("/hobbies/{hobby_id}/reactions", response_model=Optional[ReactionResponse])
def toggle_reaction(
    hobby_id: int,
    reaction: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.toggle_reaction(db, hobby_id, current_user.id, reaction.emoji_type)

@router.post("/hobbies/comments/{comment_id}/reactions", response_model=Optional[CommentReactionResponse])
def toggle_comment_reaction(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return interaction_service.toggle_comment_reaction(db, comment_id, current_user.id)
