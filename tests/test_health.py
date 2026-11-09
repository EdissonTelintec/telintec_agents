from dataclasses import replace

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


# El preflight que manda el componente de ChatKit (capturado en el navegador, docs/error-de-chatkit.md):
# chatkit-frame-instance-id lo agrega ChatKit por su cuenta.
CHATKIT_PREFLIGHT_HEADERS = "accept-language,authorization,chatkit-frame-instance-id,content-type,x-page-context"


def _preflight(
    client: TestClient, origin: str, headers: str = CHATKIT_PREFLIGHT_HEADERS, path: str = "/agents/assistant/chatkit"
):
    return client.options(
        path,
        headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": headers},
    )


def test_cors_dev_accepts_localhost(settings):
    assert settings.environment == "dev"
    with TestClient(create_app(settings)) as client:
        for origin in ("http://localhost:3000", "https://localhost:3000", "http://127.0.0.1:5173", "http://localhost"):
            r = _preflight(client, origin)
            assert r.status_code == 200 and r.headers["access-control-allow-origin"] == origin
        assert _preflight(client, "https://telintec.mx").status_code == 200  # la lista sigue
        assert _preflight(client, "http://localhost.otro.sitio").status_code == 400
        assert _preflight(client, "http://192.168.1.50:3000").status_code == 400
        assert _preflight(client, "http://localhost:3000", "content-type,x-requested-with").status_code == 400


def test_cors_dev_without_list(settings):
    with TestClient(create_app(replace(settings, cors_origins=()))) as client:
        assert _preflight(client, "http://localhost:3000").status_code == 200


def test_cors_prod_is_closed_list(settings):
    with TestClient(create_app(replace(settings, environment="prod"))) as client:
        for path in ("/agents/assistant/chatkit", "/agents/sales/chatkit"):
            r = _preflight(client, "https://telintec.mx", path=path)
            assert r.status_code == 200, r.text
            assert "chatkit-frame-instance-id" in r.headers["access-control-allow-headers"].lower()
        assert _preflight(client, "http://localhost:3000").status_code == 400
        assert _preflight(client, "https://telintec.mx", "content-type,x-requested-with").status_code == 400
        pna = client.options(
            "/agents/health",
            headers={
                "Origin": "https://telintec.mx",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Private-Network": "true",
            },
        )
        assert pna.status_code == 400
