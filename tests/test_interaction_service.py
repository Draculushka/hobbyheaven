import pytest
from sqlalchemy.orm import Session
from models import User, Persona, Hobby, Comment
from services.interaction_service import add_comment, update_comment, delete_comment, toggle_reaction

def test_add_comment(db: Session):
    u = User(email="t1@test.com", hashed_password="pw", is_active=True, tokens=100)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="t1", is_default=True)
    db.add(p)
    db.flush()
    u.active_persona_id = p.id
    h = Hobby(persona_id=p.id, title="Test Hobby", description="Desc")
    db.add(h)
    db.commit()

    comment = add_comment(db, h.id, u.id, "Hello world")
    assert comment.text == "Hello world"
    assert comment.persona_id == p.id

def test_update_comment(db: Session):
    u = User(email="t2@test.com", hashed_password="pw", is_active=True, tokens=100)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="t2", is_default=True)
    db.add(p)
    db.flush()
    h = Hobby(persona_id=p.id, title="Test Hobby 2", description="Desc")
    db.add(h)
    db.commit()
    
    comment = Comment(text="old", hobby_id=h.id, persona_id=p.id)
    db.add(comment)
    db.commit()

    updated = update_comment(db, comment.id, u.id, "new")
    assert updated.text == "new"

def test_delete_comment(db: Session):
    u = User(email="t3@test.com", hashed_password="pw", is_active=True, tokens=100)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="t3", is_default=True)
    db.add(p)
    db.flush()
    h = Hobby(persona_id=p.id, title="Test Hobby 3", description="Desc")
    db.add(h)
    db.commit()

    comment = Comment(text="del", hobby_id=h.id, persona_id=p.id)
    db.add(comment)
    db.commit()

    delete_comment(db, comment.id, u.id)
    c_check = db.query(Comment).filter(Comment.id == comment.id).first()
    assert c_check is None

def test_toggle_reaction_heart(db: Session):
    u = User(email="t4@test.com", hashed_password="pw", is_active=True, tokens=100)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="t4", is_default=True)
    db.add(p)
    db.flush()
    u.active_persona_id = p.id
    h = Hobby(persona_id=p.id, title="Test Hobby 4", description="Desc")
    db.add(h)
    db.commit()

    # Add heart
    r = toggle_reaction(db, h.id, u.id, "heart")
    assert r is not None
    assert r.emoji_type == "heart"

    # Remove heart
    r2 = toggle_reaction(db, h.id, u.id, "heart")
    assert r2 is None

def test_toggle_reaction_premium(db: Session):
    u = User(email="t5@test.com", hashed_password="pw", is_active=True, is_premium=True, tokens=10)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="t5", is_default=True)
    db.add(p)
    db.flush()
    u.active_persona_id = p.id
    h = Hobby(persona_id=p.id, title="Test Hobby 5", description="Desc")
    db.add(h)
    db.commit()

    # Add rocket
    r = toggle_reaction(db, h.id, u.id, "rocket")
    assert r is not None
    assert r.emoji_type == "rocket"
    
    # Check tokens deducted
    db.refresh(u)
    assert u.tokens == 9
