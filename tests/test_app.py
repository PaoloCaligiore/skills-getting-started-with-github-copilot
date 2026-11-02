from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
	original_activities = deepcopy(activities)
	try:
		with TestClient(app) as test_client:
			yield test_client
	finally:
		activities.clear()
		activities.update(original_activities)


def test_get_activities_returns_data_without_cache(client):
	response = client.get("/activities")

	assert response.status_code == 200
	assert response.headers["cache-control"] == "no-store"
	assert response.json()["Basketball Club"]["participants"] == []


def test_signup_adds_participant(client):
	response = client.post(
		"/activities/Basketball Club/signup",
		params={"email": "student@example.com"},
	)

	assert response.status_code == 200
	assert response.json() == {
		"message": "Signed up student@example.com for Basketball Club"
	}
	assert "student@example.com" in activities["Basketball Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
	path = "/activities/Basketball Club/signup"
	params = {"email": "student@example.com"}

	assert client.post(path, params=params).status_code == 200
	response = client.post(path, params=params)

	assert response.status_code == 400
	assert response.json()["detail"] == "Student is already signed up for this activity"
	assert activities["Basketball Club"]["participants"].count("student@example.com") == 1


def test_signup_rejects_unknown_activity(client):
	response = client.post(
		"/activities/Unknown Club/signup",
		params={"email": "student@example.com"},
	)

	assert response.status_code == 404
	assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
	path = "/activities/Basketball Club/signup"
	params = {"email": "student@example.com"}
	assert client.post(path, params=params).status_code == 200

	response = client.delete(path, params=params)

	assert response.status_code == 200
	assert response.json() == {
		"message": "Removed student@example.com from Basketball Club"
	}
	assert "student@example.com" not in activities["Basketball Club"]["participants"]


def test_unregister_rejects_unregistered_participant(client):
	response = client.delete(
		"/activities/Basketball Club/signup",
		params={"email": "student@example.com"},
	)

	assert response.status_code == 404
	assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
	response = client.delete(
		"/activities/Unknown Club/signup",
		params={"email": "student@example.com"},
	)

	assert response.status_code == 404
	assert response.json()["detail"] == "Activity not found"
