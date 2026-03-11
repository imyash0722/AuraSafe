"""
Local product cache backed by the SQLite products_cache table.
Used by the scanner to avoid redundant network calls.
"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from data.db import get_connection

CACHE_TTL_HOURS = 72  # Re-fetch after 3 days


def get_cached_product(barcode: str) -> dict | None:
    """Return cached product dict if present and not stale, else None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT product_json, fetched_at FROM products_cache WHERE barcode = ?",
            (barcode,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return None

    fetched_at = datetime.fromisoformat(row["fetched_at"]).replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - fetched_at > timedelta(hours=CACHE_TTL_HOURS):
        return None  # Stale — caller should re-fetch

    try:
        return json.loads(row["product_json"])
    except Exception:
        return None


def save_product(barcode: str, product: dict) -> None:
    """Persist a product dict to the local cache."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO products_cache (barcode, product_json, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(barcode) DO UPDATE SET
                product_json = excluded.product_json,
                fetched_at   = excluded.fetched_at
            """,
            (barcode, json.dumps(product), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
