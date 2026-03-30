import pytest
from sqlalchemy.orm import Session
from models import User, Persona, Follow
from services.interaction_service import follow_persona, unfollow_persona, get_persona_followers_count, is_following
from fastapi import HTTPException

def test_follow_persona_success(db: Session):
    # User A with Persona 1
    u1 = User(email="u1@test.com", hashed_password="pw", is_active=True)
    db.add(u1)
    db.flush()
    p1 = Persona(user_id=u1.id, username="persona1", is_default=True)
    db.add(p1)
    db.flush()
    u1.active_persona_id = p1.id
    
    # User B with Persona 2
    u2 = User(email="u2@test.com", hashed_password="pw", is_active=True)
    db.add(u2)
    db.flush()
    p2 = Persona(user_id=u2.id, username="persona2", is_default=True)
    db.add(p2)
    db.commit()

    # Persona 1 follows Persona 2
    follow = follow_persona(db, u1.id, p2.id)
    assert follow.follower_persona_id == p1.id
    assert follow.followed_persona_id == p2.id
    assert follow.follower_user_id == u1.id
    assert follow.followed_user_id == u2.id

    assert get_persona_followers_count(db, p2.id) == 1
    assert is_following(db, u1.id, p2.id) is True

def test_follow_self_fails(db: Session):
    u = User(email="self@test.com", hashed_password="pw", is_active=True)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="selfp", is_default=True)
    db.add(p)
    db.flush()
    u.active_persona_id = p.id
    db.commit()

    with pytest.raises(HTTPException) as excinfo:
        follow_persona(db, u.id, p.id)
    assert excinfo.value.status_code == 400
    assert "не можете подписаться на самого себя" in excinfo.value.detail

def test_follow_different_persona_same_user_fails(db: Session):
    u = User(email="same@test.com", hashed_password="pw", is_active=True)
    db.add(u)
    db.flush()
    p1 = Persona(user_id=u.id, username="p1", is_default=True)
    p2 = Persona(user_id=u.id, username="p2")
    db.add(p1)
    db.add(p2)
    db.flush()
    u.active_persona_id = p1.id
    db.commit()

    with pytest.raises(HTTPException) as excinfo:
        follow_persona(db, u.id, p2.id)
    assert excinfo.value.status_code == 400
    assert "не можете подписаться на самого себя" in excinfo.value.detail

def test_unique_follower_count(db: Session):
    # User A with 2 personas
    u_a = User(email="a@test.com", hashed_password="pw", is_active=True)
    db.add(u_a)
    db.flush()
    p_a1 = Persona(user_id=u_a.id, username="a1", is_default=True)
    p_a2 = Persona(user_id=u_a.id, username="a2")
    db.add(p_a1)
    db.add(p_a2)
    
    # User B with 1 persona
    u_b = User(email="b@test.com", hashed_password="pw", is_active=True)
    db.add(u_b)
    db.flush()
    p_b = Persona(user_id=u_b.id, username="b1", is_default=True)
    db.add(p_b)
    db.commit()

    # User A Persona 1 follows B
    u_a.active_persona_id = p_a1.id
    db.commit()
    follow_persona(db, u_a.id, p_b.id)
    
    # User A Persona 2 follows B
    u_a.active_persona_id = p_a2.id
    db.commit()
    follow_persona(db, u_a.id, p_b.id)

    # Count should be 1 because it's the same User A
    assert get_persona_followers_count(db, p_b.id) == 1

def test_unfollow_persona(db: Session):
    u1 = User(email="u1_un@test.com", hashed_password="pw", is_active=True)
    db.add(u1)
    db.flush()
    p1 = Persona(user_id=u1.id, username="p1_un", is_default=True)
    db.add(p1)
    db.flush()
    u1.active_persona_id = p1.id
    
    u2 = User(email="u2_un@test.com", hashed_password="pw", is_active=True)
    db.add(u2)
    db.flush()
    p2 = Persona(user_id=u2.id, username="p2_un", is_default=True)
    db.add(p2)
    db.commit()

    follow_persona(db, u1.id, p2.id)
    assert get_persona_followers_count(db, p2.id) == 1
    
    unfollow_persona(db, u1.id, p2.id)
    assert get_persona_followers_count(db, p2.id) == 0
    assert is_following(db, u1.id, p2.id) is False
