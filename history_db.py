import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "quotation_history.db")


def init_quote_history_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS quotation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quotation_id TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            company_name TEXT,
            quotation_json TEXT NOT NULL,
            grand_total REAL NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration: add user_email column if it doesn't exist yet
    try:
        c.execute("ALTER TABLE quotation_history ADD COLUMN user_email TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()
    conn.close()


def save_quotation_history(quotation_id, user_email, customer_name, company_name, quotation_payload, grand_total):
    init_quote_history_db()
    payload_json = json.dumps(quotation_payload, ensure_ascii=False)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing = c.execute(
        "SELECT id FROM quotation_history WHERE quotation_id = ?",
        (quotation_id,)
    ).fetchone()

    if existing:
        c.execute(
            """
            UPDATE quotation_history
            SET user_email = ?, customer_name = ?, company_name = ?, quotation_json = ?, grand_total = ?
            WHERE quotation_id = ?
            """,
            (user_email, customer_name, company_name, payload_json, grand_total, quotation_id)
        )
    else:
        c.execute(
            """
            INSERT INTO quotation_history (
                quotation_id, user_email, customer_name, company_name,
                quotation_json, grand_total, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quotation_id,
                user_email,
                customer_name,
                company_name,
                payload_json,
                grand_total,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

    conn.commit()
    conn.close()


def fetch_all_quotations(user_email=None):
    init_quote_history_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user_email = (user_email or "").strip().lower()
    if not user_email:
        conn.close()
        return []  # no identified user -> show nothing, never everything
    rows = c.execute(
        "SELECT id, quotation_id, customer_name, company_name, grand_total, created_at"
        " FROM quotation_history WHERE LOWER(TRIM(user_email)) = ?"
        " ORDER BY created_at DESC",
        (user_email,)
    ).fetchall()
    conn.close()
    

    return [
        {
            "id": row[0],
            "quotation_id": row[1],
            "customer_name": row[2],
            "company_name": row[3],
            "grand_total": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def fetch_quotation_by_db_id(record_id):
    init_quote_history_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute(
        "SELECT id, quotation_id, customer_name, company_name, quotation_json, grand_total, created_at"
        " FROM quotation_history WHERE id = ?",
        (record_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "quotation_id": row[1],
        "customer_name": row[2],
        "company_name": row[3],
        "quotation_json": row[4],
        "grand_total": row[5],
        "created_at": row[6],
    }


def delete_quotation_by_id(record_id):
    init_quote_history_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM quotation_history WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
