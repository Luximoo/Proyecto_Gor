"""Conexión a base de datos MySQL y funciones de compatibilidad."""

from contextlib import contextmanager
import logging
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


def obtener_pedidos_activos() -> dict[int, str]:
    """
    Obtiene los pedidos pendientes desde el nuevo esquema relacional y los formatea
    como texto para mantener `/home` funcional hasta su rediseño en la Fase 6.
    """
    from data.repositorio import obtener_pedidos_pendientes
    from domain.modelos import formatear_pedido

    pedidos = obtener_pedidos_pendientes()
    resultado: dict[int, str] = {}
    for ped in pedidos:
        if ped.id is not None:
            resultado[ped.id] = formatear_pedido(ped)
    return resultado


def completar_pedido(order_id: int) -> bool:
    """Marca un pedido como COMPLETADO usando el nuevo repositorio relacional."""
    from data.repositorio import marcar_pedido_completado

    ok = marcar_pedido_completado(order_id)
    logging.info(f"Pedido #{order_id} completado={ok}")
    return ok
