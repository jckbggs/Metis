import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv(Path(__file__).resolve().parent.parent / "chatbot" / ".env")

POSTGRES_DSN = os.getenv("POSTGRES_DSN")


def get_connection():
    return psycopg.connect(POSTGRES_DSN, row_factory=dict_row)