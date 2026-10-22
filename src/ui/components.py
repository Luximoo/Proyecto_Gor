"""Componentes visuales reutilizables de la interfaz."""

from typing import Callable
import flet as ft

from ui.theme import (
    COLOR_BORDE_INPUT,
    COLOR_BOTON_CIRCULAR,
    COLOR_BOTON_CONTADOR,
    COLOR_ETIQUETA_GORDITA,
    COLOR_ICONO_PRINCIPAL,
    COLOR_PUNTO_DECORATIVO,
    COLOR_TEXTO_BOTON,
    COLOR_TEXTO_ETIQUETA,
    COLOR_TEXTO_PRIMARIO,
    COLOR_TEXTO_TERCIARIO,
    GRADIENTE_AGREGAR,
    GRADIENTE_BOTON,
    GRADIENTE_ELIMINAR,
    GRADIENTE_PRIMARIO,
    GRADIENTE_REALIZAR,
    colors,
    icons,
    with_opacity,
)

RUTAS_NAVEGACION = {
    0: "/home",
    1: "/Pedidos",
}


def _cambiar_vista(page: ft.Page, e: ft.ControlEvent) -> None:
    """Cambia la ruta activa según el índice seleccionado en la barra de navegación."""
    ruta_destino = RUTAS_NAVEGACION.get(e.control.selected_index, "/home")
    if page.route != ruta_destino:
        page.go(ruta_destino)


def crear_navegacion(page: ft.Page, selected_index: int | None = None) -> ft.NavigationBar:
    """Crea la barra de navegación inferior marcando la pestaña actual."""
    if selected_index is None:
        selected_index = 1 if page.route == "/Pedidos" else 0

    return ft.NavigationBar(
        selected_index=selected_index,
        destinations=[
            ft.NavigationBarDestination(icon=icons.LIST_ALT, label="Ver Pedidos"),
            ft.NavigationBarDestination(icon=icons.ADD_SHOPPING_CART, label="Ordenar"),
        ],
        on_change=lambda e: _cambiar_vista(page, e),
    )


def create_info_card(
    order_id: int,
    description: str,
    on_complete_callback: Callable[[int], None],
    title: str | None = None,
) -> ft.Container:
    """Crea la tarjeta visual de un pedido activo para el monitor de cocina."""
    return ft.Container(
        data=order_id,
        width=450,
        padding=ft.padding.all(20),
        margin=ft.margin.symmetric(vertical=10, horizontal=20),
        border_radius=ft.border_radius.all(15),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=GRADIENTE_PRIMARIO,
        ),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=with_opacity(0.2, colors.BLACK),
            offset=ft.Offset(5, 5),
        ),
        content=ft.ResponsiveRow(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Sección Izquierda (Icono y decoración)
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(
                            icons.RESTAURANT,
                            size=40,
                            color=COLOR_ICONO_PRINCIPAL,
                        ),
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Container(
                                    width=8,
                                    height=8,
                                    border_radius=4,
                                    bgcolor=COLOR_PUNTO_DECORATIVO,
                                ),
                                ft.Container(
                                    width=12,
                                    height=12,
                                    border_radius=6,
                                    bgcolor=COLOR_PUNTO_DECORATIVO,
                                ),
                            ],
                        ),
                    ],
                    col={"sm": 2, "md": 2},
                ),
                # Sección Central (Detalle del pedido y número de orden)
                ft.Column(
                    controls=[
                        ft.Text(
                            description,
                            weight=ft.FontWeight.BOLD,
                            size=22,
                            color=COLOR_TEXTO_PRIMARIO,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            title or f"Numero de orden {order_id}",
                            size=16,
                            color=COLOR_TEXTO_TERCIARIO,
                            text_align=ft.TextAlign.CENTER,
                            italic=True,
                        ),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    col={"sm": 8, "md": 8},
                ),
                # Sección Derecha (Botón de completar pedido)
                ft.Container(
                    content=ft.Icon(
                        icons.CHEVRON_RIGHT_ROUNDED,
                        color=colors.WHITE,
                        size=24,
                    ),
                    width=45,
                    height=45,
                    bgcolor=COLOR_BOTON_CIRCULAR,
                    border_radius=22.5,
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda _e, oid=order_id: on_complete_callback(oid),
                    col={"sm": 2, "md": 2},
                ),
            ],
        ),
    )


def create_custom_tile_header(
    title_text: str,
    icon_name: str | None = None,
) -> ft.Container:
    """Crea el encabezado con gradiente para los bloques desplegables (ExpansionTile)."""
    icono = icon_name or icons.FASTFOOD
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        border_radius=ft.border_radius.all(10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=GRADIENTE_PRIMARIO,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(icono, size=26, color=COLOR_ICONO_PRINCIPAL),
                        ft.Column(
                            spacing=3,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=6,
                                    height=6,
                                    border_radius=3,
                                    bgcolor=COLOR_PUNTO_DECORATIVO,
                                ),
                                ft.Container(
                                    width=9,
                                    height=9,
                                    border_radius=4.5,
                                    bgcolor=COLOR_PUNTO_DECORATIVO,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Text(
                    title_text,
                    weight=ft.FontWeight.BOLD,
                    size=15,
                    color=COLOR_TEXTO_PRIMARIO,
                    expand=True,
                ),
            ],
        ),
    )


