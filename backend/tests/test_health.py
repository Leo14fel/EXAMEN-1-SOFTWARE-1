from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_identifies_backend_service() -> None:
    response = client.get("/health")
    assert response.json() == {"status": "ok", "service": "backend"}
