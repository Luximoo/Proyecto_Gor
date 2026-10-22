"""Vista para meseros (`/editar-pedidos`): listado de pedidos para consultar y editar."""

from __future__ import annotations

import logging

import flet as ft

from data.repositorio import (
    obtener_pedidos_completados_hoy,
    obtener_pedidos_pendientes,
)
from domain.modelos import Pedido
from ui.components import crear_navegacion, crear_tarjeta_pedido_mesero
from ui.theme import COLOR_FONDO_PAGINA, colors, icons


def view_editar_pedidos(page: ft.Page) -> ft.View:
    """
    Construye la pantalla exclusiva para que el mesero busque y edite pedidos
    (tanto los que siguen 'En cocina' como los 'Completados' del día).
    """
    estado = {
        "tab_activa": "PENDIENTES",  # "PENDIENTES" | "COMPLETADOS"
        "pendientes": [],
        "completados": [],
    }

    fila_filtros = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    lista_tarjetas = ft.Column(spacing=10)

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

        pedidos_mostrar = pendientes if es_pendientes else completados

        if not pedidos_mostrar:
            texto_vacio = (
                "No hay pedidos activos en este momento."
                if es_pendientes
                else "No hay pedidos completados hoy."
            )
            lista_tarjetas.controls = [
                ft.Container(
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

        lista_tarjetas.controls = [
            crear_tarjeta_pedido_mesero(pedido=ped, on_editar=abrir_edicion)
            for ped in pedidos_mostrar
        ]

    cargar_datos_bd()
    renderizar()

    encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                "Editar Pedidos",
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
            lista_tarjetas,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=14,
        bgcolor=COLOR_FONDO_PAGINA,
    )