def boton_gradiente(
    button_text: str,
    colores_gradiente: list[str] | None = None,
    padding_h: int = 12,
    padding_v: int = 8,
) -> ft.Container:
    """
    Crea el contenedor estilizado con gradiente para el interior de un botón.
    Unifica las antiguas funciones `create_styled_button*`.
    """
    colores = colores_gradiente or GRADIENTE_BOTON
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=padding_h, vertical=padding_v),
        border_radius=ft.border_radius.all(12),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=colores,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text(
                    button_text,
                    weight=ft.FontWeight.BOLD,
                    size=15,
                    color=COLOR_TEXTO_BOTON,
                ),
            ],
        ),
    )


def create_styled_button(button_text: str) -> ft.Container:
    """Contenido de botón grande para complementos en el BottomSheet."""
    return boton_gradiente(button_text, GRADIENTE_BOTON, padding_h=24, padding_v=16)


def create_styled_button_agregar(button_text: str) -> ft.Container:
    """Contenido de botón para 'Agregar a Pedido' con gradiente azul profesional."""
    return boton_gradiente(button_text, GRADIENTE_AGREGAR, padding_h=14, padding_v=10)


def create_styled_button_opciones(button_text: str) -> ft.Container:
    """Contenido de botón mediano para 'Opciones'."""
    return boton_gradiente(button_text, GRADIENTE_BOTON, padding_h=12, padding_v=8)


def create_styled_button_eliminar(button_text: str) -> ft.Container:
    """Contenido de botón rojo para deshacer la última línea del resumen."""
    return boton_gradiente(button_text, GRADIENTE_ELIMINAR, padding_h=10, padding_v=8)


def create_styled_button_realizar(button_text: str) -> ft.Container:
    """Contenido de botón verde para confirmar y enviar el pedido."""
    return boton_gradiente(button_text, GRADIENTE_REALIZAR, padding_h=10, padding_v=8)


def crear_boton_gradiente(
    contenido_gradiente: ft.Container,
    on_click: Callable[[ft.ControlEvent], None],
    expandir: bool = False,
) -> ft.ElevatedButton:
    """Crea un ElevatedButton sin padding ni fondo por defecto para que el gradiente encaje limpio."""
    return ft.ElevatedButton(
        content=contenido_gradiente,
        on_click=on_click,
        expand=expandir,
        style=ft.ButtonStyle(
            padding=ft.padding.all(0),
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor=colors.TRANSPARENT,
            shadow_color=colors.TRANSPARENT,
            elevation=2,
        ),
    )


def crear_contenedor_bottom_sheet(columna_opciones: ft.Column) -> ft.Container:
    """Envuelve la columna de opciones de un BottomSheet con el estilo visual del tema."""
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        border_radius=ft.border_radius.all(10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=GRADIENTE_PRIMARIO,
        ),
        content=columna_opciones,
    )


def crear_campo_cantidad(valor_inicial: int = 0, expandir: bool = False) -> ft.TextField:
    """Crea el campo de texto de cantidad: de solo lectura, centrado, con texto negro nítido."""
    return ft.TextField(
        value=str(valor_inicial),
        width=65,
        height=45,
        text_align=ft.TextAlign.CENTER,
        text_size=18,
        text_style=ft.TextStyle(
            weight=ft.FontWeight.BOLD,
            color=colors.BLACK87,
        ),
        bgcolor=colors.WHITE,
        border_radius=12,
        border_color=COLOR_BORDE_INPUT,
        focused_border_color=COLOR_BOTON_CONTADOR,
        read_only=True,
        content_padding=ft.padding.symmetric(vertical=8, horizontal=4),
        expand=expandir,
    )


def crear_fila_guiso(
    nombre_guiso: str,
    campo_cantidad: ft.TextField,
    on_restar: Callable[[ft.ControlEvent], None],
    on_sumar: Callable[[ft.ControlEvent], None],
    color_etiqueta: str = COLOR_ETIQUETA_GORDITA,
    expandir: bool = False,
) -> ft.Row:
    """Crea la fila `[Guiso] [-] [Cantidad] [+]` para un guisado."""
    estilo_boton_icono = ft.ButtonStyle(
        bgcolor=COLOR_BOTON_CONTADOR,
        shape=ft.RoundedRectangleBorder(radius=12),
        elevation=3,
        padding=ft.padding.all(10),
    )

    etiqueta = ft.Container(
        content=ft.Text(
            nombre_guiso,
            size=16,
            weight=ft.FontWeight.BOLD,
            color=COLOR_TEXTO_ETIQUETA,
        ),
        width=120,
        alignment=ft.alignment.center_left,
        padding=ft.padding.symmetric(horizontal=15, vertical=10),
        bgcolor=color_etiqueta,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=colors.BLACK12),
        expand=expandir,
    )

    btn_restar = ft.IconButton(
        icons.REMOVE,
        on_click=on_restar,
        icon_size=20,
        icon_color="white",
        expand=expandir,
        style=estilo_boton_icono,
    )

    btn_sumar = ft.IconButton(
        icons.ADD,
        on_click=on_sumar,
        icon_size=20,
        icon_color="white",
        expand=expandir,
        style=estilo_boton_icono,
    )

    return ft.Row(
        expand=expandir,
        alignment=ft.MainAxisAlignment.START,
        controls=[etiqueta, btn_restar, campo_cantidad, btn_sumar],
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
            lineas_plato.append(
                ft.Column(spacing=1, controls=controles_item)
            )

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
