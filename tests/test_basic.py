def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_dashboard_protected(client):
    response = client.get("/dashboard")
    assert response.status_code == 302


def test_login_and_create_entry_api(client):
    login_response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "123456"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302

    create_response = client.post(
        "/api/entries",
        json={
            "entry_date": "2026-04-21",
            "sleep_hours": 7.5,
            "study_hours": 2,
            "exercise_minutes": 30,
            "reading_hours": 1,
            "leisure_hours": 1,
            "mood_score": 8,
            "progress_percent": 70,
            "energy_level": 8,
            "notes": "Dia consistente.",
        },
    )
    assert create_response.status_code == 201
    assert create_response.get_json()["success"] is True


def test_api_requires_authentication(client):
    response = client.get("/api/entries")
    assert response.status_code == 401
