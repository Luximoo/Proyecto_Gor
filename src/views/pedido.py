"""Vista para tomar y enviar pedidos (Gorditas y Sopes)."""

from dataclasses import dataclass, field
import logging
from typing import Callable

import flet as ft
import mysql.connector

from data.db import crear_pedido
from data.menu import (
    GUISOS,
    OPCIONES_COMPLEMENTO_GORDITA,
    OPCIONES_COMPLEMENTO_SOPE,
    OpcionComplemento,
)
from ui.components import (
    crear_campo_cantidad,
    crear_contenedor_bottom_sheet,
    crear_fila_guiso,
    crear_navegacion,
    create_custom_tile_header,
    create_styled_button,
    create_styled_button_eliminar,
    create_styled_button_opciones,
    create_styled_button_realizar,
)
from ui.theme import (
    COLOR_ETIQUETA_GORDITA,
    COLOR_ETIQUETA_SOPE,
    COLOR_FONDO_PAGINA,
    COLOR_SOMBRA_BOTON,
    colors,
    icons,
)

SEPARADOR_RESUMEN = "-----------------------------------"


@dataclass
class SeccionPlatillo:
    """Agrupa el estado y los controles de una categoría de platillo (p. ej. Gorditas o Sopes)."""

    titulo_seccion: str
    nombre_singular: str
    guisos: list[str]
    opciones_complemento: list[OpcionComplemento]
    color_etiqueta: str
    expandir_controles: bool = False
    cantidades: list[int] = field(init=False)
    campos_cantidad: list[ft.TextField] = field(default_factory=list, init=False)
    guiso_activo_idx: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.cantidades = [0] * len(self.guisos)

    def construir(
        self,
        page: ft.Page,
        on_agregar_linea: Callable[[str], None],
    ) -> ft.ExpansionTile:
        """Construye el `ExpansionTile` y su `BottomSheet` asociado sin variables globales."""
        columna_opciones_bs = ft.Column(
            tight=True,
            scroll=ft.ScrollMode.ALWAYS,
        )
        bottom_sheet = ft.BottomSheet(
            content=crear_contenedor_bottom_sheet(columna_opciones_bs),
        )

        def seleccionar_complemento(opcion: OpcionComplemento) -> Callable[[ft.ControlEvent], None]:
            def handler(_e: ft.ControlEvent) -> None:
                idx = self.guiso_activo_idx
                cantidad = self.cantidades[idx]
                guiso_base = self.guisos[idx]
                if cantidad > 0:
                    linea = f"{cantidad} {self.nombre_singular} de {guiso_base} {opcion.texto_resumen}  "
                    on_agregar_linea(linea)
                    self.reiniciar_contador(idx)
                page.close(bottom_sheet)
                page.update()

            return handler

        for opcion in self.opciones_complemento:
            columna_opciones_bs.controls.append(
                ft.ElevatedButton(
                    on_click=seleccionar_complemento(opcion),
                    content=create_styled_button(opcion.etiqueta_boton),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.padding.all(0),
                        elevation=4,
                        shadow_color=COLOR_SOMBRA_BOTON,
                    ),
                )
            )

        def incrementar(idx: int) -> Callable[[ft.ControlEvent], None]:
            def handler(_e: ft.ControlEvent) -> None:
                self.cantidades[idx] += 1
                self.campos_cantidad[idx].value = str(self.cantidades[idx])
                page.update()

            return handler

        def decrementar(idx: int) -> Callable[[ft.ControlEvent], None]:
            def handler(_e: ft.ControlEvent) -> None:
                if self.cantidades[idx] >= 1:
                    self.cantidades[idx] -= 1
                    self.campos_cantidad[idx].value = str(self.cantidades[idx])
                    page.update()

            return handler

        def abrir_opciones(idx: int) -> Callable[[ft.ControlEvent], None]:
            def handler(_e: ft.ControlEvent) -> None:
                if self.cantidades[idx] > 0:
                    self.guiso_activo_idx = idx
                    page.open(bottom_sheet)

            return handler

        controles_tile: list[ft.Control] = []
        for idx, nombre_guiso in enumerate(self.guisos):
            campo = crear_campo_cantidad(
                valor_inicial=0,
                expandir=self.expandir_controles,
            )
            self.campos_cantidad.append(campo)

            fila = crear_fila_guiso(
                nombre_guiso=nombre_guiso,
                campo_cantidad=campo,
                on_restar=decrementar(idx),
                on_sumar=incrementar(idx),
                color_etiqueta=self.color_etiqueta,
                expandir=self.expandir_controles,
            )
            btn_opciones = ft.ElevatedButton(
                content=create_styled_button_opciones("Opciones"),
                on_click=abrir_opciones(idx),
            )
            controles_tile.extend([fila, btn_opciones])

        return ft.ExpansionTile(
            title=create_custom_tile_header(self.titulo_seccion, icons.FASTFOOD),
            bgcolor=colors.TRANSPARENT,
            collapsed_bgcolor=colors.TRANSPARENT,
            tile_padding=ft.padding.all(0),
            maintain_state=True,
            controls=controles_tile,
        )

    def reiniciar_contador(self, idx: int) -> None:
        """Restablece en 0 la cantidad de un guiso tanto en estado como en su TextField."""
        self.cantidades[idx] = 0
        self.campos_cantidad[idx].value = "0"

    def recolectar_pendientes(self) -> list[str]:
        """Extrae las líneas de guisos con cantidad > 0 y reinicia sus contadores."""
        lineas: list[str] = []
        for idx, nombre_guiso in enumerate(self.guisos):
            cantidad = self.cantidades[idx]
            if cantidad > 0:
                lineas.append(f" {cantidad} {self.nombre_singular} de {nombre_guiso}")
                self.reiniciar_contador(idx)
        return lineas


