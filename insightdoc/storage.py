"""Storage SQLite: users, documents, reports + log audit (PRD §8 Auditability)."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "insightdoc.db"


def _conn(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(p))
    c.row_factory = sqlite3.Row
    return c


def init_db(path: Path | None = None) -> None:
    c = _conn(path)
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL, name TEXT, department TEXT,
          password_hash TEXT NOT NULL, created_at REAL
        );
        CREATE TABLE IF NOT EXISTS documents(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_email TEXT, filename TEXT, category TEXT,
          n_rows INTEGER, created_at REAL, analysis_json TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_email TEXT, action TEXT, detail TEXT, created_at REAL
        );
        """
    )
    c.commit()
    c.close()


def audit(user_email: str, action: str, detail: str = "", path: Path | None = None) -> None:
    init_db(path)
    c = _conn(path)
    c.execute("INSERT INTO audit_log(user_email,action,detail,created_at) VALUES(?,?,?,?)",
              (user_email, action, detail, time.time()))
    c.commit()
    c.close()


def save_document(user_email: str, filename: str, category: str, n_rows: int,
                  analysis: dict, path: Path | None = None) -> int:
    init_db(path)
    safe = {k: v for k, v in analysis.items() if k in
            ("category", "mapping", "cleaning", "result", "recommendations",
             "executive_summary", "n_rows", "lang", "detected")}
    c = _conn(path)
    cur = c.execute(
        "INSERT INTO documents(user_email,filename,category,n_rows,created_at,analysis_json) VALUES(?,?,?,?,?,?)",
        (user_email, filename, category, n_rows, time.time(), json.dumps(safe, default=str)))
    c.commit()
    doc_id = cur.lastrowid
    c.close()
    audit(user_email, "upload_analyze", f"{filename} [{category}]", path)
    return int(doc_id)


def list_documents(user_email: str | None = None, path: Path | None = None) -> list[dict]:
    init_db(path)
    c = _conn(path)
    if user_email:
        rows = c.execute("SELECT * FROM documents WHERE user_email=? ORDER BY created_at DESC", (user_email,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_document(doc_id: int, path: Path | None = None) -> dict | None:
    init_db(path)
    c = _conn(path)
    r = c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    c.close()
    if not r:
        return None
    d = dict(r)
    try:
        d["analysis"] = json.loads(d["analysis_json"])
    except Exception:
        d["analysis"] = {}
    return d


def delete_document(doc_id: int, user_email: str, path: Path | None = None) -> None:
    c = _conn(path)
    c.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    c.commit()
    c.close()
    audit(user_email, "delete", f"doc {doc_id}", path)
