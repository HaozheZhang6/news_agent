from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_conversation_routes_exist():
    assert any(r.path.startswith('/api/conversation') for r in app.routes)


