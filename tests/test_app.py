import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def activity_data(monkeypatch):
    activities = {
        "Test Club": {
            "description": "A test activity",
            "schedule": "Mondays, 3:00 PM - 4:00 PM",
            "max_participants": 3,
            "participants": ["member@mergington.edu"],
        }
    }
    monkeypatch.setattr("src.app.activities", activities)
    yield activities


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_catalog(client, activity_data):
    # Arrange
    expected_activity = activity_data["Test Club"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"Test Club": expected_activity}


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new-member@mergington.edu"

    # Act
    response = client.post("/activities/Test Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Test Club"}
    assert activity_data["Test Club"]["participants"] == [
        "member@mergington.edu",
        email,
    ]


def test_signup_rejects_unknown_activity(client, activity_data):
    # Arrange
    email = "new-member@mergington.edu"

    # Act
    response = client.post("/activities/Unknown Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data["Test Club"]["participants"] == ["member@mergington.edu"]


def test_signup_rejects_duplicate_participant(client, activity_data):
    # Arrange
    email = "member@mergington.edu"

    # Act
    response = client.post("/activities/Test Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activity_data["Test Club"]["participants"] == [email]


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    email = "member@mergington.edu"

    # Act
    response = client.delete("/activities/Test Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Test Club"}
    assert activity_data["Test Club"]["participants"] == []


def test_unregister_rejects_unknown_activity(client, activity_data):
    # Arrange
    email = "member@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data["Test Club"]["participants"] == [email]


def test_unregister_rejects_unregistered_participant(client, activity_data):
    # Arrange
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete("/activities/Test Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity_data["Test Club"]["participants"] == ["member@mergington.edu"]