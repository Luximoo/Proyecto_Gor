"""Componentes visuales reutilizables de la interfaz."""

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
    """Crea la barra de navegación inferior marcando la pestaña actual."""
    if selected_index is None:
        es_vista_pedido = page.route == "/Pedidos" or page.route.startswith("/pedido")
        selected_index = 1 if es_vista_pedido else 0

    return ft.NavigationBar(
        selected_index=selected_index,
        destinations=[
            ft.NavigationBarDestination(icon=icons.LIST_ALT, label="Ver Pedidos"),
            ft.NavigationBarDestination(icon=icons.ADD_SHOPPING_CART, label="Ordenar"),
        ],
        on_change=lambda e: _cambiar_vista(page, e, on_intentar_navegar),
    )


def crear_tarjeta_pedido_cocina(
    pedido: "Pedido",
    on_editar: Callable[[int], None],
    on_completar: Callable[[int], None] | None = None,
) -> ft.Container:
    """
    Crea la tarjeta visual de un `Pedido` estructurada por platos para el monitor de cocina.
    Muestra número de pedido, insignia MESA / PARA LLEVAR, etiqueta MODIFICADO (si version > 1),
    hora, desglose por platos y botones de Editar y Completar.
    """
    from domain.modelos import EstadoPedido, TipoServicio

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    es_pendiente = pedido.estado == EstadoPedido.PENDIENTE
    fue_modificado = pedido.version > 1

    # Hora legible
    marca_tiempo = pedido.updated_at or pedido.created_at
    hora_str = marca_tiempo.strftime("%H:%M") if marca_tiempo else ""

    # Insignia de tipo de servicio (Mesa vs Para llevar)
    insignia_servicio = ft.Container(
        bgcolor=colors.BLUE_700 if es_mesa else colors.DEEP_ORANGE_700,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        content=ft.Row(
            spacing=4,
            tight=True,
            controls=[
                ft.Icon(
                    icons.RESTAURANT if es_mesa else icons.SHOPPING_BAG,
                    size=14,
                    color=colors.WHITE,
                ),
                ft.Text(
                    "MESA" if es_mesa else "PARA LLEVAR",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=colors.WHITE,
                ),
            ],
        ),
    )

    # Encabezado principal de la tarjeta
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
                    insignia_servicio,
                ],
            ),
            ft.Text(
                hora_str,
                size=13,
                weight=ft.FontWeight.BOLD,
                color=colors.BLUE_GREY_600,
            ),
        ],
    )

    controles_tarjeta: list[ft.Control] = [fila_encabezado]

    # Etiqueta MODIFICADO cuando version > 1
    if fue_modificado:
        controles_tarjeta.append(
            ft.Container(
                bgcolor=colors.AMBER_300,
                border=ft.border.all(1, colors.AMBER_800),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                content=ft.Row(
                    spacing=5,
                    tight=True,
                    controls=[
                        ft.Icon(icons.AUTORENEW, size=14, color=colors.BLACK87),
                        ft.Text(
                            f"MODIFICADO (edición #{pedido.version - 1})",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLACK87,
                        ),
                    ],
                ),
            )
        )

    # Bloques por cada plato del pedido
    for plato in pedido.platos:
        if plato.esta_vacio:
            continue

        lineas_plato: list[ft.Control] = [
            ft.Container(
                bgcolor=colors.ORANGE_100,
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            f"── Plato {plato.numero} ──",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.DEEP_ORANGE_900,
                        ),
                        ft.Text(
                            f"{plato.total_piezas} pzs",
                            size=12,
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
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK87,
                )
            ]
            if detalle:
                controles_item.append(
                    ft.Container(
                        padding=ft.padding.only(left=14),
                        content=ft.Text(
                            detalle,
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.RED_800,
                        ),
                    )
                )
            lineas_plato.append(ft.Column(spacing=1, controls=controles_item))

        controles_tarjeta.append(
            ft.Container(
                bgcolor=colors.BLUE_GREY_50,
                border_radius=8,
                padding=ft.padding.all(8),
                content=ft.Column(spacing=5, controls=lineas_plato),
            )
        )

    # Pie de tarjeta con botones de Editar y Listo
    controles_acciones: list[ft.Control] = [
        ft.OutlinedButton(
            text="Editar",
            icon=icons.EDIT,
            style=ft.ButtonStyle(
                color=colors.BLUE_GREY_800,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _e, pid=pedido_id: on_editar(pid),
        )
    ]

    if es_pendiente and on_completar is not None:
        controles_acciones.append(
            ft.ElevatedButton(
                text="Listo",
                icon=icons.CHECK_CIRCLE,
                bgcolor=colors.GREEN_700,
                color=colors.WHITE,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=lambda _e, pid=pedido_id: on_completar(pid),
            )
        )
    else:
        controles_acciones.append(
            ft.Container(
                bgcolor=colors.GREEN_100,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(icons.CHECK, size=15, color=colors.GREEN_800),
                        ft.Text(
                            "Completado",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=colors.GREEN_800,
                        ),
                    ],
                ),
            )
        )

    controles_tarjeta.append(
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controles_acciones,
        )
    )

    color_borde = (
        colors.AMBER_700
        if fue_modificado and es_pendiente
        else (colors.ORANGE_400 if es_pendiente else colors.GREEN_300)
    )

    return ft.Container(
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(14),
        margin=ft.margin.symmetric(vertical=6, horizontal=2),
        border_radius=14,
        border=ft.border.all(2, color_borde),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=6,
            color=with_opacity(0.12, colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
        content=ft.Column(spacing=10, controls=controles_tarjeta),
    )
