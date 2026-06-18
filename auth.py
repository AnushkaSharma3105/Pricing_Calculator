import sqlite3
import bcrypt
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append("At least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("At least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("At least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("At least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("At least one special character (!@#$%^&* etc.)")
    return errors

def register_user(full_name, email, password):
    init_db()
    email = email.strip().lower()
    if not full_name.strip():
        return False, "Full name cannot be empty."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email address."
    pwd_errors = validate_password(password)
    if pwd_errors:
        return False, "Password must have: " + ", ".join(pwd_errors) + "."
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                  (full_name.strip(), email, pw_hash))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

def login_user(email, password):
    init_db()
    email = email.strip().lower()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, full_name, email, password_hash FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False, "No account found with this email.", None
    user_id, full_name, email_db, pw_hash = row
    if bcrypt.checkpw(password.encode(), pw_hash.encode()):
        return True, "Login successful!", {"id": user_id, "full_name": full_name, "email": email_db}
    return False, "Incorrect password.", None

def change_password(user_id, old_password, new_password):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        conn.close()
        return False, "User not found."
    if not bcrypt.checkpw(old_password.encode(), row[0].encode()):
        conn.close()
        return False, "Current password is incorrect."
    pwd_errors = validate_password(new_password)
    if pwd_errors:
        conn.close()
        return False, "New password must have: " + ", ".join(pwd_errors) + "."
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()
    return True, "Password updated successfully!"

def delete_account(user_id, password):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        conn.close()
        return False, "User not found."
    if not bcrypt.checkpw(password.encode(), row[0].encode()):
        conn.close()
        return False, "Incorrect password."
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True, "Account deleted."