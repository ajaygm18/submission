import jwt


def login(client, email: str, password: str = "password123") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_student_signup_and_login_returns_valid_jwt(client):
    signup = client.post(
        "/auth/signup",
        json={
            "name": "New Student",
            "email": "new.student@example.com",
            "password": "password123",
            "role": "student",
        },
    )
    assert signup.status_code == 200, signup.text
    signup_token = signup.json()["access_token"]
    decoded = jwt.decode(signup_token, options={"verify_signature": False})
    assert decoded["role"] == "student"
    assert decoded["token_type"] == "access"
    assert "user_id" in decoded
    assert "exp" in decoded

    login_response = client.post(
        "/auth/login",
        json={"email": "new.student@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200, login_response.text
    assert login_response.json()["access_token"]


def test_trainer_creates_session_with_required_fields(client, seeded):
    token = login(client, "trainer@example.com")
    response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "batch_id": seeded["batch"].id,
            "title": "Session Created By Test",
            "date": "2030-01-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Session Created By Test"
    assert body["trainer_id"] == seeded["trainer"].id


def test_student_marks_own_attendance(client, seeded):
    token = login(client, "student@example.com")
    response = client.post(
        "/attendance/mark",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_id": seeded["session"].id, "status": "present"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["student_id"] == seeded["student"].id
    assert body["status"] == "present"


def test_post_monitoring_attendance_returns_405(client):
    response = client.post("/monitoring/attendance")
    assert response.status_code == 405


def test_protected_endpoint_without_token_returns_401(client, seeded):
    response = client.post(
        "/sessions",
        json={
            "batch_id": seeded["batch"].id,
            "title": "No Token",
            "date": "2030-01-01",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        },
    )
    assert response.status_code == 401
