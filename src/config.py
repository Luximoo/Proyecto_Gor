"""Configuración centralizada de la aplicación."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Busca el archivo .env en la raíz del proyecto
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    # Si python-dotenv no está instalado aún, se usan las variables del sistema o valores por defecto
    pass


def get_db_config() -> dict:
    """Devuelve el diccionario de conexión para mysql.connector."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "gorditas"),
        "autocommit": False,
    }


# Constantes de interfaz y comportamiento
WINDOW_WIDTH = 375
WINDOW_HEIGHT = 667
POLL_INTERVAL_SECONDS = 1.5
ERROR_RETRY_SECONDS = 5.0
