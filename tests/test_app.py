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
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert "/static/index.html" in resp.headers.get("location", "")


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data


def test_signup_and_duplicate():
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]

    # verify participant list changed
    assert email in activities[activity]["participants"]

    # duplicate attempt should return 400
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json()["detail"]


def test_remove_participant():
    activity = "Programming Class"
    email = "emma@mergington.edu"

    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp.status_code == 200
    assert email not in activities[activity]["participants"]

    # removing again should give 404
    resp2 = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp2.status_code == 404


def test_nonexistent_activity():
    resp = client.post("/activities/NoSuch/signup", params={"email": "x@x.com"})
    assert resp.status_code == 404

    resp2 = client.delete("/activities/NoSuch/participants", params={"email": "x@x.com"})
    assert resp2.status_code == 404
