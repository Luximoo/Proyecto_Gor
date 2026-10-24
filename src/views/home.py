"""Vista exclusiva para Cocina (`/home`): visualización limpia de pedidos pendientes."""

from __future__ import annotations

import logging
import threading

import flet as ft
import mysql.connector

from config import ERROR_RETRY_SECONDS, POLL_INTERVAL_SECONDS
from data.repositorio import (
    cargar_pedido,
    iniciar_jornada_dia,
    marcar_pedido_completado,
    obtener_jornada_activa,
    obtener_pedidos_pendientes,
    obtener_precios_menu,
)
from domain.modelos import (
    PRECIOS_POR_DEFECTO,
    Pedido,
    formatear_moneda,
    seleccionar_pedidos_visibles_cocina,
)
from ui.components import crear_navegacion, crear_tarjeta_pedido_cocina
from ui.theme import COLOR_FONDO_PAGINA, colors, icons
from views.corte import mostrar_dialogo_confirmar_corte

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def view_home(page: ft.Page) -> ft.View:
    """
    Construye el monitor limpio de cocina (`/home`):
    - Muestra únicamente los pedidos pendientes por preparar.
    - Sin botones de edición ni pestañas extra para no distraer a los cocineros.
    - Letra grande y clara para leer de un vistazo mientras cocinan.
    """
    evento_anterior: threading.Event | None = getattr(page, "_home_stop_event", None)
    if evento_anterior is not None:
        evento_anterior.set()

    stop_event = threading.Event()
    setattr(page, "_home_stop_event", stop_event)

    ui_lock = threading.Lock()
    estado_cocina = {
        "jornada": None,
        "pendientes": [],
        "precios": dict(PRECIOS_POR_DEFECTO),
        "huella_pendientes": (),
    }

    titulo_contador = ft.Text(
        "Pedidos en Cocina",
        size=22,
        weight=ft.FontWeight.BOLD,
        color=colors.BLACK87,
    )
    insignia_pedidos_dia = ft.Container(visible=False)
    insignia_espera = ft.Container(visible=False)
    boton_accion_dia = ft.Container(visible=False)

    barra_superior = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Row(
                spacing=10,
                wrap=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[titulo_contador, insignia_pedidos_dia, insignia_espera],
            ),
            boton_accion_dia,
        ],
    )
    lista_tarjetas = ft.ResponsiveRow(spacing=12, run_spacing=12)

    def _calcular_huella(
        jornada: dict | None,
        pedidos: list[Pedido],
        precios: dict[str, float],
    ) -> tuple:
        jid = int(jornada["id"]) if jornada else 0
        tot_dia = int(jornada.get("total_pedidos", 0)) if jornada else 0
        comp_dia = int(jornada.get("completados", 0)) if jornada else 0
        pzs_dia = int(jornada.get("total_platillos", 0)) if jornada else 0
        ventas_dia = float(jornada.get("total_ventas", 0.0)) if jornada else 0.0
        tupla_precios = tuple(sorted((k, round(float(v), 2)) for k, v in precios.items()))
        tupla_pedidos = tuple(
            (int(p.id or 0), int(p.version), bool(p.solo_en_cocina), p.nombre_cliente)
            for p in pedidos
        )
        return (jid, tot_dia, comp_dia, pzs_dia, ventas_dia, tupla_precios, tupla_pedidos)

    def _accion_iniciar_dia_cocina(_e: ft.ControlEvent) -> None:
        try:
            iniciar_jornada_dia()
            _sincronizar_desde_bd(forzar_render=True)
            if page:
                page.update()
        except Exception as err:
            logging.error(f"Error al iniciar el día desde cocina: {err}")

    def _accion_finalizar_dia_cocina(_e: ft.ControlEvent) -> None:
        def post_corte() -> None:
            _sincronizar_desde_bd(forzar_render=True)
            if page:
                page.update()

        mostrar_dialogo_confirmar_corte(page, on_corte_realizado=post_corte)

    def _ejecutar_completado_pedido(
        pedido_id: int,
        total_cobrado: float,
        pago_cliente: float,
        cambio_entregado: float,
    ) -> None:
        """Marca el pedido como listo con los datos de cobro y actualiza la pantalla de cocina."""
        logging.info(
            f"Completando pedido #{pedido_id} desde cocina (Total: ${total_cobrado:.2f}, Pago: ${pago_cliente:.2f}, Cambio: ${cambio_entregado:.2f})..."
        )
        try:
            marcar_pedido_completado(
                pedido_id=pedido_id,
                total_cobrado=total_cobrado,
                pago_cliente=pago_cliente,
                cambio_entregado=cambio_entregado,
            )
            precios = obtener_precios_menu()
            jornada = obtener_jornada_activa()
            pendientes = (
                obtener_pedidos_pendientes(solo_jornada_activa=True)
                if jornada is not None
                else []
            )
            with ui_lock:
                estado_cocina["precios"] = precios
                estado_cocina["jornada"] = jornada
                estado_cocina["pendientes"] = pendientes
                estado_cocina["huella_pendientes"] = _calcular_huella(jornada, pendientes, precios)
                _renderizar_en_lock()
            if page:
                page.update()
        except mysql.connector.Error as err:
            logging.error(f"Error de base de datos al completar pedido #{pedido_id}: {err}")
        except Exception as err:
            logging.error(f"Error inesperado al completar pedido #{pedido_id}: {err}")

    def _completar_pedido_accion(pedido_id: int) -> None:
        """
        Al presionar 'Listo' en cocina, abre el modal con el Total a cobrar, permite
        ingresar con cuánto paga el cliente y calcula automáticamente el cambio a regresar.
        """
        pedido_actual: Pedido | None = None
        with ui_lock:
            precios_actuales = dict(estado_cocina["precios"])
            for p in estado_cocina["pendientes"]:
                if p.id == pedido_id:
                    pedido_actual = p
                    break

        if pedido_actual is None:
            try:
                pedido_actual = cargar_pedido(pedido_id)
            except Exception:
                _ejecutar_completado_pedido(pedido_id, 0.0, 0.0, 0.0)
                return

        total_a_cobrar = pedido_actual.calcular_total(precios_actuales)
        nombre_mostrar = pedido_actual.nombre_mostrar

        texto_error = ft.Text(
            "",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=colors.RED_700,
            visible=False,
        )

        texto_cambio_valor = ft.Text(
            f"Cambio a regresar: {formatear_moneda(0)}",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=colors.GREEN_900,
            text_align=ft.TextAlign.CENTER,
        )
        subtexto_cambio = ft.Text(
            "Si no escribes monto, se registra como pago exacto.",
            size=12,
            color=colors.BLUE_GREY_700,
            text_align=ft.TextAlign.CENTER,
        )

        contenedor_cambio = ft.Container(
            bgcolor=colors.GREEN_50,
            border=ft.border.all(2, colors.GREEN_600),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            alignment=ft.alignment.center,
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[texto_cambio_valor, subtexto_cambio],
            ),
        )

        campo_pago = ft.TextField(
            label="¿Con cuánto paga el cliente? ($)",
            hint_text=f"Ej. {int(total_a_cobrar) if total_a_cobrar == int(total_a_cobrar) else total_a_cobrar}, 100, 200, 500",
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            text_size=22,
            border_radius=10,
        )

        def recalcular_cambio(_e: ft.ControlEvent | None = None) -> tuple[bool, float, float]:
            texto_error.visible = False
            raw = (campo_pago.value or "").strip().replace(",", "")
            if not raw:
                texto_cambio_valor.value = f"Cambio a regresar: {formatear_moneda(0)}"
                texto_cambio_valor.color = colors.GREEN_900
                subtexto_cambio.value = f"Pago exacto ({formatear_moneda(total_a_cobrar)})"
                contenedor_cambio.bgcolor = colors.GREEN_50
                contenedor_cambio.border = ft.border.all(2, colors.GREEN_600)
                if page:
                    page.update()
                return True, total_a_cobrar, 0.0

            try:
                monto_pagado = float(raw)
            except ValueError:
                texto_cambio_valor.value = "Ingresa un monto válido en números"
                texto_cambio_valor.color = colors.RED_800
                subtexto_cambio.value = ""
                contenedor_cambio.bgcolor = colors.RED_50
                contenedor_cambio.border = ft.border.all(2, colors.RED_400)
                if page:
                    page.update()
                return False, 0.0, 0.0

            diferencia = round(monto_pagado - total_a_cobrar, 2)
            if diferencia < 0:
                faltante = abs(diferencia)
                texto_cambio_valor.value = f"Faltan: {formatear_moneda(faltante)}"
                texto_cambio_valor.color = colors.RED_800
                subtexto_cambio.value = f"El total es de {formatear_moneda(total_a_cobrar)}"
                contenedor_cambio.bgcolor = colors.RED_50
                contenedor_cambio.border = ft.border.all(2, colors.RED_400)
                if page:
                    page.update()
                return False, monto_pagado, 0.0

            texto_cambio_valor.value = f"Cambio a regresar: {formatear_moneda(diferencia)}"
            texto_cambio_valor.color = colors.GREEN_900
            subtexto_cambio.value = (
                f"Recibido: {formatear_moneda(monto_pagado)}  ·  Total: {formatear_moneda(total_a_cobrar)}"
            )
            contenedor_cambio.bgcolor = colors.GREEN_50
            contenedor_cambio.border = ft.border.all(2, colors.GREEN_600)
            if page:
                page.update()
            return True, monto_pagado, diferencia

        campo_pago.on_change = recalcular_cambio

        def fijar_billete(monto: float) -> None:
            entero = int(monto) if monto == int(monto) else monto
            campo_pago.value = str(entero)
            recalcular_cambio()

        billetes_sugeridos = [50, 100, 200, 500]
        botones_billetes: list[ft.Control] = [
            ft.OutlinedButton(
                text=f"Exacto ({formatear_moneda(total_a_cobrar)})",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                ),
                on_click=lambda _e: fijar_billete(total_a_cobrar),
            )
        ]
        for billete in billetes_sugeridos:
            if billete >= total_a_cobrar:
                botones_billetes.append(
                    ft.OutlinedButton(
                        text=f"${billete}",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        ),
                        on_click=lambda _e, b=billete: fijar_billete(float(b)),
                    )
                )

        def cerrar_modal(_e: ft.ControlEvent | None = None) -> None:
            dialogo_cobro.open = False
            if page:
                page.update()

        def confirmar_cobro(_e: ft.ControlEvent | None = None) -> None:
            valido, pago_final, cambio_final = recalcular_cambio()
            if not valido:
                texto_error.value = "El dinero recibido debe cubrir el total del pedido."
                texto_error.visible = True
                if page:
                    page.update()
                return

            dialogo_cobro.open = False
            if page:
                page.update()
            _ejecutar_completado_pedido(
                pedido_id=pedido_id,
                total_cobrado=total_a_cobrar,
                pago_cliente=pago_final,
                cambio_entregado=cambio_final,
            )

        campo_pago.on_submit = confirmar_cobro

        dialogo_cobro = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icons.PAYMENTS_ROUNDED, color=colors.GREEN_700, size=28),
                    ft.Text(
                        f"Cobrar Pedido · {nombre_mostrar}",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Container(
                            bgcolor=colors.BLUE_GREY_900,
                            border_radius=12,
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            alignment=ft.alignment.center,
                            content=ft.Column(
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "TOTAL A COBRAR",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=colors.AMBER_300,
                                    ),
                                    ft.Text(
                                        formatear_moneda(total_a_cobrar),
                                        size=34,
                                        weight=ft.FontWeight.BOLD,
                                        color=colors.WHITE,
                                    ),
                                ],
                            ),
                        ),
                        campo_pago,
                        ft.Row(
                            wrap=True,
                            spacing=6,
                            run_spacing=6,
                            controls=botones_billetes,
                        ),
                        contenedor_cambio,
                        texto_error,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_modal),
                ft.ElevatedButton(
                    text="Cobrar y Marcar Listo",
                    icon=icons.CHECK_CIRCLE,
                    bgcolor=colors.GREEN_700,
                    color=colors.WHITE,
                    height=44,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),
                    on_click=confirmar_cobro,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialogo_cobro)
        dialogo_cobro.open = True
        page.update()

    def _renderizar_en_lock() -> None:
        jornada: dict | None = estado_cocina["jornada"]
        pendientes: list[Pedido] = estado_cocina["pendientes"]
        precios_actuales: dict[str, float] = estado_cocina["precios"]

        if jornada is None:
            titulo_contador.value = "Monitor de Cocina"
            insignia_pedidos_dia.visible = False
            insignia_espera.visible = False
            boton_accion_dia.visible = True
            boton_accion_dia.content = ft.ElevatedButton(
                content=ft.Row(
                    spacing=6,
                    tight=True,
                    controls=[
                        ft.Icon(icons.PLAY_CIRCLE_FILL, size=20, color=colors.WHITE),
                        ft.Text("Iniciar Día", size=15, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                    ],
                ),
                bgcolor=colors.GREEN_700,
                color=colors.WHITE,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.padding.symmetric(horizontal=14, vertical=6),
                ),
                on_click=_accion_iniciar_dia_cocina,
            )

            lista_tarjetas.controls = [
                ft.Container(
                    col={"xs": 12},
                    padding=ft.padding.symmetric(vertical=45, horizontal=20),
                    alignment=ft.alignment.center,
                    bgcolor=colors.WHITE,
                    border_radius=14,
                    border=ft.border.all(2, colors.BLUE_GREY_200),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=14,
                        controls=[
                            ft.Icon(
                                icons.WB_SUNNY_ROUNDED,
                                size=56,
                                color=colors.ORANGE_700,
                            ),
                            ft.Text(
                                "El día aún no ha iniciado",
                                size=26,
                                weight=ft.FontWeight.BOLD,
                                color=colors.BLACK87,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Presiona 'INICIAR DÍA' para abrir la jornada de hoy y recibir pedidos en cocina.",
                                size=16,
                                color=colors.BLACK54,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    spacing=8,
                                    tight=True,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(icons.PLAY_CIRCLE_FILL, size=26, color=colors.WHITE),
                                        ft.Text(
                                            "INICIAR DÍA",
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=colors.WHITE,
                                        ),
                                    ],
                                ),
                                bgcolor=colors.GREEN_700,
                                color=colors.WHITE,
                                height=54,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    padding=ft.padding.symmetric(horizontal=28, vertical=10),
                                ),
                                on_click=_accion_iniciar_dia_cocina,
                            ),
                        ],
                    ),
                )
            ]
            return

        total = len(pendientes)
        visibles = seleccionar_pedidos_visibles_cocina(pendientes)
        en_espera = max(0, total - len(visibles))
        total_pedidos_dia = int(jornada.get("total_pedidos", 0))
        completados_dia = int(jornada.get("completados", 0))
        total_pzs_dia = int(jornada.get("total_platillos", 0))

        titulo_contador.value = (
            f"En Cocina ({total})" if total > 0 else "En Cocina"
        )

        insignia_pedidos_dia.visible = True
        insignia_pedidos_dia.bgcolor = colors.BLUE_50
        insignia_pedidos_dia.border = ft.border.all(1.5, colors.BLUE_400)
        insignia_pedidos_dia.border_radius = 8
        insignia_pedidos_dia.padding = ft.padding.symmetric(horizontal=10, vertical=5)
        insignia_pedidos_dia.content = ft.Row(
            spacing=6,
            tight=True,
            controls=[
                ft.Icon(icons.RECEIPT_LONG, size=18, color=colors.BLUE_900),
                ft.Text(
                    f"Pedidos del Día: {total_pedidos_dia} (Listos: {completados_dia} · Piezas: {total_pzs_dia})",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLUE_900,
                ),
            ],
        )

        boton_accion_dia.visible = True
        boton_accion_dia.content = ft.ElevatedButton(
            content=ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    ft.Icon(icons.LOCK_CLOCK, size=18, color=colors.WHITE),
                    ft.Text(
                        "Finalizar Día",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=colors.WHITE,
                    ),
                ],
            ),
            bgcolor=colors.RED_700,
            color=colors.WHITE,
            height=38,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
            ),
            on_click=_accion_finalizar_dia_cocina,
        )

        if en_espera > 0:
            insignia_espera.visible = True
            insignia_espera.bgcolor = colors.ORANGE_100
            insignia_espera.border = ft.border.all(1.5, colors.ORANGE_700)
            insignia_espera.border_radius = 8
            insignia_espera.padding = ft.padding.symmetric(horizontal=12, vertical=5)
            insignia_espera.content = ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    ft.Icon(icons.SCHEDULE, size=18, color=colors.DEEP_ORANGE_900),
                    ft.Text(
                        f"Mostrando {len(visibles)} · +{en_espera} en espera",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=colors.DEEP_ORANGE_900,
                    ),
                ],
            )
        else:
            insignia_espera.visible = False

        if not visibles:
            lista_tarjetas.controls = [
                ft.Container(
                    col={"xs": 12},
                    padding=ft.padding.symmetric(vertical=50, horizontal=20),
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(
                                icons.HOURGLASS_EMPTY_ROUNDED,
                                size=44,
                                color=colors.BLUE_ACCENT_700,
                            ),
                            ft.Text(
                                "Esperando pedidos del día...",
                                size=19,
                                weight=ft.FontWeight.BOLD,
                                color=colors.BLACK54,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                    ),
                )
            ]
            return

        usar_pantalla_completa = len(visibles) == 1
        lista_tarjetas.controls = [
            crear_tarjeta_pedido_cocina(
                pedido=ped,
                on_completar=_completar_pedido_accion,
                posicion_cola=idx,
                pantalla_completa=usar_pantalla_completa,
                precios=precios_actuales,
            )
            for idx, ped in enumerate(visibles, start=1)
        ]

    def _sincronizar_desde_bd(forzar_render: bool = False) -> bool:
        precios = obtener_precios_menu()
        jornada = obtener_jornada_activa()
        pendientes = (
            obtener_pedidos_pendientes(solo_jornada_activa=True)
            if jornada is not None
            else []
        )
        nueva_huella = _calcular_huella(jornada, pendientes, precios)

        with ui_lock:
            hubo_cambios = (
                forzar_render or nueva_huella != estado_cocina["huella_pendientes"]
            )
            if hubo_cambios:
                estado_cocina["precios"] = precios
                estado_cocina["jornada"] = jornada
                estado_cocina["pendientes"] = pendientes
                estado_cocina["huella_pendientes"] = nueva_huella
                _renderizar_en_lock()
            return hubo_cambios

    def _tarea_actualizacion() -> None:
        logging.info("Hilo del monitor de cocina iniciado.")
        while not stop_event.is_set():
            if not page or page.route != "/home":
                break

            try:
                if _sincronizar_desde_bd() and page and not stop_event.is_set():
                    try:
                        page.update()
                    except Exception as update_err:
                        logging.error(f"Error durante page.update(): {update_err}")
                        break
            except mysql.connector.Error as err:
                logging.error(f"Error de base de datos en cocina: {err}")
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue
            except Exception as err:
                logging.error(f"Error inesperado en cocina: {err}", exc_info=True)
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue

            if stop_event.wait(POLL_INTERVAL_SECONDS):
                break

        logging.info("Hilo del monitor de cocina detenido limpiamente.")

    try:
        _sincronizar_desde_bd(forzar_render=True)
    except Exception as err:
        logging.warning(f"No se pudo realizar la carga inicial de cocina: {err}")
        with ui_lock:
            _renderizar_en_lock()

    navegacion = crear_navegacion(page, selected_index=0)

    hilo = threading.Thread(target=_tarea_actualizacion, daemon=True)
    hilo.start()

    return ft.View(
        route="/home",
        controls=[
            barra_superior,
            lista_tarjetas,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=10,
        bgcolor=COLOR_FONDO_PAGINA,
    )


# Alias de compatibilidad
View_home = view_home
