from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_bounce_shorturl():
    response = client.get("/shorturl/accounts", allow_redirects=False)
    assert response.status_code == 301


def test_bounce_shorturl_invalid():
    response = client.get("/shorturl/odnwoandowa", allow_redirects=False)
    assert response.status_code == 404
