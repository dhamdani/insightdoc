"""Auth internal sederhana (FR-20/21): email + password hash (SHA-256+salt).

Catatan: MVP memakai SQLite lokal. Untuk produksi, ganti dengan SSO korporat
(Google Workspace/Microsoft 365) sesuai FR-20.
"""
from __future__ import annotations

import hashlib
import secrets
import time

from .storage import _conn, init_db


def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def register(email: str, password: str, name: str = "", department: str = "") -> dict:
    email = email.strip().lower()
    if "@" not in email or len(password) < 6:
        raise ValueError("Email tidak valid atau kata sandi <6 karakter. Invalid email or password <6 chars.")
    init_db()
    salt = secrets.token_hex(8)
    c = _conn()
    try:
        c.execute(
            "INSERT INTO users(email,name,department,password_hash,created_at) VALUES(?,?,?,?,?)",
            (email, name, department, f"{salt}${_hash(password, salt)}", time.time()))
        c.commit()
    except Exception as e:
        c.close()
        raise ValueError("Email sudah terdaftar. Email already registered.") from e
    c.close()
    return {"email": email, "name": name, "department": department}


def login(email: str, password: str) -> dict | None:
    init_db()
    c = _conn()
    r = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    c.close()
    if not r:
        return None
    try:
        salt, h = r["password_hash"].split("$")
    except ValueError:
        return None
    if _hash(password, salt) == h:
        return {"email": r["email"], "name": r["name"], "department": r["department"]}
    return None
