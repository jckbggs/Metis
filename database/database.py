import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        raise ValueError("POSTGRES_DSN is missing in .env")