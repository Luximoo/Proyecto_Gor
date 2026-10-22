"""Vista para meseros (`/editar-pedidos`): editar pedidos y reordenar su prioridad arrastrándolos."""

from __future__ import annotations

import logging

import flet as ft

from data.repositorio import (
    actualizar_orden_pedidos,
    obtener_pedidos_completados_hoy,
    obtener_pedidos_pendientes,
)
from domain.modelos import Pedido
from ui.components import crear_navegacion, crear_tarjeta_pedido_mesero
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
    }

    fila_filtros = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    instruccion_arrastre = ft.Container()
    lista_tarjetas = ft.ResponsiveRow(spacing=12, run_spacing=12)

    def cargar_datos_bd() -> None:
        try:
            estado["pendientes"] = obtener_pedidos_pendientes()
            estado["completados"] = obtener_pedidos_completados_hoy()
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

    def reordenar_por_arrastre(id_origen: int, id_destino: int) -> None:
        """Mueve el pedido `id_origen` al lugar donde estaba `id_destino` y guarda el orden en BD."""
        pendientes: list[Pedido] = list(estado["pendientes"])
        idx_origen = next((i for i, p in enumerate(pendientes) if p.id == id_origen), None)
        idx_destino = next((i for i, p in enumerate(pendientes) if p.id == id_destino), None)

        if idx_origen is None or idx_destino is None or idx_origen == idx_destino:
            return

        pedido_movido = pendientes.pop(idx_origen)
        pendientes.insert(idx_destino, pedido_movido)

        estado["pendientes"] = pendientes
        persistir_nuevo_orden(pendientes)
        renderizar()
        page.update()

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

        instruccion_arrastre.visible = es_pendientes and len(pendientes) > 1
        instruccion_arrastre.content = ft.Container(
            bgcolor=colors.BLUE_50,
            border=ft.border.all(1, colors.BLUE_200),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(icons.DRAG_INDICATOR, size=18, color=colors.BLUE_700),
                    ft.Text(
                        "Arrastra una tarjeta sobre otra (o usa ◀ ▶) para cambiar qué pedido sale primero en Cocina.",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=colors.BLUE_900,
                        expand=True,
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
        lista_tarjetas.controls = [
            crear_tarjeta_pedido_mesero(
                page=page,
                pedido=ped,
                on_editar=abrir_edicion,
                posicion_cola=idx if es_pendientes else None,
                total_en_cola=total_cola if es_pendientes else 0,
                on_arrastrar_a_destino=reordenar_por_arrastre if es_pendientes else None,
                on_mover_paso=mover_un_paso if es_pendientes else None,
            )
            for idx, ped in enumerate(pedidos_mostrar, start=1)
        ]

    cargar_datos_bd()
    renderizar()

    encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                "Editar y Ordenar Pedidos",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            ft.IconButton(
                icon=icons.REFRESH,
                icon_color=colors.BLUE_GREY_700,
                tooltip="Actualizar lista",
                on_click=recargar_manual,
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
