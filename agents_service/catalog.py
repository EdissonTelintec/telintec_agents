# -*- coding: utf-8 -*-
"""Catalogo publico para el agente virtual de ventas (solo lectura).

`products_simple` es la version reducida del catalogo SYSCOM: `name` normalizado (minusculas, sin
acentos, sin digitos ni puntuacion) con indice FULLTEXT, `brand` en minusculas y `model`.
`products_services` trae el nombre completo, `price_retail` (**MXN con IVA**), `available_quantity`,
`description` e `image`. `price_provider` nunca se lee aqui.

La busqueda usa FULLTEXT en modo natural (ranking por relevancia; tolera palabras que no estan)
con la consulta normalizada igual que `name`; marca y modelo filtran aparte. Devuelve pocas filas
y campos cortos para gastar pocos tokens.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from agents_service.db import Database

MAX_RESULTS = 8
_STOPWORDS = frozenset(
    {"de", "del", "la", "el", "los", "las", "para", "con", "a", "y", "o", "u", "en", "un", "una", "unos", "unas",
     "por", "al", "que", "me", "mi", "tu", "su", "lo", "le", "es", "busco", "quiero", "necesito", "tienen", "tiene"}
)


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    brand: str
    model: str
    price_mxn: float  # precio de lista, MXN con IVA
    available: bool
    stock: int
    image: str | None
    description: str | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.description is None:
            d.pop("description")
        return d


def normalize_query(text: str) -> str:
    """Misma forma que `products_simple.name`: minusculas, sin acentos, solo letras, sin muletillas."""
    text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z ]+", " ", text)
    tokens = [t for t in text.split() if t not in _STOPWORDS]
    return " ".join(tokens)


def _row_to_product(row: dict[str, Any], with_description: bool = False) -> Product:
    stock = int(row.get("available_quantity") or 0)
    return Product(
        product_id=int(row["product_id"]),
        name=str(row["name"]).strip(),
        brand=str(row.get("marca") or "").strip(),
        model=str(row.get("model") or "").strip(),
        price_mxn=round(float(row.get("price_retail") or 0), 2),
        available=stock > 0,
        stock=stock,
        image=(row.get("image") or None),
        description=(str(row["description"]).strip() if with_description and row.get("description") else None),
    )


async def search_products(
    db: Database,
    query: str,
    brand: str | None = None,
    model: str | None = None,
    only_available: bool = True,
    limit: int = 5,
    catalog: str = "sql_telintec",
) -> list[Product]:
    """Busca en el catalogo. `query` en lenguaje natural; `brand` y `model` filtran con LIKE."""
    limit = max(1, min(limit, MAX_RESULTS))
    q = normalize_query(query or "")
    if not q and not (brand or "").strip() and not (model or "").strip():
        return []  # sin criterio no se devuelve el catalogo
    where: list[str] = []
    args: list[Any] = []
    select_score = "0 AS score"
    if q:
        select_score = "MATCH(s.name) AGAINST (%s) AS score"
        args.append(q)
        where.append("MATCH(s.name) AGAINST (%s)")
    # marca y model son utf8mb4_bin: LIKE distingue mayusculas, por eso LOWER en ambos lados
    if brand:
        where.append("LOWER(p.marca) LIKE LOWER(%s)")
    if model:
        where.append("LOWER(p.model) LIKE LOWER(%s)")
    if only_available:
        where.append("p.available_quantity > 0")
    if not where:
        return []
    # los args del WHERE van despues del del SELECT
    if q:
        args.append(q)
    if brand:
        args.append(f"%{brand.strip()}%")
    if model:
        args.append(f"%{model.strip()}%")
    rows = await db.fetch_all(
        f"SELECT p.product_id, p.name, p.marca, p.model, p.price_retail, p.available_quantity, p.image, {select_score} "
        f"FROM {catalog}.products_simple s JOIN {catalog}.products_services p ON p.product_id = s.product_id "
        f"WHERE {' AND '.join(where)} "
        f"ORDER BY score DESC, p.available_quantity DESC, p.product_id LIMIT %s",
        args + [limit],
    )
    return [_row_to_product(r) for r in rows]


async def get_product(db: Database, product_id: int, catalog: str = "sql_telintec") -> Product | None:
    row = await db.fetch_one(
        f"SELECT product_id, name, marca, model, price_retail, available_quantity, image, description "
        f"FROM {catalog}.products_services WHERE product_id = %s",
        (product_id,),
    )
    return _row_to_product(row, with_description=True) if row else None
