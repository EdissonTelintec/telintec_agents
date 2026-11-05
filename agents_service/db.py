# -*- coding: utf-8 -*-
"""Acceso a MySQL con aiomysql: un pool por proceso, creado al primer uso.

Los nombres de tabla van calificados con el esquema (`sql_telintec_mod_agents.agent_messages`),
asi que la conexion no fija base. Autocommit: cada sentencia es su propia transaccion.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import aiomysql

from agents_service.config import Settings


class Database:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._pool: aiomysql.Pool | None = None

    async def pool(self) -> aiomysql.Pool:
        if self._pool is None:
            s = self._settings
            self._pool = await aiomysql.create_pool(
                host=s.db_host,
                port=s.db_port,
                user=s.db_user,
                password=s.db_password,
                db=None,
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=s.db_pool_size,
                cursorclass=aiomysql.DictCursor,
            )
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def fetch_one(self, sql: str, args: Sequence[Any] = ()) -> dict[str, Any] | None:
        pool = await self.pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, args)
                row = await cur.fetchone()
                return dict(row) if row is not None else None

    async def fetch_all(self, sql: str, args: Sequence[Any] = ()) -> list[dict[str, Any]]:
        pool = await self.pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, args)
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def execute(self, sql: str, args: Sequence[Any] = ()) -> tuple[int, int]:
        """Ejecuta INSERT/UPDATE/DELETE. Devuelve (filas afectadas, lastrowid)."""
        pool = await self.pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, args)
                return cur.rowcount, cur.lastrowid or 0
