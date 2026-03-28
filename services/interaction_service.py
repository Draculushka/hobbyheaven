from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models import Hobby, Comment, Reaction, Persona, User, CommentReaction
from typing import Optional

def add_comment(db: Session, hobby_id: int, user_id: int, text: str, persona_id: Optional[int] = None) -> Comment:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if persona_id:
        # Проверяем, что выбранная персона принадлежит пользователю
        persona = db.query(Persona).filter(Persona.id == persona_id, Persona.user_id == user_id).first()
        if not persona:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid persona")
    else:
        persona_id = user.active_persona_id
        if not persona_id:
            persona = db.query(Persona).filter(Persona.user_id == user_id, Persona.is_default).first()
            if not persona:
                persona = db.query(Persona).filter(Persona.user_id == user_id).first()
            if not persona:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No persona found for user")
            persona_id = persona.id
            user.active_persona_id = persona_id
            db.commit()

    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hobby not found")

    comment = Comment(text=text, hobby_id=hobby_id, persona_id=persona_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def update_comment(db: Session, comment_id: int, user_id: int, new_text: str) -> Comment:
    comment = db.query(Comment).options(joinedload(Comment.author_persona)).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Только автор может редактировать
    if comment.author_persona.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this comment")

    comment.text = new_text
    db.commit()
    db.refresh(comment)
    return comment

def delete_comment(db: Session, comment_id: int, user_id: int):
    comment = db.query(Comment).options(joinedload(Comment.author_persona), joinedload(Comment.hobby)).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    # Проверяем, принадлежит ли комментарий пользователю (через любую его персону)
    # Или если это админ, или владелец поста
    is_author = (comment.author_persona.user_id == user_id)

    if not is_author:
        user = db.query(User).filter(User.id == user_id).first()
        is_admin = user.is_admin if user else False
        is_post_owner = (comment.hobby.author_persona.user_id == user_id)

        if not (is_admin or is_post_owner):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()

def toggle_reaction(db: Session, hobby_id: int, user_id: int, emoji_type: str = "heart") -> Optional[Reaction]:
    # Используем with_for_update(), чтобы заблокировать строку пользователя на время транзакции
    # Это защищает от "состояния гонки" (race condition) при одновременных кликах
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    is_premium_emoji = (emoji_type != "heart")
    if is_premium_emoji:
        if user.tokens < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно токенов для кастомной реакции")

    persona_id = user.active_persona_id
    if not persona_id:
        # Фолбэк на дефолтную или любую
        persona = db.query(Persona).filter(Persona.user_id == user_id, Persona.is_default).first()
        if not persona:
            persona = db.query(Persona).filter(Persona.user_id == user_id).first()
        if not persona:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No persona found for user")
        persona_id = persona.id
        user.active_persona_id = persona_id

    hobby = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hobby not found")

    if emoji_type == "heart":
        # ТОЛЬКО для сердечка логика переключения
        existing = db.query(Reaction).filter(
            Reaction.hobby_id == hobby_id,
            Reaction.persona_id == persona_id,
            Reaction.emoji_type == "heart"
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            return None
        else:
            new_reaction = Reaction(hobby_id=hobby_id, persona_id=persona_id, emoji_type="heart")
            db.add(new_reaction)
            db.commit()
            db.refresh(new_reaction)
            return new_reaction
    else:
        # Для ПРЕМИУМ-реакций: ВСЕГДА новая запись, старые не ищем
        # Списываем токен только ПЕРЕД сохранением
        user.tokens -= 1
        db.add(user)
        new_reaction = Reaction(hobby_id=hobby_id, persona_id=persona_id, emoji_type=emoji_type)
        db.add(new_reaction)
        db.commit()
        db.refresh(user)
        db.refresh(new_reaction)
        return new_reaction

def toggle_comment_reaction(db: Session, comment_id: int, user_id: int) -> Optional[CommentReaction]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    persona_id = user.active_persona_id
    if not persona_id:
        persona = db.query(Persona).filter(Persona.user_id == user_id, Persona.is_default).first()
        if not persona:
            persona = db.query(Persona).filter(Persona.user_id == user_id).first()
        if not persona:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No persona found for user")
        persona_id = persona.id
        user.active_persona_id = persona_id
        db.commit()

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    existing = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.persona_id == persona_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return None
    else:
        new_reaction = CommentReaction(comment_id=comment_id, persona_id=persona_id)
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
        return new_reaction
