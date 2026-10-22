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
    posicion_cola: int | None = None,
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

    controles_izquierda: list[ft.Control] = []
    if posicion_cola is not None:
        controles_izquierda.append(
            ft.Container(
                bgcolor=colors.BLUE_GREY_900,
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=7, vertical=2),
                content=ft.Text(
                    f"{posicion_cola}°",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=colors.WHITE,
                ),
            )
        )

    controles_izquierda.extend(
        [
            ft.Text(
                f"#{pedido_id}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            _crear_insignia_servicio(es_mesa),
        ]
    )

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controles_izquierda,
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
    page: ft.Page,
    pedido: "Pedido",
    on_editar: Callable[[int], None],
    posicion_cola: int | None = None,
    total_en_cola: int = 0,
    on_arrastrar_a_destino: Callable[[int, int], None] | None = None,
    on_mover_paso: Callable[[int, int], None] | None = None,
) -> ft.Container:
    """
    Tarjeta responsiva para la sección 'Editar Pedidos' (`/editar-pedidos`) de los meseros.
    En los pedidos activos ('En orden'), permite reordenarlos arrastrando y soltando
    una tarjeta sobre otra (`Draggable` + `DragTarget`) o con los botones de posición.
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

    controles_izquierda: list[ft.Control] = []
    if es_pendiente and posicion_cola is not None:
        controles_izquierda.extend(
            [
                ft.Icon(
                    icons.DRAG_INDICATOR,
                    size=20,
                    color=colors.BLUE_GREY_500,
                    tooltip="Arrastra esta tarjeta para cambiar su orden",
                ),
                ft.Container(
                    bgcolor=colors.BLUE_GREY_900,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=7, vertical=2),
                    content=ft.Text(
                        f"{posicion_cola}°",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=colors.WHITE,
                    ),
                ),
            ]
        )

    controles_izquierda.extend(
        [
            ft.Text(
                f"#{pedido_id}",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            _crear_insignia_servicio(es_mesa),
        ]
    )

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controles_izquierda,
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

    controles_pie_izquierda: list[ft.Control] = []
    if es_pendiente and posicion_cola is not None and on_mover_paso is not None and total_en_cola > 1:
        controles_pie_izquierda.extend(
            [
                ft.IconButton(
                    icon=icons.ARROW_BACK_ROUNDED,
                    icon_size=16,
                    icon_color=colors.BLUE_GREY_800,
                    bgcolor=colors.BLUE_GREY_100,
                    width=32,
                    height=32,
                    disabled=posicion_cola <= 1,
                    tooltip="Subir prioridad (aparecer antes)",
                    on_click=lambda _e, pid=pedido_id: on_mover_paso(pid, -1),
                ),
                ft.IconButton(
                    icon=icons.ARROW_FORWARD_ROUNDED,
                    icon_size=16,
                    icon_color=colors.BLUE_GREY_800,
                    bgcolor=colors.BLUE_GREY_100,
                    width=32,
                    height=32,
                    disabled=posicion_cola >= total_en_cola,
                    tooltip="Bajar prioridad (aparecer después)",
                    on_click=lambda _e, pid=pedido_id: on_mover_paso(pid, +1),
                ),
            ]
        )

    fila_pie = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(spacing=4, controls=controles_pie_izquierda),
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
    )

    contenedor_visual_tarjeta = ft.Container(
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
        content=ft.Column(
            spacing=8,
            controls=[
                fila_encabezado,
                _crear_grilla_platos(pedido, tamano_item=14),
                fila_pie,
            ],
        ),
    )

    if not es_pendiente or on_arrastrar_a_destino is None:
        contenedor_visual_tarjeta.col = columnas_responsivas
        contenedor_visual_tarjeta.data = pedido_id
        return contenedor_visual_tarjeta

    # Vista flotante compacta mientras se arrastra la tarjeta
    feedback_arrastre = ft.Container(
        width=230,
        bgcolor=colors.ORANGE_700,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border_radius=10,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=10,
            color=with_opacity(0.35, colors.BLACK),
        ),
        content=ft.Row(
            spacing=8,
            tight=True,
            controls=[
                ft.Icon(icons.DRAG_INDICATOR, color=colors.WHITE, size=20),
                ft.Text(
                    f"Moviendo Pedido #{pedido_id}",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=colors.WHITE,
                ),
            ],
        ),
    )

    draggable = ft.Draggable(
        group="cola_pedidos_cocina",
        data=str(pedido_id),
        content=contenedor_visual_tarjeta,
        content_feedback=feedback_arrastre,
    )

    def al_entrar_arrastre(_e: ft.DragTargetEvent) -> None:
        contenedor_visual_tarjeta.border = ft.border.all(3, colors.BLUE_700)
        contenedor_visual_tarjeta.bgcolor = colors.BLUE_50
        page.update()

    def al_salir_arrastre(_e: ft.DragTargetEvent) -> None:
        contenedor_visual_tarjeta.border = ft.border.all(1.5, colors.BLUE_GREY_200)
        contenedor_visual_tarjeta.bgcolor = colors.WHITE
        page.update()

    def al_soltar_en_destino(e: ft.DragTargetAcceptEvent) -> None:
        contenedor_visual_tarjeta.border = ft.border.all(1.5, colors.BLUE_GREY_200)
        contenedor_visual_tarjeta.bgcolor = colors.WHITE
        try:
            ctrl_origen = page.get_control(e.src_id)
            id_origen = int(ctrl_origen.data)
            if id_origen != pedido_id:
                on_arrastrar_a_destino(id_origen, pedido_id)
                return
        except Exception:
            pass
        page.update()

    return ft.Container(
        col=columnas_responsivas,
        data=pedido_id,
        content=ft.DragTarget(
            group="cola_pedidos_cocina",
            content=draggable,
            on_will_accept=al_entrar_arrastre,
            on_leave=al_salir_arrastre,
            on_accept=al_soltar_en_destino,
        ),
    )
