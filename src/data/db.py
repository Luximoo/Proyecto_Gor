"""Gestión de conexiones a la base de datos MySQL."""

from contextlib import contextmanager
from typing import Generator

import mysql.connector
from mysql.connector.connection import MySQLConnection

from config import get_db_config


@contextmanager
def get_connection() -> Generator[MySQLConnection, None, None]:
    """Context manager que abre y cierra de forma segura una conexión a MySQL."""
    conn = mysql.connector.connect(**get_db_config())
    try:
        yield conn
    finally:
        if conn.is_connected():
            conn.close()
