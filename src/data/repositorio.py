"""Repositorio MySQL transaccional para el catálogo y los pedidos estructurados."""

from __future__ import annotations

import logging
from typing import Iterable

from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from data.db import get_connection
from domain.modelos import (
    PRECIOS_POR_DEFECTO,
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


_COLUMNA_PRIORIDAD_VERIFICADA = False


def _asegurar_columna_orden_prioridad(cursor: MySQLCursor) -> None:
    """
    Verifica una vez por ejecución que la tabla `pedidos` tenga las columnas
    `orden_prioridad` y `solo_en_cocina`. Si aún no existen en la BD actual,
    las agrega automáticamente sin perder datos.
    """
    global _COLUMNA_PRIORIDAD_VERIFICADA
    if _COLUMNA_PRIORIDAD_VERIFICADA:
        return

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'orden_prioridad'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `orden_prioridad` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN orden_prioridad INT NOT NULL DEFAULT 0 AFTER estado"
        )
        cursor.execute("UPDATE pedidos SET orden_prioridad = id WHERE orden_prioridad = 0")

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'solo_en_cocina'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `solo_en_cocina` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN solo_en_cocina TINYINT(1) NOT NULL DEFAULT 0 AFTER orden_prioridad"
        )

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'nombre_cliente'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `nombre_cliente` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN nombre_cliente VARCHAR(100) NOT NULL DEFAULT '' AFTER id"
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jornadas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            estado ENUM('ABIERTA', 'CERRADA') NOT NULL DEFAULT 'ABIERTA',
            iniciada_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cerrada_at TIMESTAMP NULL DEFAULT NULL,
            total_pedidos INT NOT NULL DEFAULT 0,
            total_platillos INT NOT NULL DEFAULT 0,
            INDEX idx_jornadas_estado (estado, iniciada_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'jornada_id'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `jornada_id` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN jornada_id INT NULL DEFAULT NULL AFTER id"
        )

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'numero_orden_dia'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `numero_orden_dia` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN numero_orden_dia INT NOT NULL DEFAULT 0 AFTER jornada_id"
        )
        # Poblar numero_orden_dia en pedidos existentes por jornada en orden de llegada (id ASC)
        cursor.execute("SELECT id, COALESCE(jornada_id, 0) FROM pedidos ORDER BY id ASC")
        filas_existentes = cursor.fetchall()
        conteo_por_jornada: dict[int, int] = {}
        actualizaciones_orden: list[tuple[int, int]] = []
        for pid_raw, jid_raw in filas_existentes:
            jid = int(jid_raw or 0)
            conteo_por_jornada[jid] = conteo_por_jornada.get(jid, 0) + 1
            actualizaciones_orden.append((conteo_por_jornada[jid], int(pid_raw)))
        if actualizaciones_orden:
            cursor.executemany(
                "UPDATE pedidos SET numero_orden_dia = %s WHERE id = %s",
                actualizaciones_orden,
            )

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'total_cobrado'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `total_cobrado` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN total_cobrado DECIMAL(10,2) NOT NULL DEFAULT 0.00 AFTER solo_en_cocina"
        )

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'pago_cliente'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `pago_cliente` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN pago_cliente DECIMAL(10,2) NOT NULL DEFAULT 0.00 AFTER total_cobrado"
        )

    cursor.execute("SHOW COLUMNS FROM pedidos LIKE 'cambio_entregado'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `cambio_entregado` a la tabla `pedidos`...")
        cursor.execute(
            "ALTER TABLE pedidos ADD COLUMN cambio_entregado DECIMAL(10,2) NOT NULL DEFAULT 0.00 AFTER pago_cliente"
        )

    cursor.execute("SHOW COLUMNS FROM jornadas LIKE 'total_ventas'")
    if cursor.fetchone() is None:
        logging.info("Agregando columna `total_ventas` a la tabla `jornadas`...")
        cursor.execute(
            "ALTER TABLE jornadas ADD COLUMN total_ventas DECIMAL(10,2) NOT NULL DEFAULT 0.00 AFTER total_platillos"
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS precios_menu (
            clave VARCHAR(50) PRIMARY KEY,
            precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    cursor.executemany(
        "INSERT IGNORE INTO precios_menu (clave, precio) VALUES (%s, %s)",
        [(clave, float(valor)) for clave, valor in PRECIOS_POR_DEFECTO.items()],
    )

    _COLUMNA_PRIORIDAD_VERIFICADA = True


def _obtener_precios_menu_cursor(cursor: MySQLCursor) -> dict[str, float]:
    """Lee el diccionario de precios actuales desde MySQL usando el cursor activo."""
    _asegurar_columna_orden_prioridad(cursor)
    cursor.execute("SELECT clave, precio FROM precios_menu")
    precios = dict(PRECIOS_POR_DEFECTO)
    for clave_raw, precio_raw in cursor.fetchall():
        precios[str(clave_raw)] = float(precio_raw)
    return precios


def obtener_precios_menu() -> dict[str, float]:
    """Devuelve el diccionario de precios vigentes del menú (`GORDITA`, `SOPE_FRIJOLES`, `SOPE_GUISO`, `QUESADILLA`)."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            precios = _obtener_precios_menu_cursor(cursor)
            conn.commit()
            return precios


def actualizar_precios_menu(nuevos_precios: dict[str, float]) -> dict[str, float]:
    """Actualiza los precios del menú en MySQL y devuelve el diccionario actualizado."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                _asegurar_columna_orden_prioridad(cursor)
                filas: list[tuple[str, float]] = []
                for clave in PRECIOS_POR_DEFECTO:
                    if clave in nuevos_precios:
                        valor = float(nuevos_precios[clave])
                        if valor < 0:
                            raise ErrorRepositorio("El precio no puede ser negativo.")
                        filas.append((clave, round(valor, 2)))
                if filas:
                    cursor.executemany(
                        """
                        INSERT INTO precios_menu (clave, precio)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE precio = VALUES(precio)
                        """,
                        filas,
                    )
                precios_actualizados = _obtener_precios_menu_cursor(cursor)
            conn.commit()
            logging.info(f"Precios del menú actualizados: {precios_actualizados}")
            return precios_actualizados
        except Exception:
            conn.rollback()
            raise


def _asegurar_catalogo_inicial(cursor: MySQLCursor) -> None:
    """
    Si la tabla `productos` está vacía, inserta el catálogo inicial automáticamente.
    Además, si ya existían `Gordita` y `Sope` pero aún no existe `Quesadilla` o el guiso
    `Frijoles`, los agrega y vincula sus reglas automáticamente.
    """
    cursor.execute("SELECT COUNT(*) FROM productos")
    fila = cursor.fetchone()
    if fila and int(fila[0]) > 0:
        cursor.execute("SELECT id FROM ingredientes WHERE nombre = 'Frijoles'")
        if cursor.fetchone() is None:
            logging.info("Agregando guiso 'Frijoles' al catálogo en BD...")
            cursor.execute(
                "INSERT IGNORE INTO ingredientes (nombre, es_guiso, activo) VALUES ('Frijoles', 1, 1)"
            )
            cursor.execute("SELECT id FROM ingredientes WHERE nombre = 'Frijoles'")
            fila_f = cursor.fetchone()
            if fila_f:
                fid = int(fila_f[0])
                cursor.execute("SELECT id FROM productos WHERE activo = 1")
                reglas_f: list[tuple[int, int, str]] = []
                for (pid_raw,) in cursor.fetchall():
                    pid = int(pid_raw)
                    reglas_f.append((pid, fid, "BASE"))
                    reglas_f.append((pid, fid, "EXTRA"))
                if reglas_f:
                    cursor.executemany(
                        "INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo) VALUES (%s, %s, %s)",
                        reglas_f,
                    )

        cursor.execute("SELECT id FROM productos WHERE nombre = 'Quesadilla'")
        if cursor.fetchone() is None:
            logging.info("Agregando producto 'Quesadilla' y sus reglas al catálogo en BD...")
            cursor.execute("INSERT IGNORE INTO productos (nombre, activo) VALUES ('Quesadilla', 1)")
            cursor.execute("SELECT id FROM productos WHERE nombre = 'Quesadilla'")
            fila_q = cursor.fetchone()
            if fila_q:
                qid = int(fila_q[0])
                cursor.execute("SELECT id, nombre, es_guiso FROM ingredientes WHERE activo = 1")
                reglas_q: list[tuple[int, int, str]] = []
                for iid_raw, ing_nom_raw, es_guiso_raw in cursor.fetchall():
                    iid = int(iid_raw)
                    ing_nom = str(ing_nom_raw)
                    es_guiso = bool(es_guiso_raw)
                    if es_guiso:
                        reglas_q.append((qid, iid, "BASE"))
                        reglas_q.append((qid, iid, "EXTRA"))
                    else:
                        if ing_nom in ("Queso", "Crema"):
                            reglas_q.append((qid, iid, "EXTRA"))
                        reglas_q.append((qid, iid, "SIN"))
                if reglas_q:
                    cursor.executemany(
                        "INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo) VALUES (%s, %s, %s)",
                        reglas_q,
                    )
        return

    logging.info("Catálogo vacío en BD; poblando productos, ingredientes y reglas iniciales...")
    catalogo_base = catalogo_por_defecto()

    cursor.executemany(
        "INSERT IGNORE INTO productos (nombre, activo) VALUES (%s, 1)",
        [(nombre,) for nombre in catalogo_base.nombres_productos],
    )

    guisos = (
        "Frijoles",
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


def agregar_ingrediente_catalogo(
    nombre: str,
    es_guiso: bool = True,
    permitir_sin: bool = False,
) -> str:
    """
    Agrega un nuevo ingrediente (guiso principal o complemento) al catálogo en MySQL
    y lo vincula automáticamente con los productos activos (`Gordita`, `Sope`, etc.).
    Retorna el nombre limpio del ingrediente guardado.
    """
    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio:
        raise ErrorRepositorio("Escribe el nombre del ingrediente.")

    # Capitalizar primera letra manteniendo el resto (ej. "huevo con jamon" -> "Huevo con jamon")
    nombre_limpio = nombre_limpio[0].upper() + nombre_limpio[1:]

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                _asegurar_catalogo_inicial(cursor)

                cursor.execute(
                    """
                    INSERT INTO ingredientes (nombre, es_guiso, activo)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE es_guiso = VALUES(es_guiso), activo = 1
                    """,
                    (nombre_limpio, 1 if es_guiso else 0),
                )

                cursor.execute(
                    "SELECT id FROM ingredientes WHERE nombre = %s",
                    (nombre_limpio,),
                )
                fila_ing = cursor.fetchone()
                if not fila_ing:
                    raise ErrorRepositorio("No se pudo obtener el ID del ingrediente creado.")
                ingrediente_id = int(fila_ing[0])

                cursor.execute("SELECT id, nombre FROM productos WHERE activo = 1")
                productos_activos = cursor.fetchall()

                reglas_nuevas: list[tuple[int, int, str]] = []
                for prod_id_raw, prod_nombre_raw in productos_activos:
                    pid = int(prod_id_raw)
                    pnombre = str(prod_nombre_raw)
                    if es_guiso:
                        reglas_nuevas.append((pid, ingrediente_id, "BASE"))
                        reglas_nuevas.append((pid, ingrediente_id, "EXTRA"))
                    else:
                        reglas_nuevas.append((pid, ingrediente_id, "EXTRA"))
                        if permitir_sin or pnombre.lower() == "sope":
                            reglas_nuevas.append((pid, ingrediente_id, "SIN"))

                if reglas_nuevas:
                    cursor.executemany(
                        """
                        INSERT IGNORE INTO producto_ingrediente (producto_id, ingrediente_id, tipo)
                        VALUES (%s, %s, %s)
                        """,
                        reglas_nuevas,
                    )

            conn.commit()
            logging.info(
                f"Ingrediente '{nombre_limpio}' ({'guiso' if es_guiso else 'complemento'}) agregado al catálogo."
            )
            return nombre_limpio
        except Exception:
            conn.rollback()
            raise


def desactivar_ingrediente_catalogo(nombre: str) -> None:
    """Desactiva un ingrediente del catálogo para que ya no aparezca al tomar pedidos nuevos."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE ingredientes SET activo = 0 WHERE nombre = %s",
                    ((nombre or "").strip(),),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


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
                _asegurar_columna_orden_prioridad(cursor)
                mapa_productos, mapa_ingredientes = _obtener_mapas_catalogo_ids(cursor)
                precios_actuales = _obtener_precios_menu_cursor(cursor)
                total_calculado = pedido.calcular_total(precios_actuales)

                cursor.execute(
                    "SELECT id FROM jornadas WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1"
                )
                fila_jornada = cursor.fetchone()
                jornada_activa_id = int(fila_jornada[0]) if fila_jornada else None

                if jornada_activa_id is not None:
                    cursor.execute(
                        "SELECT COALESCE(MAX(numero_orden_dia), COUNT(*)) + 1 FROM pedidos WHERE jornada_id = %s",
                        (jornada_activa_id,),
                    )
                else:
                    cursor.execute(
                        "SELECT COUNT(*) + 1 FROM pedidos WHERE DATE(created_at) = CURDATE()"
                    )
                fila_num_dia = cursor.fetchone()
                siguiente_num_dia = int(fila_num_dia[0]) if fila_num_dia else 1

                cursor.execute(
                    "SELECT COALESCE(MAX(orden_prioridad), 0) + 1 FROM pedidos WHERE estado = %s",
                    (EstadoPedido.PENDIENTE.value,),
                )
                fila_max = cursor.fetchone()
                siguiente_prioridad = int(fila_max[0]) if fila_max else 1

                cursor.execute(
                    """
                    INSERT INTO pedidos (jornada_id, numero_orden_dia, nombre_cliente, tipo_servicio, estado, orden_prioridad, total_cobrado, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        jornada_activa_id,
                        siguiente_num_dia,
                        pedido.nombre_cliente.strip(),
                        pedido.tipo_servicio.value,
                        EstadoPedido.PENDIENTE.value,
                        siguiente_prioridad,
                        total_calculado,
                    ),
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

    for fila in filas_pedidos:
        pid, tipo_servicio, estado, version, created_at, updated_at, completed_at = fila[:7]
        solo_en_cocina = bool(fila[7]) if len(fila) > 7 else False
        nombre_cliente = str(fila[8] or "") if len(fila) > 8 else ""
        total_cobrado = float(fila[9] or 0.0) if len(fila) > 9 else 0.0
        pago_cliente = float(fila[10] or 0.0) if len(fila) > 10 else 0.0
        cambio_entregado = float(fila[11] or 0.0) if len(fila) > 11 else 0.0
        numero_orden_dia = int(fila[12] or 0) if len(fila) > 12 else 0
        pedido_id = int(pid)
        orden_ids.append(pedido_id)
        pedido_obj = Pedido(
            id=pedido_id,
            numero_orden_dia=numero_orden_dia if numero_orden_dia > 0 else pedido_id,
            nombre_cliente=nombre_cliente,
            tipo_servicio=TipoServicio(str(tipo_servicio)),
            estado=EstadoPedido(str(estado)),
            version=int(version),
            solo_en_cocina=solo_en_cocina,
            total_cobrado=total_cobrado,
            pago_cliente=pago_cliente,
            cambio_entregado=cambio_entregado,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        pedido_obj.platos.clear()
        pedidos_por_id[pedido_id] = pedido_obj

    placeholders_pedidos = ", ".join(["%s"] * len(orden_ids))

    with conn.cursor() as cursor:
        precios_actuales = _obtener_precios_menu_cursor(cursor)

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
        if ped.total_cobrado <= 0 or ped.estado == EstadoPedido.PENDIENTE:
            ped.total_cobrado = ped.calcular_total(precios_actuales)

    return [pedidos_por_id[pid] for pid in orden_ids]


def cargar_pedido(pedido_id: int) -> Pedido:
    """Carga un pedido completo por su ID o lanza `PedidoNoEncontradoError` si no existe."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_columna_orden_prioridad(cursor)
            conn.commit()
            cursor.execute(
                """
                SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at, solo_en_cocina, nombre_cliente, total_cobrado, pago_cliente, cambio_entregado, numero_orden_dia
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
                _asegurar_columna_orden_prioridad(cursor)
                mapa_productos, mapa_ingredientes = _obtener_mapas_catalogo_ids(cursor)
                precios_actuales = _obtener_precios_menu_cursor(cursor)
                total_calculado = pedido.calcular_total(precios_actuales)

                cursor.execute(
                    """
                    UPDATE pedidos
                    SET nombre_cliente = %s,
                        tipo_servicio = %s,
                        estado = %s,
                        total_cobrado = %s,
                        completed_at = NULL,
                        version = version + 1
                    WHERE id = %s AND version = %s
                    """,
                    (
                        pedido.nombre_cliente.strip(),
                        pedido.tipo_servicio.value,
                        EstadoPedido.PENDIENTE.value,
                        total_calculado,
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


def obtener_pedidos_pendientes(solo_jornada_activa: bool = False) -> list[Pedido]:
    """
    Devuelve todos los pedidos en estado `PENDIENTE` ordenados según la posición
    definida por el mesero (`orden_prioridad`).
    Si `solo_jornada_activa=True`, devuelve únicamente los pedidos de la jornada (día) abierta.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_columna_orden_prioridad(cursor)
            conn.commit()

            if solo_jornada_activa:
                cursor.execute(
                    "SELECT id FROM jornadas WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1"
                )
                fila_j = cursor.fetchone()
                if not fila_j:
                    return []
                jornada_id = int(fila_j[0])
                cursor.execute(
                    """
                    SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at, solo_en_cocina, nombre_cliente, total_cobrado, pago_cliente, cambio_entregado, numero_orden_dia
                    FROM pedidos
                    WHERE estado = %s AND jornada_id = %s
                    ORDER BY CASE WHEN orden_prioridad > 0 THEN orden_prioridad ELSE id END ASC,
                             created_at ASC,
                             id ASC
                    """,
                    (EstadoPedido.PENDIENTE.value, jornada_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at, solo_en_cocina, nombre_cliente, total_cobrado, pago_cliente, cambio_entregado, numero_orden_dia
                    FROM pedidos
                    WHERE estado = %s
                    ORDER BY CASE WHEN orden_prioridad > 0 THEN orden_prioridad ELSE id END ASC,
                             created_at ASC,
                             id ASC
                    """,
                    (EstadoPedido.PENDIENTE.value,),
                )
            filas = cursor.fetchall()

        return _hidratar_pedidos_desde_cabeceras(conn, filas)


def actualizar_modo_pantalla_pedido(pedido_id: int, solo_en_cocina: bool) -> None:
    """
    Permite al mesero elegir si un pedido debe ocupar toda la pantalla de cocina (1 solo)
    o permitir hasta 2 a la par si es pequeño.
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                _asegurar_columna_orden_prioridad(cursor)
                cursor.execute(
                    "UPDATE pedidos SET solo_en_cocina = %s WHERE id = %s",
                    (1 if solo_en_cocina else 0, int(pedido_id)),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def actualizar_orden_pedidos(ids_en_orden: list[int]) -> None:
    """
    Actualiza en una transacción la posición (`orden_prioridad`) de los pedidos
    pendientes según el orden en que fueron arrastrados por el mesero.
    """
    if not ids_en_orden:
        return

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                _asegurar_columna_orden_prioridad(cursor)
                pares = [(posicion, int(pid)) for posicion, pid in enumerate(ids_en_orden, start=1)]
                cursor.executemany(
                    "UPDATE pedidos SET orden_prioridad = %s WHERE id = %s",
                    pares,
                )
            conn.commit()
            logging.info(f"Nuevo orden de prioridad guardado para pedidos: {ids_en_orden}")
        except Exception:
            conn.rollback()
            raise


def obtener_pedidos_completados_hoy(
    limite: int = 30,
    solo_jornada_activa: bool = False,
) -> list[Pedido]:
    """
    Devuelve los pedidos `COMPLETADO` del día actual (o de la jornada abierta si `solo_jornada_activa=True`),
    ordenados del más reciente al más antiguo.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_columna_orden_prioridad(cursor)
            conn.commit()
            if solo_jornada_activa:
                cursor.execute(
                    "SELECT id FROM jornadas WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1"
                )
                fila_j = cursor.fetchone()
                if not fila_j:
                    return []
                jornada_id = int(fila_j[0])
                cursor.execute(
                    """
                    SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at, solo_en_cocina, nombre_cliente, total_cobrado, pago_cliente, cambio_entregado, numero_orden_dia
                    FROM pedidos
                    WHERE estado = %s AND jornada_id = %s
                    ORDER BY completed_at DESC, id DESC
                    LIMIT %s
                    """,
                    (EstadoPedido.COMPLETADO.value, jornada_id, limite),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at, solo_en_cocina, nombre_cliente, total_cobrado, pago_cliente, cambio_entregado, numero_orden_dia
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


def marcar_pedido_completado(
    pedido_id: int,
    total_cobrado: float | None = None,
    pago_cliente: float = 0.0,
    cambio_entregado: float = 0.0,
) -> bool:
    """
    Marca un pedido como `COMPLETADO` registrando `completed_at`, el total cobrado,
    el dinero recibido del cliente y el cambio entregado. Retorna True si se actualizó.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_columna_orden_prioridad(cursor)
            if total_cobrado is not None:
                cursor.execute(
                    """
                    UPDATE pedidos
                    SET estado = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        total_cobrado = %s,
                        pago_cliente = %s,
                        cambio_entregado = %s
                    WHERE id = %s AND estado = %s
                    """,
                    (
                        EstadoPedido.COMPLETADO.value,
                        round(float(total_cobrado), 2),
                        round(float(pago_cliente), 2),
                        round(float(cambio_entregado), 2),
                        pedido_id,
                        EstadoPedido.PENDIENTE.value,
                    ),
                )
            else:
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


# -----------------------------------------------------------------------------
# Gestión de Jornada / Corte del Día ("Iniciar Día" y "Finalizar Día")
# -----------------------------------------------------------------------------


def obtener_jornada_activa() -> dict | None:
    """
    Devuelve la información de la jornada (día) actualmente ABIERTA, o `None` si el día
    no se ha iniciado o ya se cerró.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_columna_orden_prioridad(cursor)
            conn.commit()
            cursor.execute(
                """
                SELECT id, estado, iniciada_at, cerrada_at
                FROM jornadas
                WHERE estado = 'ABIERTA'
                ORDER BY id DESC
                LIMIT 1
                """
            )
            fila = cursor.fetchone()
            if not fila:
                return None

            jornada_id = int(fila[0])
            iniciada_at = fila[2]

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN estado = 'COMPLETADO' THEN 1 ELSE 0 END),
                    COALESCE(SUM(total_cobrado), 0),
                    COALESCE(SUM(CASE WHEN estado = 'COMPLETADO' THEN total_cobrado ELSE 0 END), 0)
                FROM pedidos
                WHERE jornada_id = %s
                """,
                (jornada_id,),
            )
            conteos = cursor.fetchone()
            total_pedidos = int(conteos[0] or 0) if conteos else 0
            pendientes_count = int(conteos[1] or 0) if conteos else 0
            completados_count = int(conteos[2] or 0) if conteos else 0
            total_ventas = float(conteos[3] or 0.0) if conteos else 0.0
            ventas_cobradas = float(conteos[4] or 0.0) if conteos else 0.0

            cursor.execute(
                """
                SELECT COALESCE(SUM(it.cantidad), 0)
                FROM items it
                JOIN platos pl ON pl.id = it.plato_id
                JOIN pedidos pe ON pe.id = pl.pedido_id
                WHERE pe.jornada_id = %s
                """,
                (jornada_id,),
            )
            fila_pzs = cursor.fetchone()
            total_platillos = int(fila_pzs[0] or 0) if fila_pzs else 0

            return {
                "id": jornada_id,
                "estado": str(fila[1]),
                "iniciada_at": iniciada_at,
                "cerrada_at": fila[3],
                "total_pedidos": total_pedidos,
                "pendientes": pendientes_count,
                "completados": completados_count,
                "total_platillos": total_platillos,
                "total_ventas": total_ventas,
                "ventas_cobradas": ventas_cobradas,
            }


def iniciar_jornada_dia() -> dict:
    """
    Inicia un nuevo día (jornada ABIERTA). Si ya hay una jornada abierta, la devuelve.
    Además, vincula cualquier pedido pendiente huérfano (`jornada_id IS NULL`) del día
    de hoy a esta nueva jornada.
    """
    existente = obtener_jornada_activa()
    if existente is not None:
        return existente

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                _asegurar_columna_orden_prioridad(cursor)
                cursor.execute("INSERT INTO jornadas (estado) VALUES ('ABIERTA')")
                nueva_id = int(cursor.lastrowid)

                # Si había pedidos pendientes sin jornada asignada, asociarlos al día que inicia
                cursor.execute(
                    """
                    SELECT id FROM pedidos
                    WHERE jornada_id IS NULL AND estado = 'PENDIENTE'
                    ORDER BY id ASC
                    """
                )
                huerfanos = [int(r[0]) for r in cursor.fetchall()]
                for idx_h, pid_h in enumerate(huerfanos, start=1):
                    cursor.execute(
                        "UPDATE pedidos SET jornada_id = %s, numero_orden_dia = %s WHERE id = %s",
                        (nueva_id, idx_h, pid_h),
                    )
            conn.commit()
            logging.info(f"Jornada del día #{nueva_id} iniciada.")
        except Exception:
            conn.rollback()
            raise

    return obtener_jornada_activa() or {"id": nueva_id, "estado": "ABIERTA"}


def obtener_resumen_jornada_actual() -> dict:
    """
    Calcula el desglose completo de la jornada activa para la sección de Corte del Día:
    - Totales de pedidos (pendientes, completados, mesa, para llevar)
    - Totales de ventas en pesos (total_ventas, ventas_cobradas, ventas_pendientes)
    - Totales de piezas por producto (Gorditas, Sopes, Quesadillas)
    - Totales de piezas por guiso
    - Lista completa de pedidos del día
    """
    jornada = obtener_jornada_activa()
    precios = obtener_precios_menu()
    if jornada is None:
        return {
            "activa": False,
            "jornada": None,
            "total_pedidos": 0,
            "pendientes": 0,
            "completados": 0,
            "mesa": 0,
            "llevar": 0,
            "total_platillos": 0,
            "total_ventas": 0.0,
            "ventas_cobradas": 0.0,
            "ventas_pendientes": 0.0,
            "por_producto": {},
            "por_guiso": {},
            "pedidos": [],
            "precios": precios,
        }

    jornada_id = int(jornada["id"])
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tipo_servicio, estado, version, created_at, updated_at, completed_at, solo_en_cocina, nombre_cliente, total_cobrado, pago_cliente, cambio_entregado, numero_orden_dia
                FROM pedidos
                WHERE jornada_id = %s
                ORDER BY id DESC
                """,
                (jornada_id,),
            )
            filas = cursor.fetchall()

        pedidos_dia = _hidratar_pedidos_desde_cabeceras(conn, filas)

    mesa_count = sum(1 for p in pedidos_dia if p.tipo_servicio == TipoServicio.MESA)
    llevar_count = sum(1 for p in pedidos_dia if p.tipo_servicio == TipoServicio.LLEVAR)
    pendientes_count = sum(1 for p in pedidos_dia if p.estado == EstadoPedido.PENDIENTE)
    completados_count = sum(1 for p in pedidos_dia if p.estado == EstadoPedido.COMPLETADO)

    por_producto: dict[str, int] = {}
    por_guiso: dict[str, int] = {}
    total_platillos = 0
    total_ventas = 0.0
    ventas_cobradas = 0.0
    ventas_pendientes = 0.0

    for ped in pedidos_dia:
        monto_ped = ped.total_cobrado if ped.total_cobrado > 0 else ped.calcular_total(precios)
        ped.total_cobrado = monto_ped
        total_ventas += monto_ped
        if ped.estado == EstadoPedido.COMPLETADO:
            ventas_cobradas += monto_ped
        else:
            ventas_pendientes += monto_ped

        for plato in ped.platos:
            for item in plato.items:
                total_platillos += item.cantidad
                por_producto[item.producto] = por_producto.get(item.producto, 0) + item.cantidad
                por_guiso[item.guiso] = por_guiso.get(item.guiso, 0) + item.cantidad

    # Ordenar guisos de mayor a menor venta
    por_guiso_ordenado = dict(
        sorted(por_guiso.items(), key=lambda par: (-par[1], par[0]))
    )

    return {
        "activa": True,
        "jornada": jornada,
        "total_pedidos": len(pedidos_dia),
        "pendientes": pendientes_count,
        "completados": completados_count,
        "mesa": mesa_count,
        "llevar": llevar_count,
        "total_platillos": total_platillos,
        "total_ventas": round(total_ventas, 2),
        "ventas_cobradas": round(ventas_cobradas, 2),
        "ventas_pendientes": round(ventas_pendientes, 2),
        "por_producto": por_producto,
        "por_guiso": por_guiso_ordenado,
        "pedidos": pedidos_dia,
        "precios": precios,
    }


def finalizar_jornada_dia() -> dict:
    """
    Finaliza el día actual (cierra la jornada ABIERTA), marca como completados
    los pedidos pendientes que quedaran abiertos, guarda el resumen del corte en BD
    y devuelve el diccionario con el reporte completo del Corte del Día.
    """
    resumen = obtener_resumen_jornada_actual()
    if not resumen["activa"] or not resumen["jornada"]:
        raise ErrorRepositorio("No hay un día activo para finalizar.")

    jornada_id = int(resumen["jornada"]["id"])
    total_pedidos = int(resumen["total_pedidos"])
    total_platillos = int(resumen["total_platillos"])
    total_ventas = float(resumen["total_ventas"])

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                # Asegurar que cada pedido de la jornada tenga su total_cobrado guardado
                for ped in resumen["pedidos"]:
                    if ped.id is not None and ped.total_cobrado > 0:
                        cursor.execute(
                            "UPDATE pedidos SET total_cobrado = %s WHERE id = %s AND total_cobrado <= 0",
                            (round(float(ped.total_cobrado), 2), int(ped.id)),
                        )

                cursor.execute(
                    """
                    UPDATE pedidos
                    SET estado = 'COMPLETADO',
                        completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                    WHERE jornada_id = %s AND estado = 'PENDIENTE'
                    """,
                    (jornada_id,),
                )
                cursor.execute(
                    """
                    UPDATE jornadas
                    SET estado = 'CERRADA',
                        cerrada_at = CURRENT_TIMESTAMP,
                        total_pedidos = %s,
                        total_platillos = %s,
                        total_ventas = %s
                    WHERE id = %s
                    """,
                    (total_pedidos, total_platillos, round(total_ventas, 2), jornada_id),
                )
            conn.commit()
            logging.info(
                f"Jornada #{jornada_id} finalizada (Corte: {total_pedidos} pedidos, {total_platillos} platillos, ${total_ventas:.2f})."
            )
        except Exception:
            conn.rollback()
            raise

    return resumen


def obtener_historial_cortes(limite: int = 10) -> list[dict]:
    """Devuelve la lista de jornadas cerradas (cortes anteriores) más recientes."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _asegurar_columna_orden_prioridad(cursor)
            conn.commit()
            cursor.execute(
                """
                SELECT id, iniciada_at, cerrada_at, total_pedidos, total_platillos, total_ventas
                FROM jornadas
                WHERE estado = 'CERRADA'
                ORDER BY id DESC
                LIMIT %s
                """,
                (limite,),
            )
            filas = cursor.fetchall()

    return [
        {
            "id": int(f[0]),
            "iniciada_at": f[1],
            "cerrada_at": f[2],
            "total_pedidos": int(f[3] or 0),
            "total_platillos": int(f[4] or 0),
            "total_ventas": float(f[5] or 0.0) if len(f) > 5 else 0.0,
        }
        for f in filas
    ]
