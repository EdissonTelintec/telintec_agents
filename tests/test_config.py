from pathlib import Path

import pytest

from agents_service.config import load_settings

BASE = {"AGENTS_ENVIRONMENT": "dev", "DB_HOST": "h", "DB_USER": "u", "DB_PASSWORD": "p"}


def test_environment_required(tmp_path: Path):
    for value in (None, "", "test", "production"):
        env = {k: v for k, v in BASE.items() if k != "AGENTS_ENVIRONMENT"}
        if value is not None:
            env["AGENTS_ENVIRONMENT"] = value
        with pytest.raises(RuntimeError, match="AGENTS_ENVIRONMENT"):
            load_settings(env_file=tmp_path / "no.env", environ=env)


def test_db_keys_required(tmp_path: Path):
    env = {k: v for k, v in BASE.items() if k != "DB_PASSWORD"}
    with pytest.raises(RuntimeError, match="DB_PASSWORD"):
        load_settings(env_file=tmp_path / "no.env", environ=env)


def test_defaults_dev(tmp_path: Path):
    s = load_settings(env_file=tmp_path / "no.env", environ=BASE)
    assert s.environment == "dev"
    assert s.token_kids == ("lambda", "dev")
    assert s.model == "gpt-5.4-mini" and s.model_guardrail == "gpt-5.4-nano"
    assert s.limit_messages_per_conversation == 30
    assert s.db_agents == "sql_telintec_mod_agents"
    assert s.cors_origins == ()


def test_defaults_prod_and_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "AGENTS_ENVIRONMENT=prod\nDB_HOST=rds\nDB_USER=agents_svc\nDB_PASSWORD=s3cret\n"
        "CORS_ORIGINS=https://telintec.mx, https://telintec.com.mx\nLIMIT_OUTPUT_TOKENS=700\n",
        encoding="utf-8",
    )
    s = load_settings(env_file=env_file, environ={})
    assert s.environment == "prod" and s.db_user == "agents_svc"
    assert s.token_kids == ("lambda",)
    assert s.token_keys_dir == tmp_path  # las llaves publicas viven junto al .env
    assert s.cors_origins == ("https://telintec.mx", "https://telintec.com.mx")
    assert s.limit_output_tokens == 700


def test_environ_wins_over_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("AGENTS_ENVIRONMENT=prod\nDB_HOST=rds\nDB_USER=u\nDB_PASSWORD=p\n", encoding="utf-8")
    s = load_settings(env_file=env_file, environ={"AGENTS_ENVIRONMENT": "dev"})
    assert s.environment == "dev"
