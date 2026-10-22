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
    from domain.modelos import Item, Pedido, Plato

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
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        content=ft.Row(
            spacing=5,
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


def _crear_fila_item_compacta(item: "Item", tamano_fuente: int = 16) -> ft.Container:
    """
    Renderiza un platillo con un badge de cantidad (`2×`), su nombre y etiquetas
    compactas para sus modificadores (`+ Queso`, `sin Cebolla`) sin desperdiciar espacio.
    """
    from domain.modelos import TipoModificador

    chips_modificadores: list[ft.Control] = []
    for mod in item.modificadores:
        es_extra = mod.tipo == TipoModificador.EXTRA
        chips_modificadores.append(
            ft.Container(
                bgcolor=colors.RED_50 if not es_extra else colors.AMBER_100,
                border=ft.border.all(
                    1,
                    colors.RED_400 if not es_extra else colors.AMBER_700,
                ),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                content=ft.Text(
                    mod.formatear(),
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=colors.RED_900 if not es_extra else colors.DEEP_ORANGE_900,
                ),
            )
        )

    if item.nota:
        chips_modificadores.append(
            ft.Container(
                bgcolor=colors.BLUE_50,
                border=ft.border.all(1, colors.BLUE_400),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                content=ft.Text(
                    f"Nota: {item.nota}",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLUE_900,
                ),
            )
        )

    fila_principal = ft.Row(
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                bgcolor=colors.ORANGE_700 if item.cantidad > 1 else colors.BLUE_GREY_700,
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=7, vertical=2),
                content=ft.Text(
                    f"{item.cantidad}×",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=colors.WHITE,
                ),
            ),
            ft.Text(
                f"{item.producto} {item.guiso}",
                size=tamano_fuente,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
                expand=True,
            ),
        ],
    )

    if not chips_modificadores:
        return ft.Container(
            padding=ft.padding.symmetric(vertical=2),
            content=fila_principal,
        )

    return ft.Container(
        padding=ft.padding.symmetric(vertical=2),
        content=ft.Column(
            spacing=4,
            controls=[
                fila_principal,
                ft.Container(
                    padding=ft.padding.only(left=34),
                    content=ft.Row(
                        wrap=True,
                        spacing=5,
                        run_spacing=4,
                        controls=chips_modificadores,
                    ),
                ),
            ],
        ),
    )


def _crear_grilla_platos(
    pedido: "Pedido",
    tamano_item: int = 16,
) -> ft.ResponsiveRow:
    """
    Organiza los platos del pedido en una cuadrícula responsiva:
    - Si el pedido tiene 1 solo plato: ocupa todo el ancho de la tarjeta (12 cols).
    - Si el pedido tiene 2 o más platos: en pantallas medianas/grandes se colocan
      lado a lado (6 cols cada uno) para aprovechar el espacio horizontal.
    """
    platos_activos: list[Plato] = [p for p in pedido.platos if not p.esta_vacio]
    tiene_varios_platos = len(platos_activos) > 1
    col_plato = {"xs": 12, "md": 6} if tiene_varios_platos else {"xs": 12}

    controles_platos: list[ft.Control] = []
    for plato in platos_activos:
        filas_items = [
            _crear_fila_item_compacta(item, tamano_fuente=tamano_item)
            for item in plato.items
        ]

        encabezado_plato = ft.Container(
            bgcolor=colors.ORANGE_100,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        f"Plato {plato.numero}",
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

        controles_platos.append(
            ft.Container(
                col=col_plato,
                bgcolor=colors.BLUE_GREY_50,
                border_radius=8,
                border=ft.border.all(1, colors.BLUE_GREY_100),
                padding=ft.padding.all(8),
                content=ft.Column(
                    spacing=5,
                    controls=[encabezado_plato, *filas_items],
                ),
            )
        )

    return ft.ResponsiveRow(spacing=8, run_spacing=8, controls=controles_platos)


def crear_tarjeta_pedido_cocina(
    pedido: "Pedido",
    on_completar: Callable[[int], None],
) -> ft.Container:
    """
    Tarjeta compacta y multi-columna para el monitor de cocina (`/home`).
    En monitores grandes se acomodan hasta 3 o 4 pedidos por fila para aprovechar
    toda la pantalla sin dejar espacio vacío.
    """
    from domain.modelos import TipoServicio

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    fue_modificado = pedido.version > 1
    platos_no_vacios = [p for p in pedido.platos if not p.esta_vacio]
    tiene_varios_platos = len(platos_no_vacios) > 1

    # Si el pedido tiene varios platos, le damos el doble de ancho en monitor para mostrarlos lado a lado
    columnas_responsivas = (
        {"xs": 12, "sm": 12, "md": 8, "lg": 6}
        if tiene_varios_platos
        else {"xs": 12, "sm": 6, "md": 4, "lg": 3}
    )

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"#{pedido_id}",
                        size=20,
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
                height=36,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
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
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                content=ft.Row(
                    spacing=5,
                    tight=True,
                    controls=[
                        ft.Icon(icons.AUTORENEW, size=14, color=colors.BLACK87),
                        ft.Text(
                            "PEDIDO MODIFICADO",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLACK87,
                        ),
                    ],
                ),
            )
        )

    controles_tarjeta.append(_crear_grilla_platos(pedido, tamano_item=15))

    return ft.Container(
        col=columnas_responsivas,
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(12),
        border_radius=12,
        border=ft.border.all(2, colors.AMBER_700 if fue_modificado else colors.ORANGE_400),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=with_opacity(0.10, colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        content=ft.Column(spacing=8, controls=controles_tarjeta),
    )


def crear_tarjeta_pedido_mesero(
    pedido: "Pedido",
    on_editar: Callable[[int], None],
) -> ft.Container:
    """
    Tarjeta responsiva para la sección 'Editar Pedidos' (`/editar-pedidos`) de los meseros.
    """
    from domain.modelos import EstadoPedido, TipoServicio

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    es_pendiente = pedido.estado == EstadoPedido.PENDIENTE
    platos_no_vacios = [p for p in pedido.platos if not p.esta_vacio]
    tiene_varios_platos = len(platos_no_vacios) > 1

    columnas_responsivas = (
        {"xs": 12, "sm": 12, "md": 8, "lg": 6}
        if tiene_varios_platos
        else {"xs": 12, "sm": 6, "md": 4, "lg": 3}
    )

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
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"#{pedido_id}",
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
        _crear_grilla_platos(pedido, tamano_item=14),
        ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.ElevatedButton(
                    text="Editar pedido",
                    icon=icons.EDIT,
                    bgcolor=colors.BLUE_700,
                    color=colors.WHITE,
                    height=36,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _e, pid=pedido_id: on_editar(pid),
                ),
            ],
        ),
    ]

    return ft.Container(
        col=columnas_responsivas,
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(12),
        border_radius=12,
        border=ft.border.all(1.5, colors.BLUE_GREY_200),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=with_opacity(0.10, colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        content=ft.Column(spacing=8, controls=controles_tarjeta),
    )
