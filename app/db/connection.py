import os
import psycopg2

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://myuser:mypassword@db:5432/mydb"
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)
