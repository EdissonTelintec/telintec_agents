import pytest

from agents_service.auth import TokenError, TokenVerifier, has_permission, permission_names


@pytest.fixture
def verifier(settings) -> TokenVerifier:
    return TokenVerifier(settings.token_keys_dir, settings.token_kids, 30, 24 * 3600)


def test_valid_token(verifier, sign):
    data = verifier.verify(sign())
    assert data["user"] == "pytest" and data["emp_id"] == 1


def test_leeway_tolerates_small_skew(verifier, sign):
    data = verifier.verify(sign({"exp": __import__("time").time() - 10}))
    assert data["user"] == "pytest"


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        ({"lifetime": -120}, "vencido"),
        ({"lifetime": 25 * 3600}, "mas de 24 h"),
        ({"kid": "otro"}, "kid desconocido"),
        ({"kid": None}, "sin kid"),
        ({"alg": "HS256"}, "HS256"),
    ],
)
def test_rejections(verifier, sign, kwargs, reason):
    with pytest.raises(TokenError):
        verifier.verify(sign(**kwargs))


def test_requires_exp_and_iat(verifier, sign):
    with pytest.raises(TokenError):
        verifier.verify(sign(lifetime=None))  # sin exp ni iat
    with pytest.raises(TokenError):
        verifier.verify(sign({"iat": None}))  # exp sin iat


def test_garbage(verifier):
    with pytest.raises(TokenError):
        verifier.verify("esto-no-es-un-jwt")


def test_missing_key_file_is_rejected(settings, sign):
    v = TokenVerifier(settings.token_keys_dir, ("test", "lambda"), 30, 24 * 3600)
    with pytest.raises(TokenError, match="kid no aceptado"):
        v.verify(sign(kid="lambda"))  # kid aceptado pero sin archivo .pem


def test_permissions_helpers():
    token = {"permissions": {"0": "App.Department.Basic", "1": "App.Department.RRHH"}}
    assert permission_names(token) == ["App.Department.Basic", "App.Department.RRHH"]
    assert has_permission(token, "App.Department.RRHH")
    assert not has_permission(token, "App.Department.ALMACEN")
    assert has_permission({"permissions": ["App.Department.Administrator"]}, "lo-que-sea")
    assert permission_names({}) == []
