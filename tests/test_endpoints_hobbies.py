"""
P0 endpoint integration tests for hobby CRUD and IDOR protection.
"""
from models import User, Persona, Hobby
from core.security import get_password_hash, create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(db, email="test@test.com", password="secret123", username="testuser", active=True):
    user = User(email=email, hashed_password=get_password_hash(password), is_active=active)
    db.add(user)
    db.flush()
    persona = Persona(user_id=user.id, username=username, is_default=True)
    db.add(persona)
    db.commit()
    db.refresh(user)
    db.refresh(persona)
    return user, persona


def auth_headers(email="test@test.com"):
    token = create_access_token(data={"sub": email})
    return {"access_token": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# TP-H12: Authenticated, no persona_id → uses default persona, creates hobby
# ---------------------------------------------------------------------------

def test_create_hobby_default_persona(client, db):
    """Creating hobby without persona_id uses default persona."""
    user, persona = create_user(db, email="creator@test.com", username="creator")
    client.cookies.update(auth_headers("creator@test.com"))

    response = client.post(
        "/create-hobby",
        data={"title": "My Hobby", "description": "A great hobby"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    hobby = db.query(Hobby).filter(Hobby.title == "My Hobby").first()
    assert hobby is not None
    assert hobby.persona_id == persona.id


# ---------------------------------------------------------------------------
# TP-H14: IDOR: persona_id of another user → 403
# ---------------------------------------------------------------------------

def test_idor_create_hobby_other_persona(client, db):
    """Creating hobby with someone else's persona_id → 403."""
    user1, persona1 = create_user(db, email="user1@test.com", username="user1")
    user2, persona2 = create_user(db, email="user2@test.com", username="user2")

    client.cookies.update(auth_headers("user1@test.com"))

    response = client.post(
        "/create-hobby",
        data={"title": "Stolen", "description": "IDOR attempt", "persona_id": str(persona2.id)},
        follow_redirects=False,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TP-H20: IDOR: edit someone else's hobby → 403
# ---------------------------------------------------------------------------

def test_idor_edit_others_hobby(client, db):
    """User1 tries to access edit page for User2's hobby → 403."""
    user1, persona1 = create_user(db, email="user1@test.com", username="user1")
    user2, persona2 = create_user(db, email="user2@test.com", username="user2")

    hobby = Hobby(title="User2 Hobby", description="Desc", persona_id=persona2.id)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)

    client.cookies.update(auth_headers("user1@test.com"))
    response = client.get(f"/edit/{hobby.id}", follow_redirects=False)
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TP-H23: Update own hobby → success 303
# ---------------------------------------------------------------------------

def test_update_own_hobby(client, db):
    """Owner can update their own hobby."""
    user, persona = create_user(db, email="owner@test.com", username="owner")

    hobby = Hobby(title="Original", description="Desc", persona_id=persona.id)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)

    client.cookies.update(auth_headers("owner@test.com"))
    response = client.post(
        f"/update/{hobby.id}",
        data={"title": "Updated", "description": "New desc", "tags_input": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    db.refresh(hobby)
    assert hobby.title == "Updated"


# ---------------------------------------------------------------------------
# TP-H24: IDOR: update someone else's hobby → 403
# ---------------------------------------------------------------------------

def test_idor_update_others_hobby(client, db):
    """User1 tries to update User2's hobby → 403."""
    user1, persona1 = create_user(db, email="user1@test.com", username="user1")
    user2, persona2 = create_user(db, email="user2@test.com", username="user2")

    hobby = Hobby(title="User2 Hobby", description="Desc", persona_id=persona2.id)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)

    client.cookies.update(auth_headers("user1@test.com"))
    response = client.post(
        f"/update/{hobby.id}",
        data={"title": "Hacked", "description": "IDOR", "tags_input": ""},
        follow_redirects=False,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TP-H26: Delete own hobby → 303, hobby removed
# ---------------------------------------------------------------------------

def test_delete_own_hobby(client, db):
    """Owner can delete their own hobby."""
    user, persona = create_user(db, email="owner@test.com", username="owner")

    hobby = Hobby(title="ToDelete", description="Desc", persona_id=persona.id)
    db.add(hobby)
    db.commit()
    hobby_id = hobby.id

    client.cookies.update(auth_headers("owner@test.com"))
    response = client.post(f"/delete-hobby/{hobby_id}", follow_redirects=False)
    assert response.status_code == 303

    deleted = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    assert deleted is None


# ---------------------------------------------------------------------------
# TP-H27: IDOR: delete someone else's hobby (not admin) → 403
# ---------------------------------------------------------------------------

def test_idor_delete_others_hobby(client, db):
    """Non-admin user tries to delete another user's hobby → 403."""
    user1, persona1 = create_user(db, email="user1@test.com", username="user1")
    user2, persona2 = create_user(db, email="user2@test.com", username="user2")

    hobby = Hobby(title="User2 Hobby", description="Desc", persona_id=persona2.id)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)

    client.cookies.update(auth_headers("user1@test.com"))
    response = client.post(f"/delete-hobby/{hobby.id}", follow_redirects=False)
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TP-H28: Admin deletes someone else's hobby → 303
# ---------------------------------------------------------------------------

def test_admin_can_delete_others_hobby(client, db):
    """Admin can delete any user's hobby."""
    user1, persona1 = create_user(db, email="user1@test.com", username="user1")
    admin, admin_persona = create_user(db, email="admin@test.com", username="admin")
    admin.is_admin = True
    db.commit()

    hobby = Hobby(title="User1 Hobby", description="Desc", persona_id=persona1.id)
    db.add(hobby)
    db.commit()
    hobby_id = hobby.id

    client.cookies.update(auth_headers("admin@test.com"))
    response = client.post(f"/delete-hobby/{hobby_id}", follow_redirects=False)
    assert response.status_code == 303

    deleted = db.query(Hobby).filter(Hobby.id == hobby_id).first()
    assert deleted is None
