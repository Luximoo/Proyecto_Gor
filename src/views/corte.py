"""Vista de Gestión de Jornada y Corte del Día (`/corte`): Iniciar Día, Pedidos del Día y Finalizar Día."""

from __future__ import annotations

import logging
from typing import Callable

import flet as ft

from data.repositorio import (
    finalizar_jornada_dia,
    iniciar_jornada_dia,
    obtener_historial_cortes,
    obtener_resumen_jornada_actual,
)
from domain.modelos import EstadoPedido, Pedido, TipoServicio, formatear_moneda
from ui.components import crear_navegacion
from ui.theme import COLOR_FONDO_PAGINA, colors, icons


def mostrar_dialogo_confirmar_corte(
    page: ft.Page,
    on_corte_realizado: Callable[[], None] | None = None,
) -> None:
    """
    Abre un modal con el resumen completo del día (pedidos, gorditas, sopes y guisos)
    para confirmar y ejecutar el Corte / Finalización del Día.
    """
    try:
        resumen = obtener_resumen_jornada_actual()
    except Exception as err:
        logging.error(f"Error al obtener resumen para corte: {err}")
        return

    if not resumen.get("activa"):
        return

    total_pedidos = int(resumen["total_pedidos"])
    pendientes = int(resumen["pendientes"])
    completados = int(resumen["completados"])
    total_platillos = int(resumen["total_platillos"])
    total_ventas = float(resumen.get("total_ventas", 0.0))
    ventas_cobradas = float(resumen.get("ventas_cobradas", 0.0))
    ventas_pendientes = float(resumen.get("ventas_pendientes", 0.0))
    mesa = int(resumen["mesa"])
    llevar = int(resumen["llevar"])
    por_producto: dict[str, int] = resumen["por_producto"]
    por_guiso: dict[str, int] = resumen["por_guiso"]

    texto_productos = (
        " · ".join(f"{prod}: {cant}" for prod, cant in por_producto.items())
        if por_producto
        else "Sin platillos registrados"
    )

    filas_guisos: list[ft.Control] = []
    if por_guiso:
        for guiso, cant in por_guiso.items():
            filas_guisos.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(guiso, size=14, weight=ft.FontWeight.W_500, color=colors.BLACK87),
                        ft.Text(f"{cant} pzs", size=14, weight=ft.FontWeight.BOLD, color=colors.DEEP_ORANGE_900),
                    ],
                )
            )
    else:
        filas_guisos.append(
            ft.Text("No se registraron ventas en esta jornada.", size=13, color=colors.BLACK54)
        )

    aviso_pendientes = ft.Container(visible=False)
    if pendientes > 0:
        aviso_pendientes = ft.Container(
            visible=True,
            bgcolor=colors.AMBER_100,
            border=ft.border.all(1, colors.AMBER_800),
            border_radius=8,
            padding=ft.padding.all(8),
            content=ft.Text(
                f"Nota: Hay {pendientes} pedido(s) aún en cocina que se marcarán como completados al cerrar el día.",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
        )

    def confirmar_cierre(_e: ft.ControlEvent) -> None:
        page.close(dialogo_corte)
        try:
            finalizar_jornada_dia()
            snack = ft.SnackBar(
                content=ft.Text(
                    f"Día finalizado. Corte guardado: {total_pedidos} pedidos, {total_platillos} platillos · Total vendido: {formatear_moneda(total_ventas)}.",
                    color=colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=colors.GREEN_700,
                duration=3500,
            )
            try:
                page.open(snack)
            except Exception:
                page.snack_bar = snack
                snack.open = True
                page.update()

            if on_corte_realizado is not None:
                on_corte_realizado()
        except Exception as err:
            logging.error(f"Error al finalizar el día: {err}")

    dialogo_corte = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(icons.ASSESSMENT_ROUNDED, color=colors.DEEP_ORANGE_700, size=26),
                ft.Text("Finalizar Día · Corte de Caja", weight=ft.FontWeight.BOLD, size=18),
            ],
        ),
        content=ft.Container(
            width=360,
            content=ft.Column(
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                controls=[
                    aviso_pendientes,
                    ft.Container(
                        bgcolor=colors.GREEN_50,
                        border=ft.border.all(2, colors.GREEN_700),
                        border_radius=10,
                        padding=ft.padding.all(12),
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "VENTA TOTAL DEL DÍA",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.GREEN_900,
                                ),
                                ft.Text(
                                    formatear_moneda(total_ventas),
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.GREEN_900,
                                ),
                                ft.Text(
                                    f"Cobrado: {formatear_moneda(ventas_cobradas)} · Por cobrar: {formatear_moneda(ventas_pendientes)}",
                                    size=12,
                                    color=colors.BLUE_GREY_800,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        bgcolor=colors.BLUE_GREY_50,
                        border_radius=10,
                        padding=ft.padding.all(12),
                        content=ft.Column(
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text("Total Pedidos del Día:", size=15, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{total_pedidos}", size=18, weight=ft.FontWeight.BOLD, color=colors.BLUE_800),
                                    ],
                                ),
                                ft.Text(
                                    f"Completados: {completados} · En cocina: {pendientes}\nMesa: {mesa} · Para llevar: {llevar}",
                                    size=12,
                                    color=colors.BLUE_GREY_800,
                                ),
                                ft.Divider(height=6, color=colors.BLUE_GREY_200),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text("Total Platillos:", size=15, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{total_platillos} pzs", size=18, weight=ft.FontWeight.BOLD, color=colors.GREEN_800),
                                    ],
                                ),
                                ft.Text(
                                    texto_productos,
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.DEEP_ORANGE_800,
                                ),
                            ],
                        ),
                    ),
                    ft.Text("Desglose por guiso:", size=13, weight=ft.FontWeight.BOLD, color=colors.BLACK87),
                    ft.Container(
                        bgcolor=colors.WHITE,
                        border=ft.border.all(1, colors.BLUE_GREY_200),
                        border_radius=8,
                        padding=ft.padding.all(10),
                        content=ft.Column(spacing=4, controls=filas_guisos),
                    ),
                ],
            ),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _e: page.close(dialogo_corte)),
            ft.ElevatedButton(
                "Finalizar Día y Guardar Corte",
                icon=icons.LOCK_CLOCK,
                bgcolor=colors.RED_700,
                color=colors.WHITE,
                on_click=confirmar_cierre,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dialogo_corte)


