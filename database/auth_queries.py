from database.database import get_connection

def get_user_by_username(username: str):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT username, password_hash
            FROM users
            WHERE username = %s
            """,
            (username,)
        )
        return cur.fetchone()