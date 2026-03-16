def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "HobbyHeaven" in response.text

def test_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert "Регистрация" in response.text

def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Войти" in response.text

def test_create_hobby_unauthorized_redirects(client):
    # Попытка создать хобби без куки доступа должна редиректить на логин
    response = client.post("/create-hobby", data={"title": "Test", "description": "Test"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
