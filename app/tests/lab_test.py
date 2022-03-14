from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_desktop_usage():
    response = client.get("/lab/desktops")
    assert response.status_code == 200


def test_get_num_users_in_lab():
    response = client.get("/lab/num_users")
    assert response.status_code == 200


def test_get_staff_in_lab():
    response = client.get("/lab/staff")
    assert response.status_code == 200
