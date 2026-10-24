"""Ligação ao PostgreSQL + pgvector."""

import psycopg
from pgvector.psycopg import register_vector

from app.config import get_settings


def get_connection() -> psycopg.Connection:
    """Abre uma ligação nova e regista o tipo `vector`.

    Uso:
        with get_connection() as conn:
            conn.execute("SELECT 1")
    """
    conn = psycopg.connect(get_settings().database_url)
    register_vector(conn)
    return conn
