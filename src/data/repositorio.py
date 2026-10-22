"""Repositorio MySQL transaccional para el catálogo y los pedidos estructurados."""

from __future__ import annotations

import logging
from typing import Iterable

from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from data.db import get_connection
from domain.modelos import (
    Catalogo,
    EstadoPedido,
    Item,
    Modificador,
    Pedido,
    Plato,
    ReglasProducto,
    TipoModificador,
    TipoServicio,
    catalogo_por_defecto,
)


class ErrorRepositorio(Exception):
    """Error base de la capa de persistencia."""


class PedidoNoEncontradoError(ErrorRepositorio):
    """Se lanza cuando se intenta cargar o editar un pedido que no existe en BD."""


class ErrorConcurrenciaPedido(ErrorRepositorio):
    """Se lanza cuando la versión del pedido en BD cambió antes de guardar una edición."""


def _asegurar_catalogo_inicial(cursor: MySQLCursor) -> None:
    """
    Si la tabla `productos` está vacía, inserta el catálogo inicial automáticamente
    para garantizar que el sistema siempre tenga datos base coherentes.
    """
    cursor.execute("SELECT COUNT(*) FROM productos")
    fila = cursor.fetchone()
    if fila and int(fila[0]) > 0:
        return

    logging.info("Catálogo vacío en BD; poblando productos, ingredientes y reglas iniciales...")
    catalogo_base = catalogo_por_defecto()

    cursor.executemany(
        "INSERT IGNORE INTO productos (nombre, activo) VALUES (%s, 1)",
        [(nombre,) for nombre in catalogo_base.nombres_productos],
    )

    guisos = (
        "Chicharron",
        "Papas",
        "Huevo rojo",
        "Huevo verde",
        "Nopales",
        "Aldilla",
        "Rajas",
        "Chorizo",
    )
    complementos = ("Queso", "Crema", "Cebolla", "Verdura")

    cursor.executemany(
        "INSERT IGNORE INTO ingredientes (nombre, es_guiso, activo) VALUES (%s, 1, 1)",
        [(g,) for g in guisos],
    )
    cursor.executemany(
        "INSERT IGNORE INTO ingredientes (nombre, es_guiso, activo) VALUES (%s, 0, 1)",
        [(c,) for c in complementos],
    )

    cursor.execute("SELECT id, nombre FROM productos")
    mapa_prod = {str(nombre): int(pid) for pid, nombre in cursor.fetchall()}

    cursor.execute("SELECT id, nombre FROM ingredientes")
    mapa_ing = {str(nombre): int(iid) for iid, nombre in cursor.fetchall()}

    reglas_filas: list[tuple[int, int, str]] = []
    for nombre_prod, reglas in catalogo_base.productos.items():
        pid = mapa_prod[nombre_prod]
        for ing in reglas.guisos_base:
            reglas_filas.append((pid, mapa_ing[ing], "BASE"))
        for ing in reglas.extras_permitidos:
            reglas_filas.append((pid, mapa_ing[ing], "EXTRA"))
        for ing in reglas.sin_permitidos:
            reglas_filas.append((pid, mapa_ing[ing], "SIN"))

    cursor.executemany(
        "INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo) VALUES (%s, %s, %s)",
        reglas_filas,
    )


