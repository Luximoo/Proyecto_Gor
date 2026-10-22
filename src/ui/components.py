"""Componentes visuales reutilizables de la interfaz (Cocina, Mesero y Navegación)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable
import flet as ft

from ui.theme import (
    colors,
    icons,
    with_opacity,
)

if TYPE_CHECKING:
    from domain.modelos import Pedido

RUTAS_NAVEGACION = {
    0: "/home",
    1: "/Pedidos",
    2: "/editar-pedidos",
}


def _cambiar_vista(
    page: ft.Page,
    e: ft.ControlEvent,
    on_intentar_navegar: Callable[[str], None] | None = None,
) -> None:
    """Cambia la ruta activa según el índice seleccionado en la barra de navegación."""
    ruta_destino = RUTAS_NAVEGACION.get(e.control.selected_index, "/home")
    if page.route == ruta_destino:
        return
    if on_intentar_navegar is not None:
        on_intentar_navegar(ruta_destino)
    else:
        page.go(ruta_destino)


def crear_navegacion(
    page: ft.Page,
    selected_index: int | None = None,
    on_intentar_navegar: Callable[[str], None] | None = None,
) -> ft.NavigationBar:
    """
    Crea la barra de navegación inferior con 3 secciones:
    0: Cocina (/home)
    1: Ordenar (/Pedidos)
    2: Editar Pedidos (/editar-pedidos)
    """
    if selected_index is None:
        ruta = page.route or "/home"
        if ruta == "/editar-pedidos" or ruta.startswith("/pedido/"):
            selected_index = 2
        elif ruta in ("/Pedidos", "/pedido"):
            selected_index = 1
        else:
            selected_index = 0

    return ft.NavigationBar(
        selected_index=selected_index,
        destinations=[
            ft.NavigationBarDestination(icon=icons.LIST_ALT, label="Cocina"),
            ft.NavigationBarDestination(icon=icons.ADD_SHOPPING_CART, label="Ordenar"),
            ft.NavigationBarDestination(icon=icons.EDIT_NOTE, label="Editar Pedidos"),
        ],
        on_change=lambda e: _cambiar_vista(page, e, on_intentar_navegar),
    )


def _crear_insignia_servicio(es_mesa: bool) -> ft.Container:
    """Insignia clara para distinguir MESA vs PARA LLEVAR."""
    return ft.Container(
        bgcolor=colors.BLUE_700 if es_mesa else colors.DEEP_ORANGE_700,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        content=ft.Row(
            spacing=5,
            tight=True,
            controls=[
                ft.Icon(
                    icons.RESTAURANT if es_mesa else icons.SHOPPING_BAG,
                    size=15,
                    color=colors.WHITE,
                ),
                ft.Text(
                    "MESA" if es_mesa else "PARA LLEVAR",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=colors.WHITE,
                ),
            ],
        ),
    )


def _crear_bloques_platos(pedido: "Pedido", tamano_item: int = 17, tamano_detalle: int = 14) -> list[ft.Control]:
    """Construye los bloques visuales de cada plato con letra grande y legible."""
    bloques: list[ft.Control] = []
    for plato in pedido.platos:
        if plato.esta_vacio:
            continue

        lineas_plato: list[ft.Control] = [
            ft.Container(
                bgcolor=colors.ORANGE_100,
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            f"Plato {plato.numero}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors.DEEP_ORANGE_900,
                        ),
                        ft.Text(
                            f"{plato.total_piezas} pzs",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.DEEP_ORANGE_900,
                        ),
                    ],
                ),
            )
        ]

        for item in plato.items:
            detalle = item.formatear_detalle()
            controles_item: list[ft.Control] = [
                ft.Text(
                    f"• {item.formatear_titulo()}",
                    size=tamano_item,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK87,
                )
            ]
            if detalle:
                controles_item.append(
                    ft.Container(
                        padding=ft.padding.only(left=16),
                        content=ft.Text(
                            detalle,
                            size=tamano_detalle,
                            weight=ft.FontWeight.BOLD,
                            color=colors.RED_800,
                        ),
                    )
                )
            lineas_plato.append(ft.Column(spacing=2, controls=controles_item))

        bloques.append(
            ft.Container(
                bgcolor=colors.BLUE_GREY_50,
                border_radius=10,
                padding=ft.padding.all(10),
                content=ft.Column(spacing=6, controls=lineas_plato),
            )
        )
    return bloques


def crear_tarjeta_pedido_cocina(
    pedido: "Pedido",
    on_completar: Callable[[int], None],
) -> ft.Container:
    """
    Tarjeta limpia y de alta legibilidad exclusiva para el monitor de cocina (`/home`).
    Sin botón de editar ni distracciones: solo número de orden, Mesa/Llevar, platos
    con letra grande y botón de Listo.
    """
    from domain.modelos import TipoServicio

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    fue_modificado = pedido.version > 1

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"#{pedido_id}",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLACK87,
                    ),
                    _crear_insignia_servicio(es_mesa),
                ],
            ),
            ft.ElevatedButton(
                text="Listo",
                icon=icons.CHECK_CIRCLE,
                bgcolor=colors.GREEN_700,
                color=colors.WHITE,
                height=38,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=lambda _e, pid=pedido_id: on_completar(pid),
            ),
        ],
    )

    controles_tarjeta: list[ft.Control] = [fila_encabezado]

    if fue_modificado:
        controles_tarjeta.append(
            ft.Container(
                bgcolor=colors.AMBER_300,
                border=ft.border.all(1, colors.AMBER_800),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                content=ft.Row(
                    spacing=5,
                    tight=True,
                    controls=[
                        ft.Icon(icons.AUTORENEW, size=15, color=colors.BLACK87),
                        ft.Text(
                            "PEDIDO MODIFICADO",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLACK87,
                        ),
                    ],
                ),
            )
        )

    controles_tarjeta.extend(_crear_bloques_platos(pedido, tamano_item=17, tamano_detalle=14))

    return ft.Container(
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(14),
        margin=ft.margin.symmetric(vertical=6, horizontal=2),
        border_radius=14,
        border=ft.border.all(2, colors.AMBER_700 if fue_modificado else colors.ORANGE_400),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=6,
            color=with_opacity(0.12, colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
        content=ft.Column(spacing=10, controls=controles_tarjeta),
    )


def crear_tarjeta_pedido_mesero(
    pedido: "Pedido",
    on_editar: Callable[[int], None],
) -> ft.Container:
    """
    Tarjeta para la sección 'Editar Pedidos' (`/editar-pedidos`) de los meseros.
    Muestra el detalle del pedido, su estado ('En cocina' o 'Completado'), hora
    y el botón para editarlo.
    """
    from domain.modelos import EstadoPedido, TipoServicio

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    es_pendiente = pedido.estado == EstadoPedido.PENDIENTE

    marca_tiempo = pedido.updated_at or pedido.created_at
    hora_str = marca_tiempo.strftime("%H:%M") if marca_tiempo else ""

    insignia_estado = ft.Container(
        bgcolor=colors.ORANGE_100 if es_pendiente else colors.GREEN_100,
        border_radius=6,
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        content=ft.Text(
            "En cocina" if es_pendiente else "Completado",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=colors.DEEP_ORANGE_900 if es_pendiente else colors.GREEN_800,
        ),
    )

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"Pedido #{pedido_id}",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLACK87,
                    ),
                    _crear_insignia_servicio(es_mesa),
                ],
            ),
            ft.Row(
                spacing=6,
                controls=[
                    insignia_estado,
                    ft.Text(
                        hora_str,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLUE_GREY_600,
                    ),
                ],
            ),
        ],
    )

    controles_tarjeta: list[ft.Control] = [
        fila_encabezado,
        *_crear_bloques_platos(pedido, tamano_item=15, tamano_detalle=13),
        ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.ElevatedButton(
                    text="Editar pedido",
                    icon=icons.EDIT,
                    bgcolor=colors.BLUE_700,
                    color=colors.WHITE,
                    height=38,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    on_click=lambda _e, pid=pedido_id: on_editar(pid),
                ),
            ],
        ),
    ]

    return ft.Container(
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(14),
        margin=ft.margin.symmetric(vertical=6, horizontal=2),
        border_radius=14,
        border=ft.border.all(1.5, colors.BLUE_GREY_200),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=with_opacity(0.10, colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        content=ft.Column(spacing=10, controls=controles_tarjeta),
    )
