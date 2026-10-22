"""Vista del monitor de cocina (`/home`): muestra pedidos por plato, versión y pestaña Completados."""

from __future__ import annotations

import logging
import threading

import flet as ft
import mysql.connector

from config import ERROR_RETRY_SECONDS, POLL_INTERVAL_SECONDS
from data.repositorio import (
    marcar_pedido_completado,
    obtener_pedidos_completados_hoy,
    obtener_pedidos_pendientes,
)
from domain.modelos import Pedido
from ui.components import crear_navegacion, crear_tarjeta_pedido_cocina
from ui.theme import COLOR_FONDO_PAGINA, colors, icons

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def view_home(page: ft.Page) -> ft.View:
    """
    Construye el monitor de cocina (`/home`) con:
    - Pestaña 'Pendientes' (pedidos activos ordenados por antigüedad).
    - Pestaña 'Completados hoy' (para consultarlos o editarlos en cualquier momento).
    - Sincronización en tiempo real comparando `(id, version)` para detectar ediciones.
    """
    # Detener cualquier hilo de sondeo anterior asociado a esta página
    evento_anterior: threading.Event | None = getattr(page, "_home_stop_event", None)
    if evento_anterior is not None:
        evento_anterior.set()

    stop_event = threading.Event()
    setattr(page, "_home_stop_event", stop_event)

    ui_lock = threading.Lock()
    estado_monitor = {
        "tab_activa": "PENDIENTES",  # "PENDIENTES" | "COMPLETADOS"
        "pendientes": [],
        "completados": [],
        "huella_pendientes": (),
        "huella_completados": (),
    }

    fila_pestanas_estado = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    lista_tarjetas = ft.Column(spacing=8)

    def _calcular_huella(pedidos: list[Pedido]) -> tuple[tuple[int, int], ...]:
        """Genera una tupla inmutable de `(id, version)` para detectar altas, bajas y ediciones."""
        return tuple((int(p.id or 0), int(p.version)) for p in pedidos)

    def _cambiar_tab(nueva_tab: str) -> None:
        with ui_lock:
            estado_monitor["tab_activa"] = nueva_tab
            _renderizar_monitor_en_lock()
        if page:
            page.update()

    def _ir_a_editar(pedido_id: int) -> None:
        """Navega a la ruta de edición del pedido seleccionado."""
        stop_event.set()
        page.go(f"/pedido/{pedido_id}")

    def _completar_pedido_accion(pedido_id: int) -> None:
        """Marca un pedido como completado en BD y refresca el monitor inmediatamente."""
        logging.info(f"Completando pedido #{pedido_id}...")
        try:
            marcar_pedido_completado(pedido_id)
            pendientes = obtener_pedidos_pendientes()
            completados = obtener_pedidos_completados_hoy()
            with ui_lock:
                estado_monitor["pendientes"] = pendientes
                estado_monitor["completados"] = completados
                estado_monitor["huella_pendientes"] = _calcular_huella(pendientes)
                estado_monitor["huella_completados"] = _calcular_huella(completados)
                _renderizar_monitor_en_lock()
            if page:
                page.update()
        except mysql.connector.Error as err:
            logging.error(f"Error de base de datos al completar pedido #{pedido_id}: {err}")
        except Exception as err:
            logging.error(f"Error inesperado al completar pedido #{pedido_id}: {err}")

    def _renderizar_monitor_en_lock() -> None:
        """Reconstruye las pestañas de filtro y la lista de tarjetas (debe llamarse dentro de `ui_lock`)."""
        tab_activa = str(estado_monitor["tab_activa"])
        pendientes: list[Pedido] = estado_monitor["pendientes"]
        completados: list[Pedido] = estado_monitor["completados"]

        es_tab_pendientes = tab_activa == "PENDIENTES"

        fila_pestanas_estado.controls = [
            ft.Container(
                expand=True,
                height=42,
                bgcolor=colors.ORANGE_700 if es_tab_pendientes else colors.WHITE,
                border=ft.border.all(
                    2,
                    colors.ORANGE_800 if es_tab_pendientes else colors.BLUE_GREY_200,
                ),
                border_radius=10,
                alignment=ft.alignment.center,
                ink=True,
                on_click=lambda _e: _cambiar_tab("PENDIENTES"),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Icon(
                            icons.LOCAL_FIRE_DEPARTMENT,
                            size=17,
                            color=colors.WHITE if es_tab_pendientes else colors.ORANGE_700,
                        ),
                        ft.Text(
                            f"Pendientes ({len(pendientes)})",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.WHITE if es_tab_pendientes else colors.BLACK87,
                        ),
                    ],
                ),
            ),
            ft.Container(
                expand=True,
                height=42,
                bgcolor=colors.GREEN_700 if not es_tab_pendientes else colors.WHITE,
                border=ft.border.all(
                    2,
                    colors.GREEN_800 if not es_tab_pendientes else colors.BLUE_GREY_200,
                ),
                border_radius=10,
                alignment=ft.alignment.center,
                ink=True,
                on_click=lambda _e: _cambiar_tab("COMPLETADOS"),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Icon(
                            icons.CHECK_CIRCLE_OUTLINE,
                            size=17,
                            color=colors.WHITE if not es_tab_pendientes else colors.GREEN_700,
                        ),
                        ft.Text(
                            f"Completados ({len(completados)})",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors.WHITE if not es_tab_pendientes else colors.BLACK87,
                        ),
                    ],
                ),
            ),
        ]

        pedidos_a_mostrar = pendientes if es_tab_pendientes else completados

        if not pedidos_a_mostrar:
            mensaje_vacio = (
                "Esperando pedidos pendientes..."
                if es_tab_pendientes
                else "Aún no hay pedidos completados hoy."
            )
            icono_vacio = (
                icons.HOURGLASS_EMPTY_ROUNDED
                if es_tab_pendientes
                else icons.INBOX_OUTLINED
            )
            lista_tarjetas.controls = [
                ft.Container(
                    padding=ft.padding.symmetric(vertical=40, horizontal=20),
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(icono_vacio, size=42, color=colors.BLUE_ACCENT_700),
                            ft.Text(
                                mensaje_vacio,
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=colors.BLACK54,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                    ),
                )
            ]
            return

        lista_tarjetas.controls = [
            crear_tarjeta_pedido_cocina(
                pedido=ped,
                on_editar=_ir_a_editar,
                on_completar=_completar_pedido_accion if es_tab_pendientes else None,
            )
            for ped in pedidos_a_mostrar
        ]

    def _sincronizar_desde_bd(forzar_render: bool = False) -> bool:
        """
        Consulta pendientes y completados en BD y reconstruye las tarjetas solo si
        cambió algún `(id, version)` o si `forzar_render=True`.
        """
        pendientes = obtener_pedidos_pendientes()
        completados = obtener_pedidos_completados_hoy()

        nueva_huella_pend = _calcular_huella(pendientes)
        nueva_huella_comp = _calcular_huella(completados)

        with ui_lock:
            hubo_cambios = (
                forzar_render
                or nueva_huella_pend != estado_monitor["huella_pendientes"]
                or nueva_huella_comp != estado_monitor["huella_completados"]
            )
            if hubo_cambios:
                estado_monitor["pendientes"] = pendientes
                estado_monitor["completados"] = completados
                estado_monitor["huella_pendientes"] = nueva_huella_pend
                estado_monitor["huella_completados"] = nueva_huella_comp
                _renderizar_monitor_en_lock()
            return hubo_cambios

    def _tarea_actualizacion() -> None:
        """Hilo de sondeo periódico mientras la vista `/home` esté activa."""
        logging.info("Hilo del monitor de cocina iniciado.")
        while not stop_event.is_set():
            if not page or page.route != "/home":
                break

            try:
                if _sincronizar_desde_bd() and page and not stop_event.is_set():
                    try:
                        page.update()
                    except Exception as update_err:
                        logging.error(f"Error durante page.update(): {update_err}")
                        break
            except mysql.connector.Error as err:
                logging.error(f"Error de base de datos en monitor de cocina: {err}")
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue
            except Exception as err:
                logging.error(f"Error inesperado en monitor de cocina: {err}", exc_info=True)
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue

            if stop_event.wait(POLL_INTERVAL_SECONDS):
                break

        logging.info("Hilo del monitor de cocina detenido limpiamente.")

    # Render inicial inmediato antes de lanzar el hilo
    try:
        _sincronizar_desde_bd(forzar_render=True)
    except Exception as err:
        logging.warning(f"No se pudo realizar la carga inicial del monitor: {err}")
        with ui_lock:
            _renderizar_monitor_en_lock()

    navegacion = crear_navegacion(page, selected_index=0)

    hilo = threading.Thread(target=_tarea_actualizacion, daemon=True)
    hilo.start()

    return ft.View(
        route="/home",
        controls=[
            ft.Text(
                "Monitor de Cocina",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=colors.BLACK87,
            ),
            fila_pestanas_estado,
            lista_tarjetas,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=14,
        bgcolor=COLOR_FONDO_PAGINA,
    )


# Alias de compatibilidad
View_home = view_home
