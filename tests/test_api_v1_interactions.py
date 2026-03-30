import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, Persona, Hobby
from core.security import create_access_token

def auth_headers(email: str):
    token = create_access_token(data={"sub": email})
    return {"Authorization": f"Bearer {token}"}

def test_follow_persona_endpoint(client: TestClient, db: Session):
    # Setup users
    u1 = User(email="u1_api@test.com", hashed_password="pw", is_active=True)
    db.add(u1)
    db.flush()
    p1 = Persona(user_id=u1.id, username="p1_api", is_default=True)
    db.add(p1)
    db.flush()
    u1.active_persona_id = p1.id
    
    u2 = User(email="u2_api@test.com", hashed_password="pw", is_active=True)
    db.add(u2)
    db.flush()
    p2 = Persona(user_id=u2.id, username="p2_api", is_default=True)
    db.add(p2)
    db.commit()

    # Test Follow (POST)
    response = client.post(
        f"/api/v1/personas/{p2.id}/follow",
        headers=auth_headers(u1.email)
    )
    assert response.status_code == 200
    assert response.json()["followed_persona_id"] == p2.id

    # Test Stats (GET)
    response = client.get(f"/api/v1/personas/{p2.id}/stats", headers=auth_headers(u1.email))
    assert response.status_code == 200
    data = response.json()
    assert data["followers_count"] == 1
    assert data["is_following"] is True

    # Test Unfollow (DELETE)
    response = client.delete(
        f"/api/v1/personas/{p2.id}/follow",
        headers=auth_headers(u1.email)
    )
    assert response.status_code == 204

    # Test Stats again
    response = client.get(f"/api/v1/personas/{p2.id}/stats")
    assert response.status_code == 200
    assert response.json()["followers_count"] == 0

def test_hobby_interactions_endpoints(client: TestClient, db: Session):
    u = User(email="inter@test.com", hashed_password="pw", is_active=True)
    db.add(u)
    db.flush()
    p = Persona(user_id=u.id, username="interp", is_default=True)
    db.add(p)
    db.flush()
    u.active_persona_id = p.id
    
    h = Hobby(title="Hobby", description="Desc", persona_id=p.id)
    db.add(h)
    db.commit()

    # Test Add Comment (POST)
    response = client.post(
        f"/api/v1/hobbies/{h.id}/comments",
        json={"text": "Test comment"},
        headers=auth_headers(u.email)
    )
    assert response.status_code == 200
    comment_id = response.json()["id"]

    # Test Update Comment (PATCH) - with NEW path
    response = client.patch(
        f"/api/v1/hobbies/comments/{comment_id}",
        json={"text": "Updated text"},
        headers=auth_headers(u.email)
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Updated text"

    # Test Toggle Reaction (POST)
    response = client.post(
        f"/api/v1/hobbies/{h.id}/reactions",
        json={"emoji_type": "heart"},
        headers=auth_headers(u.email)
    )
    assert response.status_code == 200

    # Test Toggle Comment Reaction (POST) - with NEW path
    response = client.post(
        f"/api/v1/hobbies/comments/{comment_id}/reactions",
        headers=auth_headers(u.email)
    )
    assert response.status_code == 200

    # Test Delete Comment (DELETE) - with NEW path
    response = client.delete(
        f"/api/v1/hobbies/comments/{comment_id}",
        headers=auth_headers(u.email)
    )
    assert response.status_code == 204
