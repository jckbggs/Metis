import hashlib
import secrets
import psycopg

from database.database import get_connection


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{digest}"


def create_user(username: str, password: str, dob: str):
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
    except psycopg.IntegrityError:
        return False, "username_taken"
    except Exception:
        return False, "db_error"
    finally:
        if conn:
            conn.close()