def cargar_catalogo() -> Catalogo:
    """Lee de MySQL los productos, ingredientes y reglas activas y devuelve un objeto `Catalogo`."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_catalogo_inicial(cursor)
            conn.commit()

            cursor.execute(
                """
                SELECT p.nombre, pi.tipo, i.nombre
                FROM producto_ingrediente pi
                JOIN productos p ON p.id = pi.producto_id
                JOIN ingredientes i ON i.id = pi.ingrediente_id
                WHERE p.activo = 1 AND i.activo = 1
                ORDER BY p.id ASC, i.id ASC
                """
            )
            filas = cursor.fetchall()

    if not filas:
        return catalogo_por_defecto()

    agrupado: dict[str, dict[str, list[str]]] = {}
    for nombre_prod, tipo_regla, nombre_ing in filas:
        prod_str = str(nombre_prod)
        tipo_str = str(tipo_regla)
        ing_str = str(nombre_ing)
        if prod_str not in agrupado:
            agrupado[prod_str] = {"BASE": [], "EXTRA": [], "SIN": []}
        agrupado[prod_str][tipo_str].append(ing_str)

    productos_reglas: dict[str, ReglasProducto] = {}
    for nombre_prod, listas in agrupado.items():
        productos_reglas[nombre_prod] = ReglasProducto(
            nombre=nombre_prod,
            guisos_base=tuple(listas["BASE"]),
            extras_permitidos=tuple(listas["EXTRA"]),
            sin_permitidos=tuple(listas["SIN"]),
        )

    return Catalogo(productos=productos_reglas)


def _obtener_mapas_catalogo_ids(cursor: MySQLCursor) -> tuple[dict[str, int], dict[str, int]]:
    """Devuelve diccionarios `{nombre_producto: id}` y `{nombre_ingrediente: id}`."""
    _asegurar_catalogo_inicial(cursor)

    cursor.execute("SELECT id, nombre FROM productos")
    mapa_productos = {str(nombre): int(pid) for pid, nombre in cursor.fetchall()}

    cursor.execute("SELECT id, nombre FROM ingredientes")
    mapa_ingredientes = {str(nombre): int(iid) for iid, nombre in cursor.fetchall()}

    return mapa_productos, mapa_ingredientes


def _insertar_platos_items_modificadores(
    cursor: MySQLCursor,
    pedido_id: int,
    platos: list[Plato],
    mapa_productos: dict[str, int],
    mapa_ingredientes: dict[str, int],
) -> None:
    """Inserta los platos, sus items y modificadores dentro de la transacción activa."""
    for plato in platos:
        cursor.execute(
            "INSERT INTO platos (pedido_id, numero) VALUES (%s, %s)",
            (pedido_id, plato.numero),
        )
        plato_id = int(cursor.lastrowid)

        for item in plato.items:
            if item.producto not in mapa_productos:
                raise ErrorRepositorio(f"Producto desconocido en BD: '{item.producto}'")
            if item.guiso not in mapa_ingredientes:
                raise ErrorRepositorio(f"Guiso desconocido en BD: '{item.guiso}'")

            producto_id = mapa_productos[item.producto]
            guiso_id = mapa_ingredientes[item.guiso]

            cursor.execute(
                """
                INSERT INTO items (plato_id, producto_id, guiso_id, cantidad, nota)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (plato_id, producto_id, guiso_id, item.cantidad, item.nota),
            )
            item_id = int(cursor.lastrowid)

            if item.modificadores:
                mod_filas: list[tuple[int, int, str]] = []
                for mod in item.modificadores:
                    if mod.ingrediente not in mapa_ingredientes:
                        raise ErrorRepositorio(
                            f"Ingrediente de modificador desconocido en BD: '{mod.ingrediente}'"
                        )
                    mod_filas.append(
                        (item_id, mapa_ingredientes[mod.ingrediente], mod.tipo.value)
                    )
                cursor.executemany(
                    """
                    INSERT INTO item_modificadores (item_id, ingrediente_id, tipo)
                    VALUES (%s, %s, %s)
                    """,
                    mod_filas,
                )


def guardar_pedido(pedido: Pedido, catalogo: Catalogo | None = None) -> Pedido:
    """
    Valida y guarda un nuevo pedido completo (cabecera, platos, items y modificadores)
    en una única transacción. Retorna el `Pedido` persistido con su `id` y timestamps.
    """
    pedido.preparar_para_guardar(catalogo)
    assert pedido.tipo_servicio is not None

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                mapa_productos, mapa_ingredientes = _obtener_mapas_catalogo_ids(cursor)

                cursor.execute(
                    """
                    INSERT INTO pedidos (tipo_servicio, estado, version)
                    VALUES (%s, %s, 1)
                    """,
                    (pedido.tipo_servicio.value, EstadoPedido.PENDIENTE.value),
                )
                nuevo_id = int(cursor.lastrowid)

                _insertar_platos_items_modificadores(
                    cursor=cursor,
                    pedido_id=nuevo_id,
                    platos=pedido.platos,
                    mapa_productos=mapa_productos,
                    mapa_ingredientes=mapa_ingredientes,
                )

            conn.commit()
            logging.info(f"Pedido #{nuevo_id} guardado exitosamente en BD.")
        except Exception:
            conn.rollback()
            raise

    return cargar_pedido(nuevo_id)


