from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_profile_routes_exist():
    # Smoke test endpoints exist (won't hit DB without env)
    assert any(r.path.startswith('/api/profile') for r in app.routes)


