# -*- coding: utf-8 -*-
"""Busqueda en el catalogo contra la BD de dev del .env (se salta sin BD)."""

from __future__ import annotations

import pytest

from agents_service.catalog import Product, get_product, normalize_query, search_products
from agents_service.config import load_settings
from agents_service.db import Database


def test_normalize_query():
    assert normalize_query("Cámara IP para exterior Hikvision 4 MP") == "camara ip exterior hikvision mp"
    assert normalize_query("Busco un switch de 24 puertos PoE") == "switch puertos poe"
    assert normalize_query("  ") == ""
    assert normalize_query("DS-2CD1023G0-I") == "ds cd g i"


@pytest.fixture
async def db():
    try:
        settings = load_settings()
    except RuntimeError as e:
        pytest.skip(f"sin .env utilizable: {e}")
    if settings.environment != "dev":
        pytest.skip("solo contra dev")
    database = Database(settings)
    try:
        await database.fetch_one("SELECT 1 AS x")
    except Exception as e:  # noqa: BLE001
        await database.close()
        pytest.skip(f"BD de dev no disponible: {e}")
    try:
        yield database
    finally:
        await database.close()


async def test_search_natural(db: Database):
    found = await search_products(db, "switch 24 puertos poe", limit=5)
    assert 1 <= len(found) <= 5
    assert all(isinstance(p, Product) and p.available and p.stock > 0 for p in found)
    assert any("switch" in p.name.lower() for p in found)
    d = found[0].as_dict()
    assert set(d) == {"product_id", "name", "brand", "model", "price_mxn", "available", "stock", "image"}
    assert "price_provider" not in d


async def test_search_brand_and_model(db: Database):
    only_hik = await search_products(db, "camara bala exterior", brand="hikvision", limit=5)
    assert only_hik and all("HIKVISION" in p.brand.upper() for p in only_hik)  # LIKE: tambien "HiLook by HIKVISION"
    by_model = await search_products(db, "", model="DS-2CD1023G0-I", only_available=False, limit=3)
    assert by_model and all("DS-2CD1023G0-I" in p.model for p in by_model)


async def test_search_limits_and_empty(db: Database):
    assert await search_products(db, "", limit=5) == []  # sin criterio no se devuelve el catalogo
    many = await search_products(db, "cable", limit=50)
    assert len(many) <= 8  # tope de MAX_RESULTS


async def test_get_product(db: Database):
    found = await search_products(db, "switch poe", limit=1)
    assert found
    detail = await get_product(db, found[0].product_id)
    assert detail is not None and detail.product_id == found[0].product_id
    assert detail.description is not None and detail.price_mxn == found[0].price_mxn
    assert await get_product(db, -1) is None