def view_corte_dia(page: ft.Page) -> ft.View:
    """
    Construye la sección dedicada al Corte del Día (`/corte`):
    - Botón para Iniciar el Día y Finalizar el Día.
    - Tarjetas con el resumen de pedidos del día, platillos por tipo y por guiso.
    - Lista de todos los pedidos del día actual y cortes anteriores.
    """
    contenedor_principal = ft.Column(spacing=14)

    def accion_iniciar_dia(_e: ft.ControlEvent) -> None:
        try:
            iniciar_jornada_dia()
            renderizar()
            page.update()
        except Exception as err:
            logging.error(f"Error al iniciar el día: {err}")

    def accion_finalizar_dia(_e: ft.ControlEvent) -> None:
        def post_corte() -> None:
            renderizar()
            page.update()

        mostrar_dialogo_confirmar_corte(page, on_corte_realizado=post_corte)

    def renderizar() -> None:
        try:
            resumen = obtener_resumen_jornada_actual()
            historial = obtener_historial_cortes(limite=8)
        except Exception as err:
            logging.error(f"Error cargando vista de corte: {err}")
            contenedor_principal.controls = [
                ft.Text(f"Error al conectar con la base de datos: {err}", color=colors.RED_700)
            ]
            return

        activa = bool(resumen.get("activa"))
        jornada = resumen.get("jornada") or {}

        # 1. Banner de estado del día (Iniciar Día / Finalizar Día)
        if not activa:
            tarjeta_estado = ft.Container(
                bgcolor=colors.WHITE,
                border=ft.border.all(2, colors.BLUE_GREY_300),
                border_radius=14,
                padding=ft.padding.all(20),
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.Icon(icons.WB_SUNNY_ROUNDED, size=52, color=colors.ORANGE_700),
                        ft.Text(
                            "El día aún no ha sido iniciado",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLACK87,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Presiona 'Iniciar Día' para abrir la cuenta de pedidos de hoy desde cero.",
                            size=14,
                            color=colors.BLACK54,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.ElevatedButton(
                            content=ft.Row(
                                spacing=8,
                                tight=True,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(icons.PLAY_CIRCLE_FILL, size=24, color=colors.WHITE),
                                    ft.Text(
                                        "INICIAR DÍA",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=colors.WHITE,
                                    ),
                                ],
                            ),
                            bgcolor=colors.GREEN_700,
                            color=colors.WHITE,
                            height=50,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.padding.symmetric(horizontal=24, vertical=10),
                            ),
                            on_click=accion_iniciar_dia,
                        ),
                    ],
                ),
            )
            controles_vista: list[ft.Control] = [tarjeta_estado]
        else:
            iniciada_dt = jornada.get("iniciada_at")
            hora_inicio = iniciada_dt.strftime("%d/%m/%Y %H:%M") if iniciada_dt else "Hoy"
            total_pedidos = int(resumen["total_pedidos"])
            pendientes = int(resumen["pendientes"])
            completados = int(resumen["completados"])
            total_platillos = int(resumen["total_platillos"])
            total_ventas = float(resumen.get("total_ventas", 0.0))
            ventas_cobradas = float(resumen.get("ventas_cobradas", 0.0))
            ventas_pendientes = float(resumen.get("ventas_pendientes", 0.0))
            mesa = int(resumen["mesa"])
            llevar = int(resumen["llevar"])
            por_producto: dict[str, int] = resumen["por_producto"]
            por_guiso: dict[str, int] = resumen["por_guiso"]
            pedidos_dia: list[Pedido] = resumen["pedidos"]
            precios_menu: dict[str, float] = resumen.get("precios") or {}

            tarjeta_encabezado_dia = ft.Container(
                bgcolor=colors.GREEN_50,
                border=ft.border.all(2, colors.GREEN_600),
                border_radius=12,
                padding=ft.padding.all(14),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(icons.CHECK_CIRCLE, color=colors.GREEN_700, size=22),
                                        ft.Text(
                                            "DÍA EN CURSO (ABIERTO)",
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            color=colors.GREEN_900,
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    f"Iniciado: {hora_inicio}",
                                    size=13,
                                    color=colors.BLUE_GREY_800,
                                ),
                            ],
                        ),
                        ft.ElevatedButton(
                            content=ft.Row(
                                spacing=6,
                                tight=True,
                                controls=[
                                    ft.Icon(icons.LOCK_CLOCK, size=20, color=colors.WHITE),
                                    ft.Text(
                                        "Finalizar Día (Corte)",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=colors.WHITE,
                                    ),
                                ],
                            ),
                            bgcolor=colors.RED_700,
                            color=colors.WHITE,
                            height=44,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                            ),
                            on_click=accion_finalizar_dia,
                        ),
                    ],
                ),
            )

            # Tarjetas KPI del día
            texto_prod_resumen = (
                " · ".join(f"{k}: {v}" for k, v in por_producto.items())
                if por_producto
                else "0 Gorditas · 0 Sopes"
            )

            fila_kpis = ft.ResponsiveRow(
                spacing=10,
                run_spacing=10,
                controls=[
                    ft.Container(
                        col={"xs": 12, "sm": 6, "md": 3},
                        bgcolor=colors.GREEN_50,
                        border=ft.border.all(2, colors.GREEN_600),
                        border_radius=12,
                        padding=ft.padding.all(12),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("VENTA TOTAL DEL DÍA", size=12, weight=ft.FontWeight.BOLD, color=colors.GREEN_900),
                                ft.Text(formatear_moneda(total_ventas), size=28, weight=ft.FontWeight.BOLD, color=colors.GREEN_900),
                                ft.Text(
                                    f"Cobrado: {formatear_moneda(ventas_cobradas)} · Por cobrar: {formatear_moneda(ventas_pendientes)}",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.BLUE_GREY_800,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        col={"xs": 12, "sm": 6, "md": 3},
                        bgcolor=colors.WHITE,
                        border=ft.border.all(1.5, colors.BLUE_200),
                        border_radius=12,
                        padding=ft.padding.all(12),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("PEDIDOS DEL DÍA", size=12, weight=ft.FontWeight.BOLD, color=colors.BLUE_800),
                                ft.Text(f"{total_pedidos}", size=28, weight=ft.FontWeight.BOLD, color=colors.BLACK),
                                ft.Text(
                                    f"Listos: {completados} · En cocina: {pendientes}",
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=colors.BLUE_GREY_700,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        col={"xs": 12, "sm": 6, "md": 3},
                        bgcolor=colors.WHITE,
                        border=ft.border.all(1.5, colors.ORANGE_300),
                        border_radius=12,
                        padding=ft.padding.all(12),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("PLATILLOS VENDIDOS", size=12, weight=ft.FontWeight.BOLD, color=colors.DEEP_ORANGE_800),
                                ft.Text(f"{total_platillos} pzs", size=28, weight=ft.FontWeight.BOLD, color=colors.BLACK),
                                ft.Text(
                                    texto_prod_resumen,
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.DEEP_ORANGE_900,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        col={"xs": 12, "sm": 6, "md": 3},
                        bgcolor=colors.WHITE,
                        border=ft.border.all(1.5, colors.GREEN_300),
                        border_radius=12,
                        padding=ft.padding.all(12),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Text("MODALIDAD DE SERVICIO", size=12, weight=ft.FontWeight.BOLD, color=colors.GREEN_800),
                                ft.Text(f"Mesa: {mesa}", size=18, weight=ft.FontWeight.BOLD, color=colors.BLUE_800),
                                ft.Text(f"Para llevar: {llevar}", size=16, weight=ft.FontWeight.BOLD, color=colors.DEEP_ORANGE_800),
                            ],
                        ),
                    ),
                ],
            )

            # Desglose por guiso
            chips_guisos_vendidos = [
                ft.Container(
                    bgcolor=colors.ORANGE_50,
                    border=ft.border.all(1, colors.ORANGE_400),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    content=ft.Text(
                        f"{guiso}: {cant} pzs",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=colors.DEEP_ORANGE_900,
                    ),
                )
                for guiso, cant in por_guiso.items()
            ]
            seccion_guisos = ft.Container(
                bgcolor=colors.WHITE,
                border=ft.border.all(1, colors.BLUE_GREY_200),
                border_radius=12,
                padding=ft.padding.all(12),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Piezas vendidas por guiso hoy:",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLACK87,
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=chips_guisos_vendidos
                            if chips_guisos_vendidos
                            else [ft.Text("Aún no hay platillos registrados en este día.", size=13, color=colors.BLACK54)],
                        ),
                    ],
                ),
            )

            # Lista de pedidos del día
            filas_pedidos_dia: list[ft.Control] = []
            for idx_ped, ped in enumerate(pedidos_dia, start=1):
                es_listo = ped.estado == EstadoPedido.COMPLETADO
                es_mesa = ped.tipo_servicio == TipoServicio.MESA
                hora_p = (ped.completed_at or ped.created_at)
                hora_txt = hora_p.strftime("%H:%M") if hora_p else ""
                monto_ped = ped.total_cobrado if ped.total_cobrado > 0 else ped.calcular_total(precios_menu)
                detalle_cobro = f"Total: {formatear_moneda(monto_ped)}"
                if es_listo and ped.pago_cliente > 0:
                    detalle_cobro += f" (Pagó: {formatear_moneda(ped.pago_cliente)} · Cambio: {formatear_moneda(ped.cambio_entregado)})"

                resumen_items = ", ".join(
                    f"{it.cantidad}× {it.formatear_descripcion_completa()}"
                    for pl in ped.platos
                    for it in pl.items
                )
                filas_pedidos_dia.append(
                    ft.Container(
                        bgcolor=colors.WHITE,
                        border=ft.border.all(1, colors.GREEN_300 if es_listo else colors.ORANGE_400),
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    wrap=True,
                                    controls=[
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Container(
                                                    bgcolor=colors.BLUE_GREY_900,
                                                    border_radius=6,
                                                    padding=ft.padding.symmetric(horizontal=7, vertical=2),
                                                    content=ft.Text(
                                                        f"{ped.numero_pedido_mostrar}°",
                                                        size=12,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=colors.WHITE,
                                                    ),
                                                ),
                                                ft.Text(
                                                    ped.nombre_mostrar,
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=colors.BLACK87,
                                                ),
                                                ft.Container(
                                                    bgcolor=colors.BLUE_700 if es_mesa else colors.DEEP_ORANGE_700,
                                                    border_radius=6,
                                                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                                    content=ft.Text(
                                                        "MESA" if es_mesa else "LLEVAR",
                                                        size=11,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=colors.WHITE,
                                                    ),
                                                ),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=6,
                                            controls=[
                                                ft.Container(
                                                    bgcolor=colors.GREEN_50,
                                                    border=ft.border.all(1, colors.GREEN_600),
                                                    border_radius=6,
                                                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                                    content=ft.Text(
                                                        detalle_cobro,
                                                        size=12,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=colors.GREEN_900,
                                                    ),
                                                ),
                                                ft.Container(
                                                    bgcolor=colors.GREEN_100 if es_listo else colors.ORANGE_100,
                                                    border_radius=6,
                                                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                                    content=ft.Text(
                                                        "Completado" if es_listo else "En cocina",
                                                        size=11,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=colors.GREEN_900 if es_listo else colors.DEEP_ORANGE_900,
                                                    ),
                                                ),
                                                ft.Text(hora_txt, size=12, color=colors.BLUE_GREY_600),
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    resumen_items,
                                    size=13,
                                    color=colors.BLACK87,
                                    weight=ft.FontWeight.W_500,
                                ),
                            ],
                        ),
                    )
                )

            seccion_lista_pedidos = ft.Column(
                spacing=8,
                controls=[
                    ft.Text(
                        f"Pedidos registrados en el día ({len(pedidos_dia)}):",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLACK87,
                    ),
                    *(
                        filas_pedidos_dia
                        if filas_pedidos_dia
                        else [
                            ft.Container(
                                bgcolor=colors.WHITE,
                                border_radius=10,
                                padding=ft.padding.all(16),
                                content=ft.Text(
                                    "Aún no se han tomado pedidos en el día actual.",
                                    size=14,
                                    color=colors.BLACK54,
                                ),
                            )
                        ]
                    ),
                ],
            )

            controles_vista = [
                tarjeta_encabezado_dia,
                fila_kpis,
                seccion_guisos,
                seccion_lista_pedidos,
            ]

        # Historial de cortes cerrados
        if historial:
            filas_hist: list[ft.Control] = []
            for h in historial:
                ini = h["iniciada_at"].strftime("%d/%m %H:%M") if h.get("iniciada_at") else ""
                fin = h["cerrada_at"].strftime("%d/%m %H:%M") if h.get("cerrada_at") else ""
                venta_h = float(h.get("total_ventas", 0.0))
                filas_hist.append(
                    ft.Container(
                        bgcolor=colors.WHITE,
                        border=ft.border.all(1, colors.BLUE_GREY_200),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            wrap=True,
                            controls=[
                                ft.Text(
                                    f"Corte #{h['id']} ({ini} → {fin})",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.BLUE_GREY_900,
                                ),
                                ft.Text(
                                    f"{h['total_pedidos']} pedidos · {h['total_platillos']} platillos · Venta: {formatear_moneda(venta_h)}",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.GREEN_800,
                                ),
                            ],
                        ),
                    )
                )
            controles_vista.append(
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Divider(height=10, color=colors.BLUE_GREY_200),
                        ft.Text(
                            "Historial de Cortes Anteriores:",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLUE_GREY_800,
                        ),
                        *filas_hist,
                    ],
                )
            )

        contenedor_principal.controls = controles_vista

    renderizar()

    encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                "Corte del Día y Jornada",
                size=22,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            ft.IconButton(
                icon=icons.REFRESH,
                icon_color=colors.BLUE_GREY_700,
                tooltip="Actualizar resumen",
                on_click=lambda _e: (renderizar(), page.update()),
            ),
        ],
    )

    navegacion = crear_navegacion(page, selected_index=3)

    return ft.View(
        route="/corte",
        controls=[
            encabezado,
            contenedor_principal,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=14,
        bgcolor=COLOR_FONDO_PAGINA,
    )
