"""Vista de toma de pedidos para meseros (`/Pedidos`): platos, productos y envío a cocina."""

from __future__ import annotations

import logging
from typing import Callable

import flet as ft
import mysql.connector

from data.repositorio import cargar_catalogo, guardar_pedido
from domain.modelos import (
    Catalogo,
    ErrorValidacionDominio,
    Item,
    Pedido,
    Plato,
    TipoServicio,
    catalogo_por_defecto,
    formatear_pedido,
)
from ui.components import crear_navegacion
from ui.personalizacion import abrir_modal_personalizacion
from ui.theme import (
    COLOR_FONDO_PAGINA,
    colors,
    icons,
)


def _mostrar_aviso(page: ft.Page, mensaje: str, es_error: bool = False) -> None:
    """Muestra un SnackBar legible en la parte inferior de la pantalla."""
    snack = ft.SnackBar(
        content=ft.Text(
            mensaje,
            color=colors.WHITE,
            weight=ft.FontWeight.BOLD,
            size=14,
        ),
        bgcolor=colors.RED_700 if es_error else colors.GREEN_700,
        duration=2500,
    )
    try:
        page.open(snack)
    except Exception:
        page.snack_bar = snack
        snack.open = True
        page.update()


def _cargar_catalogo_seguro() -> Catalogo:
    """Obtiene el catálogo desde MySQL o usa el catálogo por defecto si hay fallo temporal."""
    try:
        return cargar_catalogo()
    except Exception as err:
        logging.warning(f"No se pudo cargar el catálogo desde BD, usando por defecto: {err}")
        return catalogo_por_defecto()


