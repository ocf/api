from main import app

from fastapi.testclient import TestClient

client = TestClient(app)


def test_read_announcements():
    response = client.get("/announce/blog")
    assert response.status_code == 200
