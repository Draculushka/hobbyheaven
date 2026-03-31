from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from models import Hobby, Comment, Reaction, Persona, User, CommentReaction, Follow, Notification
from typing import Optional

def create_notification(db: Session, user_id: int, n_type: str, message: str, link: Optional[str] = None):
    """
    Создает системное уведомление для пользователя.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя, который получит уведомление.
        n_type: Тип события ('like', 'comment', 'follow', 'reply').
        message: Текст уведомления.
        link: Опциональная ссылка для перехода из уведомления.
    """
    notification = Notification(user_id=user_id, type=n_type, message=message, link=link)
    db.add(notification)
    db.commit()

def add_comment(db: Session, hobby_id: int, user_id: int, text: str, persona_id: Optional[int] = None, parent_id: Optional[int] = None) -> Comment:
    """
    Добавляет комментарий к посту. Поддерживает вложенность (ответы).
    Триггерит уведомления для владельца поста и автора родительского комментария.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if persona_id:
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

    hobby = db.query(Hobby).options(joinedload(Hobby.author_persona)).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hobby not found")

    if parent_id:
        parent = db.query(Comment).filter(Comment.id == parent_id, Comment.hobby_id == hobby_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent comment not found")

    comment = Comment(text=text, hobby_id=hobby_id, persona_id=persona_id, parent_id=parent_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Уведомления
    if hobby.author_persona.user_id != user_id:
        create_notification(db, hobby.author_persona.user_id, "comment", f"Новый комментарий к '{hobby.title}'", f"/p/{hobby.id}#comment-{comment.id}")
    if parent_id:
        pc = db.query(Comment).options(joinedload(Comment.author_persona)).filter(Comment.id == parent_id).first()
        if pc and pc.author_persona.user_id != user_id:
            create_notification(db, pc.author_persona.user_id, "reply", "Ответ на ваш комментарий", f"/p/{hobby.id}#comment-{comment.id}")

    return comment

def update_comment(db: Session, comment_id: int, user_id: int, new_text: str) -> Comment:
    comment = db.query(Comment).options(joinedload(Comment.author_persona)).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_persona.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    comment.text = new_text
    db.commit()
    db.refresh(comment)
    return comment

def delete_comment(db: Session, comment_id: int, user_id: int):
    comment = db.query(Comment).options(joinedload(Comment.author_persona), joinedload(Comment.hobby)).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    is_author = (comment.author_persona.user_id == user_id)
    user = db.query(User).filter(User.id == user_id).first()
    is_admin = user.is_admin if user else False
    is_owner = (comment.hobby.author_persona.user_id == user_id)
    if not (is_author or is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()

def toggle_reaction(db: Session, hobby_id: int, user_id: int, emoji_type: str = "heart") -> Optional[Reaction]:
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        raise HTTPException(status_code=404)

    if emoji_type != "heart" and user.tokens < 1:
        raise HTTPException(status_code=400, detail="Need tokens")

    persona_id = user.active_persona_id
    if not persona_id:
        persona = db.query(Persona).filter(Persona.user_id == user_id, Persona.is_default).first()
        if not persona:
            persona = db.query(Persona).filter(Persona.user_id == user_id).first()
        if not persona:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No persona found for user")
        persona_id = persona.id
        user.active_persona_id = persona_id

    hobby = db.query(Hobby).options(joinedload(Hobby.author_persona)).filter(Hobby.id == hobby_id).first()
    if not hobby:
        raise HTTPException(status_code=404, detail="Hobby not found")
    if emoji_type == "heart":
        existing = db.query(Reaction).filter(Reaction.hobby_id == hobby_id, Reaction.persona_id == persona_id, Reaction.emoji_type == "heart").first()
        if existing:
            db.delete(existing)
            db.commit()
            return None
        res = Reaction(hobby_id=hobby_id, persona_id=persona_id, emoji_type="heart")
        if hobby.author_persona.user_id != user_id:
            create_notification(db, hobby.author_persona.user_id, "like", f"Ваш post '{hobby.title}' ❤️", f"/p/{hobby.id}")
    else:
        user.tokens -= 1
        res = Reaction(hobby_id=hobby_id, persona_id=persona_id, emoji_type=emoji_type)
        if hobby.author_persona.user_id != user_id:
            create_notification(db, hobby.author_persona.user_id, "premium_like", f"Ваш post получил {emoji_type}", f"/p/{hobby.id}")

    db.add(res)
    db.commit()
    return res

def toggle_comment_reaction(db: Session, comment_id: int, user_id: int) -> Optional[CommentReaction]:
    user = db.query(User).filter(User.id == user_id).first()
    persona_id = user.active_persona_id
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404)
    existing = db.query(CommentReaction).filter(CommentReaction.comment_id == comment_id, CommentReaction.persona_id == persona_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return None
    res = CommentReaction(comment_id=comment_id, persona_id=persona_id)
    db.add(res)
    db.commit()
    return res

def follow_persona(db: Session, follower_user_id: int, followed_persona_id: int) -> Follow:
    user = db.query(User).filter(User.id == follower_user_id).first()
    target = db.query(Persona).filter(Persona.id == followed_persona_id).first()
    if not target:
        raise HTTPException(status_code=404)
    if user.id == target.user_id:
        raise HTTPException(status_code=400, detail="Вы не можете подписаться на самого себя")

    follow = Follow(follower_persona_id=user.active_persona_id, followed_persona_id=followed_persona_id, follower_user_id=user.id, followed_user_id=target.user_id)
    db.add(follow)
    db.commit()
    create_notification(db, target.user_id, "follow", f"На вас подписались: {user.active_persona.username}", f"/profile/{target.username}")
    return follow

def unfollow_persona(db: Session, follower_user_id: int, followed_persona_id: int):
    user = db.query(User).filter(User.id == follower_user_id).first()
    db.query(Follow).filter(Follow.follower_persona_id == user.active_persona_id, Follow.followed_persona_id == followed_persona_id).delete()
    db.commit()

def get_persona_followers_count(db: Session, persona_id: int) -> int:
    return db.query(func.count(func.distinct(Follow.follower_user_id))).filter(Follow.followed_persona_id == persona_id).scalar() or 0

def is_following(db: Session, follower_user_id: int, followed_persona_id: int) -> bool:
    return db.query(Follow).filter(Follow.follower_user_id == follower_user_id, Follow.followed_persona_id == followed_persona_id).first() is not None
