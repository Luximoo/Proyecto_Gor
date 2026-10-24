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
    3: "/corte",
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
    Crea la barra de navegación inferior con 4 secciones:
    0: Cocina (/home)
    1: Ordenar (/Pedidos)
    2: Editar Pedidos (/editar-pedidos)
    3: Corte / Día (/corte)
    """
    if selected_index is None:
        ruta = page.route or "/home"
        if ruta == "/corte":
            selected_index = 3
        elif ruta == "/editar-pedidos" or ruta.startswith("/pedido/"):
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
            ft.NavigationBarDestination(icon=icons.ASSESSMENT_ROUNDED, label="Corte / Día"),
        ],
        on_change=lambda e: _cambiar_vista(page, e, on_intentar_navegar),
    )


def _crear_insignia_servicio(es_mesa: bool, grande: bool = False) -> ft.Container:
    """Insignia clara para distinguir MESA vs PARA LLEVAR."""
    return ft.Container(
        bgcolor=colors.BLUE_700 if es_mesa else colors.DEEP_ORANGE_700,
        border_radius=10 if grande else 8,
        padding=ft.padding.symmetric(
            horizontal=14 if grande else 10,
            vertical=6 if grande else 4,
        ),
        content=ft.Row(
            spacing=6 if grande else 5,
            tight=True,
            controls=[
                ft.Icon(
                    icons.RESTAURANT if es_mesa else icons.SHOPPING_BAG,
                    size=20 if grande else 14,
                    color=colors.WHITE,
                ),
                ft.Text(
                    "MESA" if es_mesa else "PARA LLEVAR",
                    size=17 if grande else 12,
                    weight=ft.FontWeight.BOLD,
                    color=colors.WHITE,
                ),
            ],
        ),
    )


def _crear_fila_item_compacta(
    item: "Item",
    tamano_fuente: int = 16,
    modo_cocina: bool = False,
) -> ft.Container:
    """
    Renderiza el platillo con su nombre completo corrido en una sola frase clara
    (ej. '2× Gordita Chicharron con Queso' o '1× Sope Chicharron sin Queso')
    para que en cocina se lea completo de corrido, todo en negro y con letra grande.
    """
    txt_con = item.texto_con_extras()
    txt_sin = item.texto_sin_ingredientes()
    es_gordita = item.producto.strip().lower() == "gordita"
    nombre_platillo = item.guiso if es_gordita else f"{item.producto} {item.guiso}"

    spans_texto: list[ft.TextSpan] = [
        ft.TextSpan(
            f"{item.cantidad}× {nombre_platillo}",
            ft.TextStyle(
                size=tamano_fuente,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK,
            ),
        )
    ]

    if txt_con:
        spans_texto.append(
            ft.TextSpan(
                f" {txt_con}",
                ft.TextStyle(
                    size=tamano_fuente,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK,
                ),
            )
        )

    if txt_sin:
        spans_texto.append(
            ft.TextSpan(
                f" {txt_sin}",
                ft.TextStyle(
                    size=tamano_fuente,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK,
                ),
            )
        )

    if item.nota:
        spans_texto.append(
            ft.TextSpan(
                f" ({item.nota})",
                ft.TextStyle(
                    size=tamano_fuente - (2 if modo_cocina else 1),
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK,
                ),
            )
        )

    fila_principal = ft.Row(
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                spans=spans_texto,
                color=colors.BLACK,
                expand=True,
            ),
        ],
    )

    return ft.Container(
        padding=ft.padding.symmetric(vertical=3 if modo_cocina else 2),
        content=fila_principal,
    )


def _crear_grilla_platos(
    pedido: "Pedido",
    tamano_item: int = 16,
    modo_cocina: bool = False,
    pantalla_completa: bool = False,
    precios: dict[str, float] | None = None,
) -> ft.ResponsiveRow:
    """
    Organiza los platos del pedido horizontalmente para evitar el scroll vertical:
    - Cuando un pedido grande está en `pantalla_completa=True`:
      - 2 platos -> 6 cols cada uno (2 lado a lado)
      - 3 platos -> 4 cols cada uno (3 lado a lado)
      - 4+ platos -> 3 cols en pantalla ancha / 6 cols en tablet (cuadrícula sin scroll)
    - Cuando hay 2 pedidos chicos lado a lado (`pantalla_completa=False`):
      - 1 plato -> 12 cols de su mitad
      - 2 platos chicos -> 6 cols cada uno para no crecer hacia abajo
    """
    from domain.modelos import formatear_moneda

    platos_activos: list[Plato] = [p for p in pedido.platos if not p.esta_vacio]
    num_platos = len(platos_activos)

    if modo_cocina and pantalla_completa:
        if num_platos == 1:
            col_plato = {"xs": 12}
        elif num_platos == 2:
            col_plato = {"xs": 12, "sm": 6, "md": 6}
        elif num_platos == 3:
            col_plato = {"xs": 12, "sm": 4, "md": 4}
        else:
            col_plato = {"xs": 12, "sm": 6, "md": 3, "lg": 3}
    elif modo_cocina:
        col_plato = {"xs": 12, "md": 6} if num_platos > 1 else {"xs": 12}
    else:
        col_plato = {"xs": 12, "md": 6} if num_platos > 1 else {"xs": 12}

    controles_platos: list[ft.Control] = []
    for plato in platos_activos:
        filas_items = [
            _crear_fila_item_compacta(
                item,
                tamano_fuente=tamano_item,
                modo_cocina=modo_cocina,
            )
            for item in plato.items
        ]

        texto_derecha_plato = f"{plato.total_piezas} pzs"

        encabezado_plato = ft.Container(
            bgcolor=colors.ORANGE_100,
            border_radius=7 if modo_cocina else 6,
            padding=ft.padding.symmetric(
                horizontal=10 if modo_cocina else 8,
                vertical=4 if modo_cocina else 3,
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        f"Plato {plato.numero}",
                        size=18 if modo_cocina else 13,
                        weight=ft.FontWeight.BOLD,
                        color=colors.DEEP_ORANGE_900,
                    ),
                    ft.Text(
                        texto_derecha_plato,
                        size=16 if modo_cocina else 12,
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
                border_radius=9 if modo_cocina else 8,
                border=ft.border.all(1.5 if modo_cocina else 1, colors.BLUE_GREY_200),
                padding=ft.padding.all(10 if modo_cocina else 8),
                content=ft.Column(
                    spacing=6 if modo_cocina else 5,
                    controls=[encabezado_plato, *filas_items],
                ),
            )
        )

    return ft.ResponsiveRow(
        spacing=8,
        run_spacing=8,
        controls=controles_platos,
    )


def crear_tarjeta_pedido_cocina(
    pedido: "Pedido",
    on_completar: Callable[[int], None],
    posicion_cola: int | None = None,
    pantalla_completa: bool = False,
    precios: dict[str, float] | None = None,
) -> ft.Container:
    """
    Tarjeta de alto contraste para el monitor de cocina en tablet (`/home`).
    - Si `pantalla_completa=True` (pedido de 3-4 platos o modo 1 solo): ocupa las 12 columnas
      y acomoda sus platos en paralelo para que todo quepa sin hacer scroll.
    - Si `pantalla_completa=False` (2 pedidos chicos): ocupa 6 columnas (mitad de pantalla)
      con letra grande y clara (`22px`).
    """
    from domain.modelos import TipoServicio, formatear_moneda

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    fue_modificado = pedido.version > 1
    total_pedido = (
        pedido.calcular_total(precios)
        if precios is not None
        else (pedido.total_cobrado if pedido.total_cobrado > 0 else pedido.calcular_total())
    )

    columnas_responsivas = (
        {"xs": 12}
        if pantalla_completa
        else {"xs": 12, "sm": 6, "md": 6, "lg": 6, "xl": 6}
    )

    num_orden_llegada = pedido.numero_pedido_mostrar
    controles_izquierda: list[ft.Control] = [
        ft.Container(
            bgcolor=colors.BLUE_GREY_900,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=9, vertical=3),
            content=ft.Text(
                f"{num_orden_llegada}°",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=colors.WHITE,
            ),
        ),
        ft.Text(
            pedido.nombre_mostrar,
            size=26,
            weight=ft.FontWeight.BOLD,
            color=colors.BLACK,
        ),
        _crear_insignia_servicio(es_mesa, grande=True),
    ]

    insignia_total_cocina = ft.Container(
        bgcolor=colors.GREEN_50,
        border=ft.border.all(2, colors.GREEN_700),
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=12, vertical=5),
        content=ft.Row(
            spacing=5,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Total:",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=colors.GREEN_900,
                ),
                ft.Text(
                    formatear_moneda(total_pedido),
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=colors.GREEN_900,
                ),
            ],
        ),
    )

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controles_izquierda,
            ),
            ft.Row(
                spacing=10,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    insignia_total_cocina,
                    ft.ElevatedButton(
                        content=ft.Row(
                            spacing=6,
                            tight=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(icons.CHECK_CIRCLE, size=22, color=colors.WHITE),
                                ft.Text(
                                    "Listo",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.WHITE,
                                ),
                            ],
                        ),
                        bgcolor=colors.GREEN_700,
                        color=colors.WHITE,
                        height=44,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.symmetric(horizontal=14, vertical=6),
                        ),
                        on_click=lambda _e, pid=pedido_id: on_completar(pid),
                    ),
                ],
            ),
        ],
    )

    controles_tarjeta: list[ft.Control] = [fila_encabezado]

    if fue_modificado:
        controles_tarjeta.append(
            ft.Container(
                bgcolor=colors.AMBER_300,
                border=ft.border.all(1.5, colors.AMBER_900),
                border_radius=7,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                content=ft.Row(
                    spacing=6,
                    tight=True,
                    controls=[
                        ft.Icon(icons.AUTORENEW, size=18, color=colors.BLACK),
                        ft.Text(
                            "PEDIDO MODIFICADO",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLACK,
                        ),
                    ],
                ),
            )
        )

    controles_tarjeta.append(
        _crear_grilla_platos(
            pedido,
            tamano_item=22,
            modo_cocina=True,
            pantalla_completa=pantalla_completa,
            precios=precios,
        )
    )

    return ft.Container(
        col=columnas_responsivas,
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(12),
        border_radius=12,
        border=ft.border.all(3, colors.AMBER_700 if fue_modificado else colors.ORANGE_500),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=6,
            color=with_opacity(0.12, colors.BLACK),
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
    en_pantalla_cocina: bool = False,
    on_mostrar_en_cocina: Callable[[int], None] | None = None,
    on_alternar_solo_en_cocina: Callable[[int, bool], None] | None = None,
    on_completar: Callable[[int], None] | None = None,
    precios: dict[str, float] | None = None,
) -> ft.Container:
    """
    Tarjeta responsiva para la sección 'Editar Pedidos' (`/editar-pedidos`) de los meseros.
    Permite al mesero elegir qué pedidos se muestran en la pantalla de Cocina, alternar si
    un pedido ocupa toda la pantalla (1 solo) o comparte con otro chico (2 a la par),
    y reordenar la fila.
    """
    from domain.modelos import EstadoPedido, TipoServicio, formatear_moneda

    pedido_id = pedido.id or 0
    es_mesa = pedido.tipo_servicio == TipoServicio.MESA
    es_pendiente = pedido.estado == EstadoPedido.PENDIENTE
    platos_no_vacios = [p for p in pedido.platos if not p.esta_vacio]
    tiene_varios_platos = len(platos_no_vacios) > 1
    total_pedido = (
        pedido.calcular_total(precios)
        if precios is not None
        else (pedido.total_cobrado if pedido.total_cobrado > 0 else pedido.calcular_total())
    )

    columnas_responsivas = (
        {"xs": 12, "sm": 12, "md": 8, "lg": 6}
        if tiene_varios_platos
        else {"xs": 12, "sm": 6, "md": 4, "lg": 3}
    )

    marca_tiempo = pedido.updated_at or pedido.created_at
    hora_str = marca_tiempo.strftime("%H:%M") if marca_tiempo else ""

    if es_pendiente:
        insignia_estado = ft.Container(
            bgcolor=colors.GREEN_700 if en_pantalla_cocina else colors.BLUE_GREY_100,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            content=ft.Row(
                spacing=4,
                tight=True,
                controls=[
                    ft.Icon(
                        icons.TV if en_pantalla_cocina else icons.SCHEDULE,
                        size=13,
                        color=colors.WHITE if en_pantalla_cocina else colors.BLUE_GREY_800,
                    ),
                    ft.Text(
                        "EN PANTALLA DE COCINA" if en_pantalla_cocina else "En espera",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=colors.WHITE if en_pantalla_cocina else colors.BLUE_GREY_800,
                    ),
                ],
            ),
        )
    else:
        insignia_estado = ft.Container(
            bgcolor=colors.GREEN_100,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            content=ft.Text(
                "Completado",
                size=11,
                weight=ft.FontWeight.BOLD,
                color=colors.GREEN_800,
            ),
        )

    num_orden_llegada = pedido.numero_pedido_mostrar
    controles_izquierda: list[ft.Control] = [
        ft.Container(
            bgcolor=colors.GREEN_800 if (es_pendiente and en_pantalla_cocina) else colors.BLUE_GREY_900,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=7, vertical=2),
            content=ft.Text(
                f"{num_orden_llegada}°",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=colors.WHITE,
            ),
        ),
        ft.Text(
            pedido.nombre_mostrar,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=colors.BLACK87,
        ),
        _crear_insignia_servicio(es_mesa),
    ]

    insignia_total_mesero = ft.Container(
        bgcolor=colors.GREEN_50,
        border=ft.border.all(1, colors.GREEN_600),
        border_radius=6,
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        content=ft.Text(
            f"Total: {formatear_moneda(total_pedido)}",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=colors.GREEN_900,
        ),
    )

    fila_encabezado = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controles_izquierda,
            ),
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    insignia_total_mesero,
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

    # Barra de control de pantalla de cocina para el mesero (elegir qué pedidos se ven y si 1 solo o 2 a la par)
    controles_pantalla_cocina: list[ft.Control] = []
    if es_pendiente:
        if pedido.es_grande_por_tamano:
            controles_pantalla_cocina.append(
                ft.Container(
                    bgcolor=colors.ORANGE_50,
                    border=ft.border.all(1, colors.ORANGE_300),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    content=ft.Text(
                        f"Pedido grande ({len(platos_no_vacios)} platos) · Se muestra 1 solo",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=colors.DEEP_ORANGE_900,
                    ),
                )
            )
        elif on_alternar_solo_en_cocina is not None:
            es_solo = bool(pedido.solo_en_cocina)
            controles_pantalla_cocina.append(
                ft.Container(
                    bgcolor=colors.PURPLE_50 if es_solo else colors.BLUE_50,
                    border=ft.border.all(
                        1,
                        colors.PURPLE_400 if es_solo else colors.BLUE_300,
                    ),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ink=True,
                    tooltip="Toca para cambiar entre ver este pedido solo o acompañado de otro chico",
                    on_click=lambda _e, pid=pedido_id, nuevo=(not es_solo): on_alternar_solo_en_cocina(
                        pid, nuevo
                    ),
                    content=ft.Row(
                        spacing=4,
                        tight=True,
                        controls=[
                            ft.Icon(
                                icons.FULLSCREEN if es_solo else icons.VIEW_COLUMN,
                                size=14,
                                color=colors.PURPLE_900 if es_solo else colors.BLUE_900,
                            ),
                            ft.Text(
                                "Modo: 1 solo en pantalla (Toca para 2 a la par)"
                                if es_solo
                                else "Pedido chico: Hasta 2 a la par (Toca para 1 solo)",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=colors.PURPLE_900 if es_solo else colors.BLUE_900,
                            ),
                        ],
                    ),
                )
            )

        if not en_pantalla_cocina and on_mostrar_en_cocina is not None:
            controles_pantalla_cocina.append(
                ft.ElevatedButton(
                    text="Mostrar en Cocina",
                    icon=icons.TV,
                    bgcolor=colors.GREEN_700,
                    color=colors.WHITE,
                    height=30,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.padding.symmetric(horizontal=10, vertical=2),
                    ),
                    on_click=lambda _e, pid=pedido_id: on_mostrar_en_cocina(pid),
                )
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

    controles_pie_derecha: list[ft.Control] = [
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
    ]
    if es_pendiente and on_completar is not None:
        controles_pie_derecha.append(
            ft.ElevatedButton(
                text="Listo",
                icon=icons.CHECK_CIRCLE,
                bgcolor=colors.GREEN_700,
                color=colors.WHITE,
                height=36,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=lambda _e, pid=pedido_id: on_completar(pid),
            )
        )

    fila_pie = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Row(spacing=4, controls=controles_pie_izquierda),
            ft.Row(spacing=6, tight=True, controls=controles_pie_derecha),
        ],
    )

    color_borde_mesero = (
        colors.GREEN_600
        if (es_pendiente and en_pantalla_cocina)
        else colors.BLUE_GREY_200
    )
    grosor_borde_mesero = 2.5 if (es_pendiente and en_pantalla_cocina) else 1.5

    controles_cuerpo_mesero: list[ft.Control] = [fila_encabezado]
    if controles_pantalla_cocina:
        controles_cuerpo_mesero.append(
            ft.Row(
                wrap=True,
                spacing=6,
                run_spacing=6,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controles_pantalla_cocina,
            )
        )
    controles_cuerpo_mesero.extend(
        [
            _crear_grilla_platos(pedido, tamano_item=14, precios=precios),
            fila_pie,
        ]
    )

    contenedor_visual_tarjeta = ft.Container(
        col=columnas_responsivas,
        data=pedido_id,
        bgcolor=colors.WHITE,
        padding=ft.padding.all(12),
        border_radius=12,
        border=ft.border.all(grosor_borde_mesero, color_borde_mesero),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=with_opacity(0.10, colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        content=ft.Column(
            spacing=8,
            controls=controles_cuerpo_mesero,
        ),
    )

    return contenedor_visual_tarjeta


def abrir_modal_cobro_pedido(
    page: ft.Page,
    pedido: "Pedido",
    precios: dict[str, float] | None,
    on_confirmar: Callable[[float, float, float], None],
) -> None:
    """
    Abre el diálogo modal de cobro para mostrar el Total a cobrar, permitir ingresar
    con cuánto paga el cliente, calcular automáticamente el cambio y confirmar 'Listo'.
    """
    from domain.modelos import formatear_moneda

    total_a_cobrar = pedido.calcular_total(precios)
    nombre_mostrar = pedido.nombre_mostrar

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
        on_confirmar(total_a_cobrar, pago_final, cambio_final)

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