def view_realizar_pedido(
    page: ft.Page,
    on_abrir_personalizacion: Callable[[ft.Page, Catalogo, Plato, int, Callable[[], None]], None]
    | None = None,
) -> ft.View:
    """
    Construye la pantalla de toma de pedidos (`/Pedidos`) con:
    - Selector obligatorio de tipo de servicio (Mesa / Para llevar).
    - Pestañas dinámicas de platos (`Plato 1`, `Plato 2`, `+ Plato`).
    - Selector de producto (`Gordita`, `Sope`) y cuadrícula de guisos de 1 toque.
    - Lista interactiva del plato activo con `[−]`, `[+]` y `[✎]`.
    - Barra inferior con totales y confirmación antes de enviar.
    """
    catalogo = _cargar_catalogo_seguro()
    productos_disponibles = catalogo.nombres_productos or ["Gordita", "Sope"]

    estado_vista = {
        "pedido": Pedido(tipo_servicio=None),
        "plato_activo_num": 1,
        "producto_activo": productos_disponibles[0],
    }

    # Contenedores dinámicos que se refrescan al interactuar
    contenedor_servicio = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    fila_pestanas_platos = ft.Row(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    contenedor_productos = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    cuadricula_guisos = ft.ResponsiveRow(spacing=8, run_spacing=8)
    encabezado_plato_activo = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    lista_items_plato = ft.Column(spacing=8)
    barra_inferior_contenedor = ft.Container()

    def obtener_pedido() -> Pedido:
        return estado_vista["pedido"]

    def obtener_plato_activo() -> Plato:
        pedido = obtener_pedido()
        num = int(estado_vista["plato_activo_num"])
        try:
            return pedido.obtener_plato(num)
        except ErrorValidacionDominio:
            estado_vista["plato_activo_num"] = pedido.platos[0].numero
            return pedido.platos[0]

    # --- Acciones de estado ---

    def seleccionar_servicio(servicio: TipoServicio) -> None:
        obtener_pedido().tipo_servicio = servicio
        refrescar_todo()

    def seleccionar_plato(numero: int) -> None:
        estado_vista["plato_activo_num"] = numero
        refrescar_todo()

    def agregar_nuevo_plato(_e: ft.ControlEvent) -> None:
        nuevo = obtener_pedido().agregar_plato()
        estado_vista["plato_activo_num"] = nuevo.numero
        refrescar_todo()

    def eliminar_plato_actual(_e: ft.ControlEvent) -> None:
        pedido = obtener_pedido()
        num_actual = obtener_plato_activo().numero
        pedido.eliminar_plato(num_actual)
        estado_vista["plato_activo_num"] = pedido.platos[-1].numero
        refrescar_todo()

    def seleccionar_producto(nombre_prod: str) -> None:
        estado_vista["producto_activo"] = nombre_prod
        refrescar_todo()

    def tocar_guiso(nombre_guiso: str) -> None:
        producto = str(estado_vista["producto_activo"])
        plato = obtener_plato_activo()
        plato.agregar_item(
            Item(producto=producto, guiso=nombre_guiso, cantidad=1),
            catalogo,
        )
        refrescar_todo()

    def modificar_cantidad_item(indice: int, delta: int) -> None:
        plato = obtener_plato_activo()
        plato.cambiar_cantidad(indice, delta)
        refrescar_todo()

    def abrir_editor_item(indice: int) -> None:
        plato = obtener_plato_activo()
        callback_editor = on_abrir_personalizacion or abrir_modal_personalizacion
        callback_editor(page, catalogo, plato, indice, refrescar_todo)

    def confirmar_envio(_e: ft.ControlEvent) -> None:
        pedido = obtener_pedido()
        try:
            pedido.validar_para_envio(catalogo)
        except ErrorValidacionDominio as err:
            _mostrar_aviso(page, str(err), es_error=True)
            return

        resumen_texto = formatear_pedido(pedido)

        def ejecutar_guardado(_ev: ft.ControlEvent) -> None:
            page.close(dialogo_confirmar)
            try:
                guardado = guardar_pedido(pedido, catalogo)
                _mostrar_aviso(
                    page,
                    f"Pedido #{guardado.id} ({guardado.tipo_servicio.etiqueta}) enviado a cocina",
                    es_error=False,
                )
                # Reiniciar para el siguiente pedido sin selección por defecto
                estado_vista["pedido"] = Pedido(tipo_servicio=None)
                estado_vista["plato_activo_num"] = 1
                refrescar_todo()
            except mysql.connector.Error as db_err:
                logging.error(f"Error de base de datos al guardar pedido: {db_err}")
                _mostrar_aviso(page, f"Error de BD: {db_err}", es_error=True)
            except Exception as exc:
                logging.error(f"Error inesperado al guardar pedido: {exc}")
                _mostrar_aviso(page, f"Error al enviar: {exc}", es_error=True)

        dialogo_confirmar = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar pedido", weight=ft.FontWeight.BOLD, size=18),
            content=ft.Container(
                width=300,
                padding=ft.padding.all(10),
                bgcolor=colors.BLUE_GREY_50,
                border_radius=10,
                content=ft.Text(
                    resumen_texto,
                    size=14,
                    color=colors.BLACK87,
                    weight=ft.FontWeight.W_500,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Revisar",
                    on_click=lambda _ev: page.close(dialogo_confirmar),
                ),
                ft.ElevatedButton(
                    "Confirmar y Enviar",
                    bgcolor=colors.GREEN_700,
                    color=colors.WHITE,
                    on_click=ejecutar_guardado,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialogo_confirmar)

    # --- Renderizado de secciones ---

    def renderizar_selector_servicio() -> None:
        actual = obtener_pedido().tipo_servicio
        opciones = [
            (TipoServicio.MESA, "Comer aquí (Mesa)", icons.RESTAURANT, colors.BLUE_700),
            (TipoServicio.LLEVAR, "Para llevar", icons.SHOPPING_BAG, colors.DEEP_ORANGE_700),
        ]
        controles: list[ft.Control] = []
        for serv, texto, icono, color_activo in opciones:
            seleccionado = actual == serv
            controles.append(
                ft.Container(
                    expand=True,
                    height=46,
                    bgcolor=color_activo if seleccionado else colors.WHITE,
                    border=ft.border.all(
                        2,
                        color_activo if seleccionado else colors.BLUE_GREY_200,
                    ),
                    border_radius=12,
                    ink=True,
                    on_click=lambda _e, s=serv: seleccionar_servicio(s),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Icon(
                                icono,
                                size=18,
                                color=colors.WHITE if seleccionado else colors.BLACK87,
                            ),
                            ft.Text(
                                texto,
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=colors.WHITE if seleccionado else colors.BLACK87,
                            ),
                        ],
                    ),
                )
            )
        contenedor_servicio.controls = controles

    def renderizar_pestanas_platos() -> None:
        pedido = obtener_pedido()
        num_activo = obtener_plato_activo().numero
        controles: list[ft.Control] = []

        for plato in pedido.platos:
            es_activo = plato.numero == num_activo
            piezas = plato.total_piezas
            etiqueta = f"Plato {plato.numero}" + (f" ({piezas})" if piezas > 0 else "")

            controles.append(
                ft.Container(
                    bgcolor=colors.ORANGE_700 if es_activo else colors.WHITE,
                    border=ft.border.all(
                        2,
                        colors.ORANGE_800 if es_activo else colors.BLUE_GREY_200,
                    ),
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=14, vertical=7),
                    ink=True,
                    on_click=lambda _e, n=plato.numero: seleccionar_plato(n),
                    content=ft.Text(
                        etiqueta,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=colors.WHITE if es_activo else colors.BLACK87,
                    ),
                )
            )

        # Botón "+ Plato"
        controles.append(
            ft.Container(
                bgcolor=colors.BLUE_50,
                border=ft.border.all(1.5, colors.BLUE_600),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=12, vertical=7),
                ink=True,
                on_click=agregar_nuevo_plato,
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(icons.ADD, size=16, color=colors.BLUE_700),
                        ft.Text(
                            "Plato",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.BLUE_700,
                        ),
                    ],
                ),
            )
        )
        fila_pestanas_platos.controls = controles

    def renderizar_selector_producto() -> None:
        prod_activo = str(estado_vista["producto_activo"])
        controles: list[ft.Control] = []

        for nombre_prod in productos_disponibles:
            es_activo = nombre_prod == prod_activo
            controles.append(
                ft.Container(
                    expand=True,
                    height=40,
                    bgcolor=colors.BLUE_GREY_800 if es_activo else colors.WHITE,
                    border=ft.border.all(
                        1.5,
                        colors.BLUE_GREY_800 if es_activo else colors.BLUE_GREY_200,
                    ),
                    border_radius=10,
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda _e, p=nombre_prod: seleccionar_producto(p),
                    content=ft.Text(
                        nombre_prod + "s",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=colors.WHITE if es_activo else colors.BLACK87,
                    ),
                )
            )
        contenedor_productos.controls = controles

    def renderizar_cuadricula_guisos() -> None:
        prod_activo = str(estado_vista["producto_activo"])
        reglas = catalogo.obtener_reglas(prod_activo)
        plato = obtener_plato_activo()

        # Contar cuántas piezas de cada guiso hay en el plato activo para ese producto
        conteo_por_guiso: dict[str, int] = {}
        for it in plato.items:
            if it.producto == prod_activo:
                conteo_por_guiso[it.guiso] = conteo_por_guiso.get(it.guiso, 0) + it.cantidad

        controles: list[ft.Control] = []
        for guiso in reglas.guisos_base:
            cantidad_actual = conteo_por_guiso.get(guiso, 0)
            tiene_items = cantidad_actual > 0

            controles.append(
                ft.Container(
                    col={"xs": 6, "sm": 4},
                    height=52,
                    bgcolor=colors.ORANGE_100 if tiene_items else colors.WHITE,
                    border=ft.border.all(
                        2 if tiene_items else 1,
                        colors.ORANGE_700 if tiene_items else colors.BLUE_GREY_200,
                    ),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    ink=True,
                    on_click=lambda _e, g=guiso: tocar_guiso(g),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                guiso,
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=colors.BLACK87,
                                expand=True,
                            ),
                            ft.Container(
                                visible=tiene_items,
                                bgcolor=colors.ORANGE_700,
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=7, vertical=2),
                                content=ft.Text(
                                    str(cantidad_actual),
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.WHITE,
                                ),
                            ),
                        ],
                    ),
                )
            )
        cuadricula_guisos.controls = controles

    def renderizar_lista_plato_activo() -> None:
        pedido = obtener_pedido()
        plato = obtener_plato_activo()

        mostrar_boton_borrar_plato = len(pedido.platos) > 1 or not plato.esta_vacio
        encabezado_plato_activo.controls = [
            ft.Text(
                f"PLATO {plato.numero} ({plato.total_piezas} pzs)",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=colors.BLUE_GREY_800,
            ),
            ft.TextButton(
                text="Quitar plato" if len(pedido.platos) > 1 else "Vaciar plato",
                icon=icons.DELETE_OUTLINE,
                visible=mostrar_boton_borrar_plato,
                style=ft.ButtonStyle(color=colors.RED_700),
                on_click=eliminar_plato_actual,
            ),
        ]

        if plato.esta_vacio:
            lista_items_plato.controls = [
                ft.Container(
                    padding=ft.padding.all(14),
                    bgcolor=colors.WHITE,
                    border_radius=10,
                    border=ft.border.all(1, colors.BLUE_GREY_100),
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        f"El Plato {plato.numero} está vacío. Toca un guiso arriba para agregar.",
                        size=13,
                        color=colors.BLACK54,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]
            return

        filas: list[ft.Control] = []
        for idx, item in enumerate(plato.items):
            detalle = item.formatear_detalle()
            textos_item: list[ft.Control] = [
                ft.Text(
                    item.formatear_titulo(),
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK87,
                )
            ]
            if detalle:
                textos_item.append(
                    ft.Text(
                        detalle,
                        size=12,
                        color=colors.DEEP_ORANGE_800,
                        weight=ft.FontWeight.W_500,
                    )
                )

            filas.append(
                ft.Container(
                    bgcolor=colors.WHITE,
                    border_radius=10,
                    border=ft.border.all(1, colors.BLUE_GREY_200),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=textos_item,
                            ),
                            ft.Row(
                                spacing=4,
                                tight=True,
                                controls=[
                                    ft.IconButton(
                                        icon=icons.REMOVE,
                                        icon_size=18,
                                        icon_color=colors.WHITE,
                                        bgcolor=colors.RED_600,
                                        width=34,
                                        height=34,
                                        on_click=lambda _e, i=idx: modificar_cantidad_item(i, -1),
                                    ),
                                    ft.IconButton(
                                        icon=icons.ADD,
                                        icon_size=18,
                                        icon_color=colors.WHITE,
                                        bgcolor=colors.BLUE_600,
                                        width=34,
                                        height=34,
                                        on_click=lambda _e, i=idx: modificar_cantidad_item(i, +1),
                                    ),
                                    ft.IconButton(
                                        icon=icons.EDIT,
                                        icon_size=18,
                                        icon_color=colors.WHITE,
                                        bgcolor=colors.BLUE_GREY_700,
                                        width=34,
                                        height=34,
                                        tooltip="Personalizar platillo",
                                        on_click=lambda _e, i=idx: abrir_editor_item(i),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )
        lista_items_plato.controls = filas

    def renderizar_barra_inferior() -> None:
        pedido = obtener_pedido()
        total_pzs = pedido.total_platillos
        total_platos = max(1, pedido.total_platos_con_items)

        tiene_servicio = pedido.tipo_servicio is not None
        tiene_items = total_pzs > 0
        listo_para_enviar = tiene_servicio and tiene_items

        if not tiene_servicio:
            texto_boton = "Elige Mesa o Llevar"
        elif not tiene_items:
            texto_boton = "Agrega platillos"
        else:
            texto_boton = "ENVIAR ▶"

        barra_inferior_contenedor.content = ft.Container(
            bgcolor=colors.WHITE,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=12,
            border=ft.border.all(1, colors.BLUE_GREY_200),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=1,
                        controls=[
                            ft.Text(
                                f"{total_pzs} platillo{'s' if total_pzs != 1 else ''}",
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=colors.BLACK87,
                            ),
                            ft.Text(
                                f"en {total_platos} plato{'s' if total_platos != 1 else ''}",
                                size=12,
                                color=colors.BLACK54,
                            ),
                        ],
                    ),
                    ft.ElevatedButton(
                        text=texto_boton,
                        bgcolor=colors.GREEN_700 if listo_para_enviar else colors.BLUE_GREY_200,
                        color=colors.WHITE if listo_para_enviar else colors.BLACK54,
                        disabled=not listo_para_enviar,
                        height=44,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=confirmar_envio,
                    ),
                ],
            ),
        )

    def refrescar_todo() -> None:
        renderizar_selector_servicio()
        renderizar_pestanas_platos()
        renderizar_selector_producto()
        renderizar_cuadricula_guisos()
        renderizar_lista_plato_activo()
        renderizar_barra_inferior()
        page.update()

    # Render inicial antes de devolver la vista
    renderizar_selector_servicio()
    renderizar_pestanas_platos()
    renderizar_selector_producto()
    renderizar_cuadricula_guisos()
    renderizar_lista_plato_activo()
    renderizar_barra_inferior()

    navegacion = crear_navegacion(page, selected_index=1)

    return ft.View(
        route="/Pedidos",
        controls=[
            ft.Text(
                "Tomar Pedido",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            contenedor_servicio,
            ft.Divider(height=4, color=colors.BLUE_GREY_100),
            fila_pestanas_platos,
            contenedor_productos,
            cuadricula_guisos,
            ft.Divider(height=8, color=colors.BLUE_GREY_100),
            encabezado_plato_activo,
            lista_items_plato,
            barra_inferior_contenedor,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=14,
        bgcolor=COLOR_FONDO_PAGINA,
    )


# Alias de compatibilidad
View_RealizarPedido = view_realizar_pedido
