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


def test_habits_goals_and_snapshots_endpoints(client):
    client.post(
        "/login",
        data={"email": "test@example.com", "password": "123456"},
        follow_redirects=False,
    )

    habit_response = client.post(
        "/api/habits",
        json={
            "name": "Leitura",
            "category": "Aprendizado",
            "target_value": 1,
            "unit": "hora",
            "is_active": True,
        },
    )
    assert habit_response.status_code == 201
    habit_id = habit_response.get_json()["data"]["id"]

    habit_log_response = client.post(
        "/api/habit-logs",
        json={
            "habit_id": habit_id,
            "log_date": "2026-04-21",
            "value": 1,
            "completed": True,
        },
    )
    assert habit_log_response.status_code == 201

    goal_response = client.post(
        "/api/goals",
        json={
            "title": "Estudar Flask",
            "category": "Carreira",
            "target_value": 20,
            "current_value": 4,
            "unit": "horas",
            "status": "active",
            "start_date": "2026-04-01",
            "deadline": "2026-04-30",
        },
    )
    assert goal_response.status_code == 201

    client.post(
        "/api/entries",
        json={
            "entry_date": "2026-04-21",
            "sleep_hours": 8,
            "study_hours": 3,
            "exercise_minutes": 20,
            "reading_hours": 1,
            "leisure_hours": 1,
            "mood_score": 9,
            "progress_percent": 80,
            "productivity_score": 88,
            "energy_level": 8,
            "notes": "Dia bom.",
        },
    )

    snapshots_response = client.get("/api/snapshots")
    assert snapshots_response.status_code == 200
    assert snapshots_response.get_json()["success"] is True