def view_realizar_pedido(page: ft.Page) -> ft.View:
    """Construye la vista `/Pedidos` para armar y registrar una orden."""
    navegacion = crear_navegacion(page, selected_index=1)
    lineas_resumen: list[str] = []

    resumen = ft.TextField(
        label="Resumen de pedido",
        value="",
        disabled=True,
        multiline=True,
        min_lines=1,
        max_lines=10,
    )

    def actualizar_texto_resumen() -> None:
        resumen.value = "\n".join(lineas_resumen) + ("\n" if lineas_resumen else "")

    def agregar_linea_resumen(linea: str) -> None:
        lineas_resumen.append(linea)
        actualizar_texto_resumen()

    seccion_gorditas = SeccionPlatillo(
        titulo_seccion="Gorditas",
        nombre_singular="Gordita",
        guisos=GUISOS,
        opciones_complemento=OPCIONES_COMPLEMENTO_GORDITA,
        color_etiqueta=COLOR_ETIQUETA_GORDITA,
        expandir_controles=False,
    )

    seccion_sopes = SeccionPlatillo(
        titulo_seccion="Sopes",
        nombre_singular="Sope",
        guisos=GUISOS,
        opciones_complemento=OPCIONES_COMPLEMENTO_SOPE,
        color_etiqueta=COLOR_ETIQUETA_SOPE,
        expandir_controles=True,
    )

    secciones = [seccion_gorditas, seccion_sopes]
    tile_gorditas = seccion_gorditas.construir(page, agregar_linea_resumen)
    tile_sopes = seccion_sopes.construir(page, agregar_linea_resumen)

    def agregar_al_pedido(_e: ft.ControlEvent) -> None:
        nuevas_lineas: list[str] = []
        for seccion in secciones:
            nuevas_lineas.extend(seccion.recolectar_pendientes())

        if nuevas_lineas:
            lineas_resumen.extend(nuevas_lineas)
            lineas_resumen.append(SEPARADOR_RESUMEN)
            actualizar_texto_resumen()
            page.update()

    def eliminar_ultima_linea(_e: ft.ControlEvent) -> None:
        if lineas_resumen:
            lineas_resumen.pop()
            actualizar_texto_resumen()
            page.update()

    def enviar_pedido(_e: ft.ControlEvent) -> None:
        texto_pedido = resumen.value.strip()
        if not texto_pedido:
            return

        try:
            crear_pedido(resumen.value)
            lineas_resumen.clear()
            actualizar_texto_resumen()
            page.update()
        except mysql.connector.Error as err:
            logging.error(f"Error de base de datos al registrar el pedido: {err}")
        except Exception as err:
            logging.error(f"Error inesperado al registrar el pedido: {err}")

    btn_agregar = ft.ElevatedButton(
        content=create_styled_button_opciones("Agregar a Pedido"),
        on_click=agregar_al_pedido,
    )
    btn_deshacer = ft.ElevatedButton(
        content=create_styled_button_eliminar("<-"),
        on_click=eliminar_ultima_linea,
    )
    btn_enviar = ft.ElevatedButton(
        content=create_styled_button_realizar("Realizar Pedido"),
        on_click=enviar_pedido,
    )

    return ft.View(
        route="/Pedidos",
        controls=[
            ft.Divider(height=50),
            ft.Column(
                controls=[btn_agregar, btn_deshacer, btn_enviar],
                expand=True,
            ),
            tile_gorditas,
            tile_sopes,
            resumen,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=20,
        bgcolor=COLOR_FONDO_PAGINA,
    )


# Alias de compatibilidad hacia atrás
View_RealizarPedido = view_realizar_pedido
