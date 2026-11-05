# -*- coding: utf-8 -*-
"""Verificacion del JWT de la webapp: solo ES256, por `kid`, con `exp` e `iat` y hasta 24 h.

Espejo de `unpack_token` del API (GUITelintec/templates/resources/methods/Functions_Aux_Login.py)
tras el corte a tokens de 24 h (docs/tokens_solo_24h.md): aqui nunca hubo camino HS256.
El encabezado `Authorization` trae el JWT crudo, sin `Bearer `.
"""

from __future__ import annotations

from pathlib import Path

import jwt
from fastapi import Request

ADMINISTRATOR = "App.Department.Administrator"
UNAUTHORIZED_MSG = "No autorizado. Token invalido"


class TokenError(Exception):
    """Token ausente, mal formado, de otro algoritmo, de un kid no aceptado o vencido."""


class Unauthorized(Exception):
    """La peticion no trae un token valido; se responde 401 con el envelope del API."""

    def __init__(self, error: str):
        super().__init__(error)
        self.error = error


class TokenVerifier:
    def __init__(self, keys_dir: Path, kids: tuple[str, ...], leeway_seconds: int, max_lifetime_seconds: int):
        self._keys_dir = keys_dir
        self._kids = kids
        self._leeway = leeway_seconds
        self._max_lifetime = max_lifetime_seconds
        self._cache: dict[str, str] = {}

    def public_key(self, kid: str | None) -> str | None:
        """PEM de la llave publica del kid, leida una vez por proceso; None si no se acepta."""
        if not kid or kid not in self._kids:
            return None
        if kid not in self._cache:
            path = self._keys_dir / f"token_public_{kid}.pem"
            try:
                self._cache[kid] = path.read_text(encoding="utf-8")
            except OSError:
                return None
        return self._cache[kid]

    def verify(self, token: str) -> dict:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as e:
            raise TokenError(f"token mal formado: {e}") from e
        if header.get("alg") != "ES256":
            raise TokenError("solo se aceptan tokens ES256")
        kid = header.get("kid")
        key = self.public_key(kid)
        if key is None:
            raise TokenError(f"kid no aceptado: {kid}")
        try:
            data = jwt.decode(
                token,
                key,
                algorithms=["ES256"],
                leeway=self._leeway,
                options={"require": ["exp", "iat"]},
            )
        except jwt.PyJWTError as e:
            raise TokenError(str(e)) from e
        if data["exp"] - data["iat"] > self._max_lifetime:
            raise TokenError("token con vigencia de mas de 24 h")
        return data


def permission_names(token_data: dict) -> list[str]:
    """Los permisos del token vienen como dict por indice ({"0": "App.Department.Basic", ...}) o lista."""
    raw = token_data.get("permissions") or {}
    values = raw.values() if isinstance(raw, dict) else raw
    return [str(v) for v in values]


def has_permission(token_data: dict, *names: str) -> bool:
    """Match exacto contra el catalogo (como `verify_exact_permission` del API); Administrator pasa siempre."""
    owned = set(permission_names(token_data))
    return ADMINISTRATOR in owned or any(n in owned for n in names)


def current_user(request: Request) -> dict:
    """Dependencia de FastAPI: claims del JWT crudo del encabezado `Authorization`."""
    token = request.headers.get("Authorization", "").strip()
    if not token:
        raise Unauthorized("falta el encabezado Authorization")
    verifier: TokenVerifier = request.app.state.verifier
    try:
        return verifier.verify(token)
    except TokenError as e:
        raise Unauthorized(str(e)) from e
