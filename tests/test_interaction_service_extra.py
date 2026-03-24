import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import User, Persona, Hobby, Comment
from services.interaction_service import add_comment, update_comment, delete_comment, toggle_reaction

def test_add_comment_errors(db: Session):
    # User not found
    with pytest.raises(HTTPException) as exc:
        add_comment(db, 999, 999, "text")
    assert exc.value.status_code == 404

    # User exists, no persona
    u = User(email="no_persona@test.com", hashed_password="pw", is_active=True)
    db.add(u)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        add_comment(db, 999, u.id, "text")
    assert exc.value.status_code == 400

    # Hobby not found
    p = Persona(user_id=u.id, username="np", is_default=True)
    db.add(p)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        add_comment(db, 999, u.id, "text")
    assert exc.value.status_code == 404

def test_update_comment_errors(db: Session):
    with pytest.raises(HTTPException) as exc:
        update_comment(db, 999, 999, "new")
    assert exc.value.status_code == 404

    u1 = User(email="u1@test.com", hashed_password="pw")
    u2 = User(email="u2@test.com", hashed_password="pw")
    db.add_all([u1, u2])
    db.commit()

    p1 = Persona(user_id=u1.id, username="u1", is_default=True)
    db.add(p1)
    db.commit()

    c = Comment(text="text", hobby_id=1, persona_id=p1.id)
    db.add(c)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        update_comment(db, c.id, u2.id, "new")
    assert exc.value.status_code == 403

def test_delete_comment_errors(db: Session):
    with pytest.raises(HTTPException) as exc:
        delete_comment(db, 999, 999)
    assert exc.value.status_code == 404

    u1 = User(email="d1@test.com", hashed_password="pw")
    u2 = User(email="d2@test.com", hashed_password="pw")
    db.add_all([u1, u2])
    db.commit()

    p1 = Persona(user_id=u1.id, username="d1", is_default=True)
    db.add(p1)
    db.commit()

    h = Hobby(persona_id=p1.id, title="H", description="D")
    db.add(h)
    db.commit()

    c = Comment(text="text", hobby_id=h.id, persona_id=p1.id)
    db.add(c)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        delete_comment(db, c.id, u2.id)
    assert exc.value.status_code == 403

    # Admin can delete
    u2.is_admin = True
    db.commit()
    delete_comment(db, c.id, u2.id) # Should not raise
    assert db.query(Comment).filter(Comment.id == c.id).first() is None

def test_toggle_reaction_errors(db: Session):
    with pytest.raises(HTTPException) as exc:
        toggle_reaction(db, 999, 999)
    assert exc.value.status_code == 404

    u = User(email="r1@test.com", hashed_password="pw", tokens=0)
    db.add(u)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        toggle_reaction(db, 999, u.id, "rocket")
    assert exc.value.status_code == 400

    u.tokens = 10
    db.commit()

    with pytest.raises(HTTPException) as exc:
        toggle_reaction(db, 999, u.id, "heart")
    assert exc.value.status_code == 400 # no persona

    p = Persona(user_id=u.id, username="r1", is_default=True)
    db.add(p)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        toggle_reaction(db, 999, u.id, "heart")
    assert exc.value.status_code == 404 # hobby not found
