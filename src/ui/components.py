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
    GRADIENTE_BOTON,
    GRADIENTE_ELIMINAR,
    GRADIENTE_PRIMARIO,
    GRADIENTE_REALIZAR,
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
            ft.NavigationBarDestination(icon=ft.icons.LIST_ALT, label="Ver Pedidos"),
            ft.NavigationBarDestination(icon=ft.icons.ADD_SHOPPING_CART, label="Ordenar"),
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
            color=ft.colors.with_opacity(0.2, ft.colors.BLACK),
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
                            ft.icons.RESTAURANT,
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
                        ft.icons.CHEVRON_RIGHT_ROUNDED,
                        color=ft.colors.WHITE,
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
    icon_name: str = ft.icons.FASTFOOD,
) -> ft.Container:
    """Crea el encabezado con gradiente para los bloques desplegables (ExpansionTile)."""
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
                        ft.Icon(icon_name, size=26, color=COLOR_ICONO_PRINCIPAL),
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


def create_styled_button_opciones(button_text: str) -> ft.Container:
    """Contenido de botón mediano para 'Opciones' y 'Agregar a Pedido'."""
    return boton_gradiente(button_text, GRADIENTE_BOTON, padding_h=12, padding_v=8)


def create_styled_button_eliminar(button_text: str) -> ft.Container:
    """Contenido de botón rojo para deshacer la última línea del resumen."""
    return boton_gradiente(button_text, GRADIENTE_ELIMINAR, padding_h=10, padding_v=8)


def create_styled_button_realizar(button_text: str) -> ft.Container:
    """Contenido de botón verde para confirmar y enviar el pedido."""
    return boton_gradiente(button_text, GRADIENTE_REALIZAR, padding_h=10, padding_v=8)


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
    """Crea el campo de texto de solo lectura que muestra la cantidad seleccionada."""
    return ft.TextField(
        value=str(valor_inicial),
        width=75,
        border_radius=12,
        border_color=COLOR_BORDE_INPUT,
        focused_border_color=COLOR_BOTON_CONTADOR,
        disabled=True,
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
        shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        expand=expandir,
    )

    btn_restar = ft.IconButton(
        ft.Icons.REMOVE,
        on_click=on_restar,
        icon_size=20,
        icon_color="white",
        expand=expandir,
        style=estilo_boton_icono,
    )

    btn_sumar = ft.IconButton(
        ft.Icons.ADD,
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