def _hidratar_pedidos_desde_cabeceras(
    conn: MySQLConnection,
    filas_pedidos: list[tuple],
) -> list[Pedido]:
    """
    Dado un conjunto de cabeceras de `pedidos`, carga en bloque todos sus platos,
    items y modificadores en solo 3 consultas SQL y devuelve la lista de `Pedido`.
    """
    if not filas_pedidos:
        return []

    pedidos_por_id: dict[int, Pedido] = {}
    orden_ids: list[int] = []

    for pid, tipo_servicio, estado, version, created_at, updated_at, completed_at in filas_pedidos:
        pedido_id = int(pid)
        orden_ids.append(pedido_id)
        pedido_obj = Pedido(
            id=pedido_id,
            tipo_servicio=TipoServicio(str(tipo_servicio)),
            estado=EstadoPedido(str(estado)),
            version=int(version),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        pedido_obj.platos.clear()
        pedidos_por_id[pedido_id] = pedido_obj

    placeholders_pedidos = ", ".join(["%s"] * len(orden_ids))

    with conn.cursor() as cursor:
        # 1. Cargar todos los platos de estos pedidos
        cursor.execute(
            f"""
            SELECT id, pedido_id, numero
            FROM platos
            WHERE pedido_id IN ({placeholders_pedidos})
            ORDER BY pedido_id ASC, numero ASC
            """,
            tuple(orden_ids),
        )
        filas_platos = cursor.fetchall()

        platos_por_id: dict[int, Plato] = {}
        plato_ids: list[int] = []
        for plato_id_raw, pedido_id_raw, numero_raw in filas_platos:
            plato_id = int(plato_id_raw)
            pedido_id = int(pedido_id_raw)
            plato = Plato(numero=int(numero_raw), items=[])
            platos_por_id[plato_id] = plato
            plato_ids.append(plato_id)
            pedidos_por_id[pedido_id].platos.append(plato)

        if not plato_ids:
            for ped in pedidos_por_id.values():
                if not ped.platos:
                    ped.platos = [Plato(numero=1)]
            return [pedidos_por_id[pid] for pid in orden_ids]

        # 2. Cargar todos los items de esos platos
        placeholders_platos = ", ".join(["%s"] * len(plato_ids))
        cursor.execute(
            f"""
            SELECT it.id, it.plato_id, p.nombre, ing.nombre, it.cantidad, it.nota
            FROM items it
            JOIN productos p ON p.id = it.producto_id
            JOIN ingredientes ing ON ing.id = it.guiso_id
            WHERE it.plato_id IN ({placeholders_platos})
            ORDER BY it.id ASC
            """,
            tuple(plato_ids),
        )
        filas_items = cursor.fetchall()

        items_por_id: dict[int, tuple[int, str, str, int, str, list[Modificador]]] = {}
        item_ids: list[int] = []
        for item_id_raw, plato_id_raw, prod_nombre, guiso_nombre, cantidad_raw, nota_raw in filas_items:
            item_id = int(item_id_raw)
            item_ids.append(item_id)
            items_por_id[item_id] = (
                int(plato_id_raw),
                str(prod_nombre),
                str(guiso_nombre),
                int(cantidad_raw),
                str(nota_raw or ""),
                [],
            )

        # 3. Cargar todos los modificadores de esos items
        if item_ids:
            placeholders_items = ", ".join(["%s"] * len(item_ids))
            cursor.execute(
                f"""
                SELECT im.item_id, im.tipo, ing.nombre
                FROM item_modificadores im
                JOIN ingredientes ing ON ing.id = im.ingrediente_id
                WHERE im.item_id IN ({placeholders_items})
                ORDER BY im.item_id ASC, ing.nombre ASC
                """,
                tuple(item_ids),
            )
            for item_id_raw, tipo_raw, ing_nombre in cursor.fetchall():
                iid = int(item_id_raw)
                items_por_id[iid][5].append(
                    Modificador(
                        tipo=TipoModificador(str(tipo_raw)),
                        ingrediente=str(ing_nombre),
                    )
                )

        # Ensamblar cada Item dentro de su Plato correspondiente
        for item_id in item_ids:
            plato_id, prod_nombre, guiso_nombre, cantidad, nota, mods = items_por_id[item_id]
            platos_por_id[plato_id].items.append(
                Item(
                    producto=prod_nombre,
                    guiso=guiso_nombre,
                    cantidad=cantidad,
                    modificadores=mods,
                    nota=nota,
                )
            )

    for ped in pedidos_por_id.values():
        if not ped.platos:
            ped.platos = [Plato(numero=1)]

    return [pedidos_por_id[pid] for pid in orden_ids]


def cargar_pedido(pedido_id: int) -> Pedido:
    """Carga un pedido completo por su ID o lanza `PedidoNoEncontradoError` si no existe."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at
                FROM pedidos
                WHERE id = %s
                """,
                (pedido_id,),
            )
            fila = cursor.fetchone()

        if fila is None:
            raise PedidoNoEncontradoError(f"No se encontró el pedido #{pedido_id}.")

        pedidos = _hidratar_pedidos_desde_cabeceras(conn, [fila])
        return pedidos[0]


