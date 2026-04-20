import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

env_path = Path(__file__).resolve().parent.parent / "chatbot" / ".env"
print("Loading env from:", env_path)

load_dotenv(env_path, override=True)

POSTGRES_DSN = os.getenv("POSTGRES_DSN")
print("POSTGRES_DSN actually loaded:", POSTGRES_DSN)

def get_connection():
    return psycopg.connect(POSTGRES_DSN, row_factory=dict_row)