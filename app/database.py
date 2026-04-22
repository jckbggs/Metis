import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv(Path(__file__).resolve().parent.parent / "chatbot" / ".env", override=True)


def get_connection():
    postgres_dsn = os.getenv("POSTGRES_DSN")
    if not postgres_dsn:
        raise RuntimeError("POSTGRES_DSN is not set")

    return psycopg.connect(postgres_dsn, row_factory=dict_row)