def actualizar_pedido(
    pedido: Pedido,
    version_esperada: int | None = None,
    catalogo: Catalogo | None = None,
) -> Pedido:
    """
    Actualiza un pedido existente en una transacción aplicando control de concurrencia
    por `version` (bloqueo optimista).
    Si el pedido estaba `COMPLETADO`, regresa a `PENDIENTE` para que cocina vea el cambio.
    """
    if pedido.id is None:
        raise ErrorRepositorio("No se puede actualizar un pedido que no tiene ID.")

    version_check = version_esperada if version_esperada is not None else pedido.version
    pedido.preparar_para_guardar(catalogo)
    assert pedido.tipo_servicio is not None

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                mapa_productos, mapa_ingredientes = _obtener_mapas_catalogo_ids(cursor)

                cursor.execute(
                    """
                    UPDATE pedidos
                    SET tipo_servicio = %s,
                        estado = %s,
                        completed_at = NULL,
                        version = version + 1
                    WHERE id = %s AND version = %s
                    """,
                    (
                        pedido.tipo_servicio.value,
                        EstadoPedido.PENDIENTE.value,
                        pedido.id,
                        version_check,
                    ),
                )

                if cursor.rowcount == 0:
                    cursor.execute("SELECT version FROM pedidos WHERE id = %s", (pedido.id,))
                    existe = cursor.fetchone()
                    if existe is None:
                        raise PedidoNoEncontradoError(
                            f"El pedido #{pedido.id} no existe en la base de datos."
                        )
                    raise ErrorConcurrenciaPedido(
                        f"El pedido #{pedido.id} ya fue modificado por otra persona "
                        f"(versión actual en BD: {existe[0]}, versión esperada: {version_check})."
                    )

                # Reemplazar platos, items y modificadores dentro de la misma transacción
                cursor.execute("DELETE FROM platos WHERE pedido_id = %s", (pedido.id,))

                _insertar_platos_items_modificadores(
                    cursor=cursor,
                    pedido_id=pedido.id,
                    platos=pedido.platos,
                    mapa_productos=mapa_productos,
                    mapa_ingredientes=mapa_ingredientes,
                )

            conn.commit()
            logging.info(f"Pedido #{pedido.id} actualizado exitosamente (nueva versión).")
        except Exception:
            conn.rollback()
            raise

    return cargar_pedido(pedido.id)


def obtener_pedidos_pendientes() -> list[Pedido]:
    """Devuelve todos los pedidos en estado `PENDIENTE` ordenados por antigüedad."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at
                FROM pedidos
                WHERE estado = %s
                ORDER BY created_at ASC, id ASC
                """,
                (EstadoPedido.PENDIENTE.value,),
            )
            filas = cursor.fetchall()

        return _hidratar_pedidos_desde_cabeceras(conn, filas)


def obtener_pedidos_completados_hoy(limite: int = 30) -> list[Pedido]:
    """
    Devuelve los pedidos `COMPLETADO` del día actual (o los más recientes hasta `limite`),
    ordenados del más reciente al más antiguo.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at
                FROM pedidos
                WHERE estado = %s
                  AND (DATE(completed_at) = CURDATE() OR DATE(created_at) = CURDATE())
                ORDER BY completed_at DESC, id DESC
                LIMIT %s
                """,
                (EstadoPedido.COMPLETADO.value, limite),
            )
            filas = cursor.fetchall()

        return _hidratar_pedidos_desde_cabeceras(conn, filas)


def marcar_pedido_completado(pedido_id: int) -> bool:
    """Marca un pedido como `COMPLETADO` registrando `completed_at`. Retorna True si se actualizó."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE pedidos
                SET estado = %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s AND estado = %s
                """,
                (
                    EstadoPedido.COMPLETADO.value,
                    pedido_id,
                    EstadoPedido.PENDIENTE.value,
                ),
            )
            conn.commit()
            actualizado = cursor.rowcount > 0
            if actualizado:
                logging.info(f"Pedido #{pedido_id} marcado como COMPLETADO.")
            return actualizado


def eliminar_pedido(pedido_id: int) -> bool:
    """Elimina un pedido y todo su contenido en cascada. Útil para pruebas o limpieza."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
            conn.commit()
            return cursor.rowcount > 0
