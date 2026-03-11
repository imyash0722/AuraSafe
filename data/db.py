import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aurasafe.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS products_cache (
            barcode TEXT PRIMARY KEY,
            product_json TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT DEFAULT '',
            dob TEXT DEFAULT '',
            blood_group TEXT DEFAULT '',
            allergies TEXT DEFAULT '[]',
            conditions TEXT DEFAULT '[]',
            medications TEXT DEFAULT '[]',
            emergency_contact TEXT DEFAULT '',
            pin_hash TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS triage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT NOT NULL,
            urgency TEXT NOT NULL,
            guidance TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            product_name TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Ensure default profile row exists
    c.execute("""
        INSERT OR IGNORE INTO user_profile (id) VALUES (1)
    """)

    conn.commit()
    conn.close()


def get_user_profile() -> dict:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    conn.close()
    if row:
        return {
            "name": row["name"] or "",
            "dob": row["dob"] or "",
            "blood_group": row["blood_group"] or "",
            "allergies": json.loads(row["allergies"] or "[]"),
            "conditions": json.loads(row["conditions"] or "[]"),
            "medications": json.loads(row["medications"] or "[]"),
            "emergency_contact": row["emergency_contact"] or "",
        }
    return {"name": "", "dob": "", "blood_group": "", "allergies": [], "conditions": [], "medications": [], "emergency_contact": ""}


def save_user_profile(profile: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE user_profile SET
            name = ?,
            dob = ?,
            blood_group = ?,
            allergies = ?,
            conditions = ?,
            medications = ?,
            emergency_contact = ?
        WHERE id = 1
    """, (
        profile.get("name", ""),
        profile.get("dob", ""),
        profile.get("blood_group", ""),
        json.dumps(profile.get("allergies", [])),
        json.dumps(profile.get("conditions", [])),
        json.dumps(profile.get("medications", [])),
        profile.get("emergency_contact", ""),
    ))
    conn.commit()
    conn.close()


def save_triage(symptoms: list, urgency: str, guidance: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO triage_history (symptoms, urgency, guidance, timestamp)
        VALUES (?, ?, ?, ?)
    """, (json.dumps(symptoms), urgency, guidance, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def save_scan(barcode: str, product_name: str, overall_score: int, verdict: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO scan_history (barcode, product_name, overall_score, verdict, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (barcode, product_name, overall_score, verdict, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def get_scan_history(limit: int = 20) -> list:
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute("""
        SELECT * FROM scan_history ORDER BY timestamp DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
