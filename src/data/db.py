"""Acceso a base de datos MySQL y operaciones sobre la tabla `pedidos`."""

from contextlib import contextmanager
from enum import IntEnum
import logging
from typing import Generator

import mysql.connector
from mysql.connector.connection import MySQLConnection

from config import get_db_config


class EstadoPedido(IntEnum):
    """Estados posibles de un pedido en la base de datos."""

    PENDIENTE = 1
    COMPLETADO = 3


@contextmanager
def get_connection() -> Generator[MySQLConnection, None, None]:
    """Context manager que abre y cierra de forma segura una conexión a MySQL."""
    conn = mysql.connector.connect(**get_db_config())
    try:
        yield conn
    finally:
        if conn.is_connected():
            conn.close()


def crear_pedido(pedido_texto: str) -> int:
    """
    Inserta un nuevo pedido con estado PENDIENTE de forma parametrizada (segura contra SQL Injection).
    Retorna el ID del pedido creado.
    """
    query = "INSERT INTO pedidos (estado, pedido) VALUES (%s, %s)"
    params = (int(EstadoPedido.PENDIENTE), pedido_texto)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            nuevo_id = cursor.lastrowid or 0
            logging.info(f"Nuevo pedido creado en DB con ID: {nuevo_id}")
            return nuevo_id


def obtener_pedidos_activos() -> dict[int, str]:
    """
    Consulta todos los pedidos con estado PENDIENTE.
    Retorna un diccionario {id_pedido: texto_pedido}.
    """
    query = "SELECT id, pedido FROM pedidos WHERE estado = %s"
    params = (int(EstadoPedido.PENDIENTE),)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            resultados = cursor.fetchall()

    return {int(order_id): str(pedido_data) for order_id, pedido_data in resultados}


def completar_pedido(order_id: int) -> bool:
    """
    Marca un pedido como COMPLETADO si estaba PENDIENTE.
    Retorna True si se actualizó alguna fila, False en caso contrario.
    """
    query = "UPDATE pedidos SET estado = %s WHERE id = %s AND estado = %s"
    params = (
        int(EstadoPedido.COMPLETADO),
        order_id,
        int(EstadoPedido.PENDIENTE),
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            filas_afectadas = cursor.rowcount
            logging.info(
                f"Pedido ID: {order_id} marcado como completado en DB. "
                f"Filas afectadas: {filas_afectadas}"
            )
            return filas_afectadas > 0
