from fastapi.testclient import TestClient

from agents_service.main import create_app


def test_health_without_db(settings):
    with TestClient(create_app(settings)) as client:
        r = client.get("/agents/health")
        assert r.status_code == 200 and r.text == "OK"


def test_me_requires_token(settings, sign):
    with TestClient(create_app(settings)) as client:
        r = client.get("/agents/assistant/me")
        assert r.status_code == 401
        assert r.json() == {"data": None, "msg": "No autorizado. Token invalido", "error": "falta el encabezado Authorization"}

        r = client.get("/agents/assistant/me", headers={"Authorization": "Bearer " + sign()})
        assert r.status_code == 401  # el JWT va crudo, sin Bearer

        r = client.get("/agents/assistant/me", headers={"Authorization": sign()})
        assert r.status_code == 200
        body = r.json()
        assert body["msg"] == "ok" and body["data"]["user"] == "pytest"
        assert body["data"]["permissions"] == ["App.Department.Basic"]


def test_cors_allowlist(settings, sign):
    with TestClient(create_app(settings)) as client:
        ok = client.options(
            "/agents/health",
            headers={"Origin": "https://telintec.mx", "Access-Control-Request-Method": "GET"},
        )
        assert ok.headers.get("access-control-allow-origin") == "https://telintec.mx"
        bad = client.options(
            "/agents/health",
            headers={"Origin": "https://otro.sitio", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" not in bad.headers
