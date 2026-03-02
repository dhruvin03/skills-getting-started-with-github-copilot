from fastapi.testclient import TestClient
import copy

from src.app import app, activities

client = TestClient(app)

# keep a pristine copy of the original activities structure so tests
# can reset between runs
_original_activities = copy.deepcopy(activities)


import pytest


@pytest.fixture(autouse=True)
def restore_activities():
    # called before each test
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))
    yield
    # no teardown required


def test_root_redirects():
    # Arrange: nothing special needed for root endpoint

    # Act
    resp = client.get("/", follow_redirects=False)

    # Assert
    assert resp.status_code == 307
    assert "/static/index.html" in resp.headers.get("location", "")


def test_get_activities():
    # Arrange: ensure default activities are loaded by fixture

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data


def test_signup_and_duplicate():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act - first signup
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert first signup success
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]
    assert email in activities[activity]["participants"]

    # Act - duplicate signup attempt
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert duplicate is rejected
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json()["detail"]


def test_remove_participant():
    # Arrange
    activity = "Programming Class"
    email = "emma@mergington.edu"

    # Act - remove existing participant
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert removal succeeded
    assert resp.status_code == 200
    assert email not in activities[activity]["participants"]

    # Act - attempt to remove again
    resp2 = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert second removal returns 404
    assert resp2.status_code == 404


def test_nonexistent_activity():
    # Arrange: activity name that doesn't exist

    # Act & Assert - signup attempt
    resp = client.post("/activities/NoSuch/signup", params={"email": "x@x.com"})
    assert resp.status_code == 404

    # Act & Assert - delete attempt
    resp2 = client.delete("/activities/NoSuch/participants", params={"email": "x@x.com"})
    assert resp2.status_code == 404
