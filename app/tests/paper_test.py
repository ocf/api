from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_get_paper_quota_unauthorized():
    response = client.get("/quotas/paper")
    assert response.status_code == 401
