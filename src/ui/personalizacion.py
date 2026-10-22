"""BottomSheet de personalización de platillos (cambiar guiso, extras, sin, nota y separar pieza)."""

from __future__ import annotations

from typing import Callable

import flet as ft

from domain.modelos import (
    Catalogo,
    Item,
    Modificador,
    Plato,
    TipoModificador,
)
from ui.theme import COLOR_BORDE_INPUT, colors, icons


def abrir_modal_personalizacion(
    page: ft.Page,
    catalogo: Catalogo,
    plato: Plato,
    indice_item: int,
    on_guardar_callback: Callable[[], None],
) -> None:
    """
    Abre un BottomSheet interactivo para personalizar el `Item` en `plato.items[indice_item]`.
    Permite:
    - Cambiar el guiso base.
    - Agregar múltiples extras (Queso, Crema, otros guisos).
    - Marcar ingredientes a omitir ('Sin Cebolla', etc., solo si el producto lo permite).
    - Escribir una nota libre.
    - Separar 1 pieza cuando la cantidad es > 1 para personalizarla individualmente.
    """
    if not (0 <= indice_item < len(plato.items)):
        return

    item_original = plato.items[indice_item]
    reglas = catalogo.obtener_reglas(item_original.producto)

    # Estado local editable dentro del modal
    estado_edicion = {
        "indice_objetivo": indice_item,
        "producto": item_original.producto,
        "guiso": item_original.guiso,
        "cantidad": item_original.cantidad,
        "extras": set(item_original.extras),
        "sin": set(item_original.sin_ingredientes),
        "nota": item_original.nota,
        "pieza_separada_msg": "",
    }

    # Contenedores dinámicos del modal
    encabezado_fila = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    banner_separado = ft.Container(visible=False)
    wrap_guisos_base = ft.Row(wrap=True, spacing=6, run_spacing=6)
    wrap_extras = ft.Row(wrap=True, spacing=6, run_spacing=6)
    wrap_sin = ft.Row(wrap=True, spacing=6, run_spacing=6)
    contenedor_boton_separar = ft.Container()

    campo_nota = ft.TextField(
        label="Nota especial (ej. bien dorada, salsa aparte)",
        value=str(estado_edicion["nota"]),
        bgcolor=colors.WHITE,
        border_color=COLOR_BORDE_INPUT,
        border_radius=10,
        text_size=13,
        text_style=ft.TextStyle(color=colors.BLACK87),
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
    )

    # Ordenar extras para mostrar primero complementos (Queso, Crema) y luego los guisos
    extras_ordenados = sorted(
        reglas.extras_permitidos,
        key=lambda ing: (1 if ing in reglas.guisos_base else 0, ing),
    )

    def cambiar_cantidad_borrador(delta: int) -> None:
        nueva = int(estado_edicion["cantidad"]) + delta
        if nueva >= 1:
            estado_edicion["cantidad"] = nueva
            refrescar_modal()

    def seleccionar_guiso_base(nuevo_guiso: str) -> None:
        estado_edicion["guiso"] = nuevo_guiso
        refrescar_modal()

    def alternar_extra(ingrediente: str) -> None:
        extras_set: set[str] = estado_edicion["extras"]
        sin_set: set[str] = estado_edicion["sin"]
        if ingrediente in extras_set:
            extras_set.remove(ingrediente)
        else:
            extras_set.add(ingrediente)
            # Evitar contradicción: si agrega "+ Queso", quitar "sin Queso"
            sin_set.discard(ingrediente)
        refrescar_modal()

    def alternar_sin(ingrediente: str) -> None:
        sin_set: set[str] = estado_edicion["sin"]
        extras_set: set[str] = estado_edicion["extras"]
        if ingrediente in sin_set:
            sin_set.remove(ingrediente)
        else:
            sin_set.add(ingrediente)
            # Evitar contradicción: si marca "sin Queso", quitar "+ Queso"
            extras_set.discard(ingrediente)
        refrescar_modal()

    def accion_separar_una_pieza(_e: ft.ControlEvent) -> None:
        idx_actual = int(estado_edicion["indice_objetivo"])
        if plato.items[idx_actual].cantidad <= 1:
            return
        restantes = plato.items[idx_actual].cantidad - 1
        nuevo_idx = plato.separar_pieza_de_item(idx_actual)
        estado_edicion["indice_objetivo"] = nuevo_idx
        estado_edicion["cantidad"] = 1
        estado_edicion["pieza_separada_msg"] = (
            f"Editando 1 pieza por separado (quedaron {restantes} aparte en el plato)."
        )
        on_guardar_callback()
        refrescar_modal()

    def guardar_edicion(_e: ft.ControlEvent) -> None:
        idx_actual = int(estado_edicion["indice_objetivo"])
        extras_set: set[str] = estado_edicion["extras"]
        sin_set: set[str] = estado_edicion["sin"]

        mods: list[Modificador] = [
            Modificador(TipoModificador.EXTRA, ing) for ing in extras_set
        ] + [
            Modificador(TipoModificador.SIN, ing) for ing in sin_set
        ]

        item_actualizado = Item(
            producto=str(estado_edicion["producto"]),
            guiso=str(estado_edicion["guiso"]),
            cantidad=int(estado_edicion["cantidad"]),
            modificadores=mods,
            nota=campo_nota.value or "",
        )

        plato.actualizar_item(idx_actual, item_actualizado, catalogo)
        page.close(bottom_sheet)
        on_guardar_callback()

    def renderizar_controles_modal() -> None:
        prod = str(estado_edicion["producto"])
        guiso_actual = str(estado_edicion["guiso"])
        cant_actual = int(estado_edicion["cantidad"])
        extras_set: set[str] = estado_edicion["extras"]
        sin_set: set[str] = estado_edicion["sin"]
        msg_separado = str(estado_edicion["pieza_separada_msg"])

        # 1. Encabezado con título y ajuste de cantidad
        encabezado_fila.controls = [
            ft.Column(
                spacing=2,
                expand=True,
                controls=[
                    ft.Text(
                        f"Personalizar {prod}",
                        size=12,
                        color=colors.BLUE_GREY_600,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"{cant_actual}× {prod} de {guiso_actual}",
                        size=17,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLACK87,
                    ),
                ],
            ),
            ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    ft.IconButton(
                        icon=icons.REMOVE,
                        icon_size=16,
                        icon_color=colors.WHITE,
                        bgcolor=colors.RED_600 if cant_actual > 1 else colors.BLUE_GREY_200,
                        disabled=cant_actual <= 1,
                        width=32,
                        height=32,
                        on_click=lambda _e: cambiar_cantidad_borrador(-1),
                    ),
                    ft.Text(
                        str(cant_actual),
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=colors.BLACK87,
                    ),
                    ft.IconButton(
                        icon=icons.ADD,
                        icon_size=16,
                        icon_color=colors.WHITE,
                        bgcolor=colors.BLUE_600,
                        width=32,
                        height=32,
                        on_click=lambda _e: cambiar_cantidad_borrador(+1),
                    ),
                ],
            ),
        ]

        # 2. Banner de pieza separada o botón para separar 1 pieza
        if msg_separado:
            banner_separado.visible = True
            banner_separado.content = ft.Container(
                bgcolor=colors.AMBER_100,
                border=ft.border.all(1, colors.AMBER_700),
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                content=ft.Text(
                    msg_separado,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK87,
                ),
            )
        else:
            banner_separado.visible = False

        idx_actual = int(estado_edicion["indice_objetivo"])
        puede_separar = (
            0 <= idx_actual < len(plato.items) and plato.items[idx_actual].cantidad > 1
        )
        contenedor_boton_separar.visible = puede_separar
        contenedor_boton_separar.content = ft.OutlinedButton(
            text="Separar 1 pieza para personalizarla aparte",
            icon=icons.CALL_SPLIT,
            style=ft.ButtonStyle(
                color=colors.DEEP_ORANGE_700,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=accion_separar_una_pieza,
        )

        # 3. Chips para cambiar el guiso base
        chips_base: list[ft.Control] = []
        for g in reglas.guisos_base:
            es_actual = g == guiso_actual
            chips_base.append(
                ft.Container(
                    bgcolor=colors.ORANGE_700 if es_actual else colors.WHITE,
                    border=ft.border.all(
                        1.5,
                        colors.ORANGE_800 if es_actual else colors.BLUE_GREY_200,
                    ),
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=11, vertical=6),
                    ink=True,
                    on_click=lambda _e, gb=g: seleccionar_guiso_base(gb),
                    content=ft.Text(
                        g,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=colors.WHITE if es_actual else colors.BLACK87,
                    ),
                )
            )
        wrap_guisos_base.controls = chips_base

        # 4. Chips multiselección de EXTRAS (Queso, Crema, otros guisos)
        chips_extra: list[ft.Control] = []
        for ing in extras_ordenados:
            activo = ing in extras_set
            es_complemento = ing not in reglas.guisos_base
            color_chip_activo = colors.GREEN_700 if es_complemento else colors.BLUE_700

            chips_extra.append(
                ft.Container(
                    bgcolor=color_chip_activo if activo else colors.WHITE,
                    border=ft.border.all(
                        1.5,
                        color_chip_activo if activo else colors.BLUE_GREY_300,
                    ),
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=11, vertical=6),
                    ink=True,
                    on_click=lambda _e, ex=ing: alternar_extra(ex),
                    content=ft.Row(
                        spacing=4,
                        tight=True,
                        controls=[
                            ft.Icon(
                                icons.CHECK if activo else icons.ADD,
                                size=14,
                                color=colors.WHITE if activo else colors.BLACK87,
                            ),
                            ft.Text(
                                f"Con {ing}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=colors.WHITE if activo else colors.BLACK87,
                            ),
                        ],
                    ),
                )
            )
        wrap_extras.controls = chips_extra

        # 5. Chips multiselección de SIN (solo si el producto los tiene en catálogo)
        if reglas.sin_permitidos:
            chips_sin: list[ft.Control] = []
            for ing in reglas.sin_permitidos:
                activo = ing in sin_set
                chips_sin.append(
                    ft.Container(
                        bgcolor=colors.RED_700 if activo else colors.WHITE,
                        border=ft.border.all(
                            1.5,
                            colors.RED_700 if activo else colors.BLUE_GREY_300,
                        ),
                        border_radius=16,
                        padding=ft.padding.symmetric(horizontal=11, vertical=6),
                        ink=True,
                        on_click=lambda _e, sn=ing: alternar_sin(sn),
                        content=ft.Row(
                            spacing=4,
                            tight=True,
                            controls=[
                                ft.Icon(
                                    icons.CHECK if activo else icons.REMOVE_CIRCLE_OUTLINE,
                                    size=14,
                                    color=colors.WHITE if activo else colors.RED_700,
                                ),
                                ft.Text(
                                    f"Sin {ing}",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=colors.WHITE if activo else colors.BLACK87,
                                ),
                            ],
                        ),
                    )
                )
            wrap_sin.controls = chips_sin

    def refrescar_modal() -> None:
        renderizar_controles_modal()
        page.update()

    renderizar_controles_modal()

    controles_columna: list[ft.Control] = [
        encabezado_fila,
        banner_separado,
        contenedor_boton_separar,
        ft.Divider(height=6, color=colors.BLUE_GREY_100),
        ft.Text(
            "Cambiar guiso base:",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=colors.BLACK87,
        ),
        wrap_guisos_base,
        ft.Divider(height=6, color=colors.BLUE_GREY_100),
        ft.Text(
            "Agregar extra (puedes elegir varios):",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=colors.BLACK87,
        ),
        wrap_extras,
    ]

    if reglas.sin_permitidos:
        controles_columna.extend(
            [
                ft.Divider(height=6, color=colors.BLUE_GREY_100),
                ft.Text(
                    "Quitar ingrediente (Sin...):",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=colors.BLACK87,
                ),
                wrap_sin,
            ]
        )

    controles_columna.extend(
        [
            ft.Divider(height=6, color=colors.BLUE_GREY_100),
            campo_nota,
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                spacing=10,
                controls=[
                    ft.TextButton(
                        "Cerrar",
                        on_click=lambda _e: page.close(bottom_sheet),
                    ),
                    ft.ElevatedButton(
                        "Guardar cambios",
                        icon=icons.CHECK,
                        bgcolor=colors.GREEN_700,
                        color=colors.WHITE,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=guardar_edicion,
                    ),
                ],
            ),
        ]
    )

    bottom_sheet = ft.BottomSheet(
        is_scroll_controlled=True,
        content=ft.Container(
            width=375,
            bgcolor=colors.BLUE_GREY_50,
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.only(top_left=16, top_right=16),
            content=ft.Column(
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=controles_columna,
            ),
        ),
    )

    page.open(bottom_sheet)
