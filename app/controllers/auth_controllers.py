import hashlib
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from app.db.connection import get_connection



def hash_password(password: str) -> str:
   
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{digest}"


def verify_password(plain: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split(":", 1)
        return hashlib.sha256((salt + plain).encode()).hexdigest() == digest
    except ValueError:
        return False



def create_user(username: str, password: str, dob: str) -> tuple[bool, str]:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, dob) VALUES (%s, %s, %s)",
            (username, hash_password(password), dob),
        )
        conn.commit()
        cur.close()
        return True, ""
    except psycopg2.IntegrityError:
        return False, "username_taken"
    except Exception as exc:
        return False, str(exc)
    finally:
        if conn:
            conn.close()


def get_user(username: str) -> dict | None:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        if conn:
            conn.close()
