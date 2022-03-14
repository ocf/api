from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_get_staff_hours():
    response = client.get("/hours/staff")
    assert response.status_code == 200


def test_get_hours_today():
    response = client.get("/hours/today")
    assert response.status_code == 200


def test_get_hours_date():
    response = client.get("/hours/2022-02-22")
    assert response.status_code == 200
