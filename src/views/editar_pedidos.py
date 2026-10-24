"""Vista para meseros (`/editar-pedidos`): editar pedidos y reordenar su prioridad arrastrándolos."""

from __future__ import annotations

import logging

import flet as ft

from data.repositorio import (
    actualizar_modo_pantalla_pedido,
    actualizar_orden_pedidos,
    actualizar_precios_menu,
    agregar_ingrediente_catalogo,
    cargar_catalogo,
    cargar_pedido,
    desactivar_ingrediente_catalogo,
    marcar_pedido_completado,
    obtener_pedidos_completados_hoy,
    obtener_pedidos_pendientes,
    obtener_precios_menu,
)
from domain.modelos import (
    PRECIOS_POR_DEFECTO,
    Pedido,
    formatear_moneda,
    seleccionar_pedidos_visibles_cocina,
)
from ui.components import (
    abrir_modal_cobro_pedido,
    crear_navegacion,
    crear_tarjeta_pedido_mesero,
)
from ui.theme import COLOR_FONDO_PAGINA, colors, icons


def view_editar_pedidos(page: ft.Page) -> ft.View:
    """
    Construye la pantalla exclusiva para que el mesero:
    1. Reordene qué pedidos salen primero y cuáles después arrastrando las tarjetas
       (o con las flechas de posición), reflejándose en vivo en Cocina.
    2. Consulte y edite cualquier pedido ('En orden' o 'Completados').
    """
    estado = {
        "tab_activa": "PENDIENTES",  # "PENDIENTES" | "COMPLETADOS"
        "pendientes": [],
        "completados": [],
        "precios": dict(PRECIOS_POR_DEFECTO),
    }

    fila_filtros = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    instruccion_arrastre = ft.Container()
    lista_tarjetas = ft.ResponsiveRow(spacing=12, run_spacing=12)

    def cargar_datos_bd() -> None:
        try:
            estado["precios"] = obtener_precios_menu()
            estado["pendientes"] = obtener_pedidos_pendientes(solo_jornada_activa=True)
            estado["completados"] = obtener_pedidos_completados_hoy(solo_jornada_activa=True)
        except Exception as err:
            logging.error(f"Error al cargar pedidos en vista de edición: {err}")

    def cambiar_tab(nueva_tab: str) -> None:
        estado["tab_activa"] = nueva_tab
        renderizar()
        page.update()

    def recargar_manual(_e: ft.ControlEvent) -> None:
        cargar_datos_bd()
        renderizar()
        page.update()

    def abrir_edicion(pedido_id: int) -> None:
        page.go(f"/pedido/{pedido_id}")

    def persistir_nuevo_orden(lista_pendientes: list[Pedido]) -> None:
        ids_ordenados = [int(p.id) for p in lista_pendientes if p.id is not None]
        try:
            actualizar_orden_pedidos(ids_ordenados)
        except Exception as err:
            logging.error(f"Error al guardar el nuevo orden de pedidos: {err}")

    def mover_un_paso(pedido_id: int, delta: int) -> None:
        """Mueve un pedido una posición antes (`delta=-1`) o después (`delta=+1`)."""
        pendientes: list[Pedido] = list(estado["pendientes"])
        idx_actual = next((i for i, p in enumerate(pendientes) if p.id == pedido_id), None)
        if idx_actual is None:
            return

        nuevo_idx = idx_actual + delta
        if not (0 <= nuevo_idx < len(pendientes)):
            return

        pendientes[idx_actual], pendientes[nuevo_idx] = (
            pendientes[nuevo_idx],
            pendientes[idx_actual],
        )
        estado["pendientes"] = pendientes
        persistir_nuevo_orden(pendientes)
        renderizar()
        page.update()

    def mostrar_pedido_en_cocina(pedido_id: int) -> None:
        """
         Sube el pedido elegido por el mesero al frente de la cola para que se muestre
        inmediatamente en la tablet de Cocina:
        - Si es grande (3-4 platos o modo 1 solo), se verá únicamente ese pedido.
        - Si es pequeño y el que estaba primero también es pequeño, se verán los 2 a la par.
        """
        pendientes: list[Pedido] = list(estado["pendientes"])
        idx_actual = next((i for i, p in enumerate(pendientes) if p.id == pedido_id), None)
        if idx_actual is None or idx_actual == 0:
            return

        pedido_elegido = pendientes.pop(idx_actual)
        pendientes.insert(0, pedido_elegido)

        estado["pendientes"] = pendientes
        persistir_nuevo_orden(pendientes)
        renderizar()
        page.update()

    def alternar_solo_en_cocina(pedido_id: int, nuevo_valor: bool) -> None:
        """Cambia entre mostrar un pedido solo en toda la pantalla de cocina o hasta 2 a la par."""
        try:
            actualizar_modo_pantalla_pedido(pedido_id, nuevo_valor)
            for ped in estado["pendientes"]:
                if ped.id == pedido_id:
                    ped.solo_en_cocina = nuevo_valor
                    break
        except Exception as err:
            logging.error(f"Error al actualizar modo de pantalla del pedido #{pedido_id}: {err}")
        renderizar()
        page.update()

    def mostrar_aviso_edicion(mensaje: str, es_error: bool = False) -> None:
        snack = ft.SnackBar(
            content=ft.Text(
                mensaje,
                color=colors.WHITE,
                weight=ft.FontWeight.BOLD,
                size=14,
            ),
            bgcolor=colors.RED_700 if es_error else colors.GREEN_700,
            duration=2600,
        )
        try:
            page.open(snack)
        except Exception:
            page.snack_bar = snack
            snack.open = True
            page.update()

    def completar_pedido_desde_edicion(pedido_id: int) -> None:
        """Abre el modal de cobro desde Editar Pedidos y marca el pedido como completado."""
        pedido_actual = next((p for p in estado["pendientes"] if p.id == pedido_id), None)
        if pedido_actual is None:
            try:
                pedido_actual = cargar_pedido(pedido_id)
            except Exception as err:
                mostrar_aviso_edicion(f"No se pudo cargar el pedido: {err}", es_error=True)
                return

        precios_actuales = dict(estado["precios"])

        def ejecutar_cobro(total_cobrado: float, pago_cliente: float, cambio_entregado: float) -> None:
            try:
                marcar_pedido_completado(
                    pedido_id=pedido_id,
                    total_cobrado=total_cobrado,
                    pago_cliente=pago_cliente,
                    cambio_entregado=cambio_entregado,
                )
                cargar_datos_bd()
                renderizar()
                mostrar_aviso_edicion(
                    f"Pedido de {pedido_actual.nombre_mostrar} cobrado y marcado como listo"
                )
                page.update()
            except Exception as err:
                logging.error(f"Error al completar pedido #{pedido_id} desde Editar Pedidos: {err}")
                mostrar_aviso_edicion(f"Error al cobrar pedido: {err}", es_error=True)

        abrir_modal_cobro_pedido(
            page=page,
            pedido=pedido_actual,
            precios=precios_actuales,
            on_confirmar=ejecutar_cobro,
        )

    def renderizar() -> None:
        tab_activa = str(estado["tab_activa"])
        pendientes: list[Pedido] = estado["pendientes"]
        completados: list[Pedido] = estado["completados"]
        es_pendientes = tab_activa == "PENDIENTES"

        fila_filtros.controls = [
            ft.Container(
                expand=True,
                height=42,
                bgcolor=colors.ORANGE_700 if es_pendientes else colors.WHITE,
                border=ft.border.all(
                    2,
                    colors.ORANGE_800 if es_pendientes else colors.BLUE_GREY_200,
                ),
                border_radius=10,
                alignment=ft.alignment.center,
                ink=True,
                on_click=lambda _e: cambiar_tab("PENDIENTES"),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Icon(
                            icons.LOCAL_FIRE_DEPARTMENT,
                            size=17,
                            color=colors.WHITE if es_pendientes else colors.ORANGE_700,
                        ),
                        ft.Text(
                            f"En orden ({len(pendientes)})",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.WHITE if es_pendientes else colors.BLACK87,
                        ),
                    ],
                ),
            ),
            ft.Container(
                expand=True,
                height=42,
                bgcolor=colors.GREEN_700 if not es_pendientes else colors.WHITE,
                border=ft.border.all(
                    2,
                    colors.GREEN_800 if not es_pendientes else colors.BLUE_GREY_200,
                ),
                border_radius=10,
                alignment=ft.alignment.center,
                ink=True,
                on_click=lambda _e: cambiar_tab("COMPLETADOS"),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Icon(
                            icons.CHECK_CIRCLE_OUTLINE,
                            size=17,
                            color=colors.WHITE if not es_pendientes else colors.GREEN_700,
                        ),
                        ft.Text(
                            f"Completados ({len(completados)})",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.WHITE if not es_pendientes else colors.BLACK87,
                        ),
                    ],
                ),
            ),
        ]

        visibles_cocina = seleccionar_pedidos_visibles_cocina(pendientes)
        ids_visibles_cocina = {int(p.id) for p in visibles_cocina if p.id is not None}

        instruccion_arrastre.visible = es_pendientes and len(pendientes) > 0
        texto_en_pantalla = (
            ", ".join(
                f"{p.numero_pedido_mostrar}° {p.nombre_mostrar}"
                for p in visibles_cocina
            )
            if visibles_cocina
            else "Ninguno"
        )
        modo_pantalla_desc = (
            "1 pedido ocupando toda la pantalla"
            if len(visibles_cocina) == 1
            else f"{len(visibles_cocina)} pedidos chicos a la par"
        )
        instruccion_arrastre.content = ft.Container(
            bgcolor=colors.GREEN_50,
            border=ft.border.all(1.5, colors.GREEN_400),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(icons.TV, size=18, color=colors.GREEN_800),
                            ft.Text(
                                f"Viendo ahora en Cocina: {texto_en_pantalla} ({modo_pantalla_desc})",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=colors.GREEN_900,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Text(
                        "Toca 'Mostrar en Cocina' o usa las flechas para elegir cuáles se ven en la tablet.",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=colors.BLUE_GREY_800,
                    ),
                ],
            ),
        )

        pedidos_mostrar = pendientes if es_pendientes else completados

        if not pedidos_mostrar:
            texto_vacio = (
                "No hay pedidos activos en este momento."
                if es_pendientes
                else "No hay pedidos completados hoy."
            )
            lista_tarjetas.controls = [
                ft.Container(
                    col={"xs": 12},
                    padding=ft.padding.symmetric(vertical=45, horizontal=20),
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        texto_vacio,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLACK54,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]
            return

        total_cola = len(pendientes)
        precios_actuales = dict(estado["precios"])
        lista_tarjetas.controls = [
            crear_tarjeta_pedido_mesero(
                page=page,
                pedido=ped,
                on_editar=abrir_edicion,
                posicion_cola=idx if es_pendientes else None,
                total_en_cola=total_cola if es_pendientes else 0,
                on_mover_paso=mover_un_paso if es_pendientes else None,
                en_pantalla_cocina=(int(ped.id or 0) in ids_visibles_cocina) if es_pendientes else False,
                on_mostrar_en_cocina=mostrar_pedido_en_cocina if es_pendientes else None,
                on_alternar_solo_en_cocina=alternar_solo_en_cocina if es_pendientes else None,
                on_completar=completar_pedido_desde_edicion if es_pendientes else None,
                precios=precios_actuales,
            )
            for idx, ped in enumerate(pedidos_mostrar, start=1)
        ]

    cargar_datos_bd()
    renderizar()

    def abrir_modal_ingredientes(_e: ft.ControlEvent) -> None:
        """Abre un diálogo para agregar nuevos guisos o ingredientes al catálogo."""
        estado_modal = {"es_guiso": True}

        input_nombre_ing = ft.TextField(
            label="Nombre del ingrediente o guiso",
            hint_text="Ej: Picadillo, Deshebrada, Frijoles...",
            prefix_icon=icons.RESTAURANT_MENU,
            autofocus=True,
            bgcolor=colors.WHITE,
            border_radius=10,
            border_color=colors.ORANGE_700,
            focused_border_color=colors.DEEP_ORANGE_700,
            text_size=15,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )

        fila_tipo_ing = ft.Row(spacing=8)
        contenedor_lista_actual = ft.Column(spacing=6)

        def renderizar_selector_tipo() -> None:
            es_guiso = bool(estado_modal["es_guiso"])
            opciones = [
                (True, "Guiso principal", icons.LUNCH_DINING, colors.ORANGE_700),
                (False, "Extra / Complemento", icons.ADD_CIRCLE_OUTLINE, colors.BLUE_700),
            ]
            controles_tipo: list[ft.Control] = []
            for valor_bool, etiqueta, icono, color_act in opciones:
                activo = es_guiso == valor_bool
                controles_tipo.append(
                    ft.Container(
                        expand=True,
                        height=40,
                        bgcolor=color_act if activo else colors.WHITE,
                        border=ft.border.all(
                            1.5,
                            color_act if activo else colors.BLUE_GREY_200,
                        ),
                        border_radius=8,
                        alignment=ft.alignment.center,
                        ink=True,
                        on_click=lambda _ev, v=valor_bool: cambiar_tipo_ing(v),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=5,
                            controls=[
                                ft.Icon(
                                    icono,
                                    size=16,
                                    color=colors.WHITE if activo else colors.BLACK87,
                                ),
                                ft.Text(
                                    etiqueta,
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.WHITE if activo else colors.BLACK87,
                                ),
                            ],
                        ),
                    )
                )
            fila_tipo_ing.controls = controles_tipo

        def cambiar_tipo_ing(nuevo_es_guiso: bool) -> None:
            estado_modal["es_guiso"] = nuevo_es_guiso
            renderizar_selector_tipo()
            page.update()

        def quitar_ingrediente_existente(nombre_ing: str) -> None:
            try:
                desactivar_ingrediente_catalogo(nombre_ing)
                cargar_lista_ingredientes_actuales()
                mostrar_aviso_edicion(f"Ingrediente '{nombre_ing}' quitado del menú")
                page.update()
            except Exception as err:
                mostrar_aviso_edicion(f"Error al quitar ingrediente: {err}", es_error=True)

        def cargar_lista_ingredientes_actuales() -> None:
            try:
                cat = cargar_catalogo()
                guisos_set: list[str] = []
                extras_set: list[str] = []
                for prod in cat.productos.values():
                    for g in prod.guisos_base:
                        if g not in guisos_set:
                            guisos_set.append(g)
                    for ex in prod.extras_permitidos:
                        if ex not in guisos_set and ex not in extras_set:
                            extras_set.append(ex)
                    for s in prod.sin_permitidos:
                        if s not in guisos_set and s not in extras_set:
                            extras_set.append(s)

                chips_guisos = [
                    ft.Container(
                        bgcolor=colors.ORANGE_50,
                        border=ft.border.all(1, colors.ORANGE_300),
                        border_radius=14,
                        padding=ft.padding.only(left=10, right=4, top=3, bottom=3),
                        content=ft.Row(
                            spacing=4,
                            tight=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    nombre_g,
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.DEEP_ORANGE_900,
                                ),
                                ft.IconButton(
                                    icon=icons.CLOSE,
                                    icon_size=13,
                                    icon_color=colors.RED_700,
                                    width=22,
                                    height=22,
                                    padding=0,
                                    tooltip=f"Quitar {nombre_g}",
                                    on_click=lambda _ev, n=nombre_g: quitar_ingrediente_existente(n),
                                ),
                            ],
                        ),
                    )
                    for nombre_g in guisos_set
                ]

                chips_extras = [
                    ft.Container(
                        bgcolor=colors.BLUE_50,
                        border=ft.border.all(1, colors.BLUE_300),
                        border_radius=14,
                        padding=ft.padding.only(left=10, right=4, top=3, bottom=3),
                        content=ft.Row(
                            spacing=4,
                            tight=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    nombre_e,
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.BLUE_900,
                                ),
                                ft.IconButton(
                                    icon=icons.CLOSE,
                                    icon_size=13,
                                    icon_color=colors.RED_700,
                                    width=22,
                                    height=22,
                                    padding=0,
                                    tooltip=f"Quitar {nombre_e}",
                                    on_click=lambda _ev, n=nombre_e: quitar_ingrediente_existente(n),
                                ),
                            ],
                        ),
                    )
                    for nombre_e in extras_set
                ]

                contenedor_lista_actual.controls = [
                    ft.Text(
                        "Guisos activos (toca ✕ para quitar):",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLUE_GREY_800,
                    ),
                    ft.Row(wrap=True, spacing=6, run_spacing=6, controls=chips_guisos),
                    ft.Text(
                        "Complementos / Extras activos:",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLUE_GREY_800,
                    ),
                    ft.Row(wrap=True, spacing=6, run_spacing=6, controls=chips_extras),
                ]
            except Exception as err:
                contenedor_lista_actual.controls = [
                    ft.Text(f"No se pudo cargar el catálogo: {err}", size=12, color=colors.RED_700)
                ]

        def limpiar_err_ing(_ev: ft.ControlEvent) -> None:
            if input_nombre_ing.error_text:
                input_nombre_ing.error_text = None
                page.update()

        input_nombre_ing.on_change = limpiar_err_ing

        def guardar_nuevo_ingrediente(_ev: ft.ControlEvent) -> None:
            nombre_raw = (input_nombre_ing.value or "").strip()
            if not nombre_raw:
                input_nombre_ing.error_text = "Escribe el nombre del ingrediente"
                page.update()
                return

            try:
                es_guiso = bool(estado_modal["es_guiso"])
                guardado = agregar_ingrediente_catalogo(
                    nombre=nombre_raw,
                    es_guiso=es_guiso,
                    permitir_sin=not es_guiso,
                )
                input_nombre_ing.value = ""
                cargar_lista_ingredientes_actuales()
                mostrar_aviso_edicion(
                    f"'{guardado}' agregado como {'guiso' if es_guiso else 'complemento'}"
                )
                page.update()
            except Exception as err:
                input_nombre_ing.error_text = str(err)
                page.update()

        input_nombre_ing.on_submit = guardar_nuevo_ingrediente
        renderizar_selector_tipo()
        cargar_lista_ingredientes_actuales()

        dialogo_ing = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(icons.RESTAURANT_MENU, color=colors.ORANGE_700, size=22),
                    ft.Text("Agregar Ingredientes", weight=ft.FontWeight.BOLD, size=18),
                ],
            ),
            content=ft.Container(
                width=330,
                content=ft.Column(
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                    controls=[
                        fila_tipo_ing,
                        input_nombre_ing,
                        ft.ElevatedButton(
                            text="+ Agregar al menú",
                            bgcolor=colors.GREEN_700,
                            color=colors.WHITE,
                            height=40,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                            on_click=guardar_nuevo_ingrediente,
                        ),
                        ft.Divider(height=8, color=colors.BLUE_GREY_100),
                        contenedor_lista_actual,
                    ],
                ),
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda _ev: page.close(dialogo_ing),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo_ing)

    def abrir_modal_precios(_e: ft.ControlEvent) -> None:
        """Abre un diálogo para editar los precios de Gorditas, Sopes (frijoles y otro guiso) y Quesadillas."""
        try:
            precios_actuales = obtener_precios_menu()
        except Exception:
            precios_actuales = dict(estado["precios"])

        def _fmt_input(valor: float) -> str:
            return str(int(valor)) if valor == int(valor) else f"{valor:.2f}"

        campo_gordita = ft.TextField(
            label="Gordita ($)",
            value=_fmt_input(precios_actuales.get("GORDITA", 17.0)),
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            text_size=16,
        )
        campo_sope_frijoles = ft.TextField(
            label="Sope de Frijoles ($)",
            value=_fmt_input(precios_actuales.get("SOPE_FRIJOLES", 30.0)),
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            text_size=16,
        )
        campo_sope_guiso = ft.TextField(
            label="Sope de cualquier otro guiso ($)",
            value=_fmt_input(precios_actuales.get("SOPE_GUISO", 35.0)),
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            text_size=16,
        )
        campo_quesadilla = ft.TextField(
            label="Quesadilla ($)",
            value=_fmt_input(precios_actuales.get("QUESADILLA", 45.0)),
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            text_size=16,
        )

        texto_err_precios = ft.Text(
            "",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=colors.RED_700,
            visible=False,
        )

        def cerrar_precios(_ev: ft.ControlEvent | None = None) -> None:
            dialogo_precios.open = False
            page.update()

        def guardar_precios_accion(_ev: ft.ControlEvent | None = None) -> None:
            texto_err_precios.visible = False
            try:
                nuevos = {
                    "GORDITA": float((campo_gordita.value or "").strip()),
                    "SOPE_FRIJOLES": float((campo_sope_frijoles.value or "").strip()),
                    "SOPE_GUISO": float((campo_sope_guiso.value or "").strip()),
                    "QUESADILLA": float((campo_quesadilla.value or "").strip()),
                }
                if any(v <= 0 for v in nuevos.values()):
                    raise ValueError("Todos los precios deben ser mayores a 0.")
            except ValueError:
                texto_err_precios.value = "Ingresa precios válidos en números mayores a 0."
                texto_err_precios.visible = True
                page.update()
                return

            try:
                estado["precios"] = actualizar_precios_menu(nuevos)
                cargar_datos_bd()
                renderizar()
                dialogo_precios.open = False
                mostrar_aviso_edicion(
                    f"Precios actualizados: Gordita {formatear_moneda(nuevos['GORDITA'])}, "
                    f"Sope Frijoles {formatear_moneda(nuevos['SOPE_FRIJOLES'])}, "
                    f"Sope Guiso {formatear_moneda(nuevos['SOPE_GUISO'])}, "
                    f"Quesadilla {formatear_moneda(nuevos['QUESADILLA'])}"
                )
                page.update()
            except Exception as err:
                texto_err_precios.value = f"Error al guardar precios: {err}"
                texto_err_precios.visible = True
                page.update()

        dialogo_precios = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(icons.ATTACH_MONEY, color=colors.GREEN_700, size=24),
                    ft.Text("Editar Precios del Menú", weight=ft.FontWeight.BOLD, size=18),
                ],
            ),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text(
                            "Ajusta los precios unitarios en pesos. El total de los pedidos se calculará automáticamente:",
                            size=12,
                            color=colors.BLUE_GREY_700,
                        ),
                        campo_gordita,
                        campo_sope_frijoles,
                        campo_sope_guiso,
                        campo_quesadilla,
                        texto_err_precios,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_precios),
                ft.ElevatedButton(
                    text="Guardar Precios",
                    icon=icons.SAVE,
                    bgcolor=colors.GREEN_700,
                    color=colors.WHITE,
                    height=40,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=guardar_precios_accion,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialogo_precios)
        dialogo_precios.open = True
        page.update()

    encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Text(
                "Editar Pedidos",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            ft.Row(
                spacing=6,
                tight=True,
                wrap=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.ElevatedButton(
                        text="Editar Precios",
                        icon=icons.ATTACH_MONEY,
                        bgcolor=colors.GREEN_700,
                        color=colors.WHITE,
                        height=36,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        ),
                        on_click=abrir_modal_precios,
                    ),
                    ft.ElevatedButton(
                        text="+ Ingredientes",
                        icon=icons.RESTAURANT_MENU,
                        bgcolor=colors.BLUE_GREY_800,
                        color=colors.WHITE,
                        height=36,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        ),
                        on_click=abrir_modal_ingredientes,
                    ),
                    ft.IconButton(
                        icon=icons.REFRESH,
                        icon_color=colors.BLUE_GREY_700,
                        tooltip="Actualizar lista",
                        on_click=recargar_manual,
                    ),
                ],
            ),
        ],
    )

    navegacion = crear_navegacion(page, selected_index=2)

    return ft.View(
        route="/editar-pedidos",
        controls=[
            encabezado,
            fila_filtros,
            instruccion_arrastre,
            lista_tarjetas,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=14,
        bgcolor=COLOR_FONDO_PAGINA,
    )
