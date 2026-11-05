# -*- coding: utf-8 -*-
"""Fixtures: par de llaves ES256 de prueba (kid `test`) y Settings sin .env."""

from __future__ import annotations

import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from agents_service.config import Settings, load_settings


@pytest.fixture(scope="session")
def keypair(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    """Carpeta con `token_public_test.pem` y la privada PEM para firmar."""
    keys_dir = tmp_path_factory.mktemp("keys")
    private = ec.generate_private_key(ec.SECP256R1())
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    (keys_dir / "token_public_test.pem").write_text(public_pem, encoding="utf-8")
    return keys_dir, private_pem


@pytest.fixture
def settings(keypair: tuple[Path, str], tmp_path: Path) -> Settings:
    keys_dir, _ = keypair
    environ = {
        "AGENTS_ENVIRONMENT": "dev",
        "DB_HOST": "127.0.0.1",
        "DB_USER": "x",
        "DB_PASSWORD": "x",
        "TOKEN_PUBLIC_KEYS_DIR": str(keys_dir),
        "TOKEN_PUBLIC_KIDS": "test",
        "CORS_ORIGINS": "https://telintec.mx",
    }
    return load_settings(env_file=tmp_path / "no.env", environ=environ)


@pytest.fixture
def sign(keypair: tuple[Path, str]):
    """sign(claims, kid='test', alg='ES256', lifetime=3600) -> token."""
    _, private_pem = keypair

    def _sign(claims: dict | None = None, kid: str | None = "test", alg: str = "ES256", lifetime: int | None = 3600):
        now = int(time.time())
        payload = {"user": "pytest", "emp_id": 1, "name": "Py Test", "permissions": {"0": "App.Department.Basic"}}
        if lifetime is not None:
            payload.update({"iat": now, "exp": now + lifetime})
        payload.update(claims or {})
        headers = {"kid": kid} if kid else {}
        key = private_pem if alg == "ES256" else "secreto-hs256"
        return jwt.encode(payload, key, algorithm=alg, headers=headers)

    return _sign
