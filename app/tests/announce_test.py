from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_read_announcements():
    response = client.get("/announce/blog")
    assert response.status_code == 200
