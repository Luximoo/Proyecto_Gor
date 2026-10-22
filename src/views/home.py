"""Vista exclusiva para Cocina (`/home`): visualización limpia de pedidos pendientes."""

from __future__ import annotations

import logging
import threading

import flet as ft
import mysql.connector

from config import ERROR_RETRY_SECONDS, POLL_INTERVAL_SECONDS
from data.repositorio import (
    marcar_pedido_completado,
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
    Construye el monitor limpio de cocina (`/home`):
    - Muestra únicamente los pedidos pendientes por preparar.
    - Sin botones de edición ni pestañas extra para no distraer a los cocineros.
    - Letra grande y clara para leer de un vistazo mientras cocinan.
    """
    evento_anterior: threading.Event | None = getattr(page, "_home_stop_event", None)
    if evento_anterior is not None:
        evento_anterior.set()

    stop_event = threading.Event()
    setattr(page, "_home_stop_event", stop_event)

    ui_lock = threading.Lock()
    estado_cocina = {
        "pendientes": [],
        "huella_pendientes": (),
    }

    titulo_contador = ft.Text(
        "Pedidos en Cocina",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=colors.BLACK87,
    )
    lista_tarjetas = ft.ResponsiveRow(spacing=12, run_spacing=12)

    def _calcular_huella(pedidos: list[Pedido]) -> tuple[tuple[int, int], ...]:
        return tuple((int(p.id or 0), int(p.version)) for p in pedidos)

    def _completar_pedido_accion(pedido_id: int) -> None:
        """Marca el pedido como listo y lo retira inmediatamente de la pantalla de cocina."""
        logging.info(f"Completando pedido #{pedido_id} desde cocina...")
        try:
            marcar_pedido_completado(pedido_id)
            pendientes = obtener_pedidos_pendientes()
            with ui_lock:
                estado_cocina["pendientes"] = pendientes
                estado_cocina["huella_pendientes"] = _calcular_huella(pendientes)
                _renderizar_en_lock()
            if page:
                page.update()
        except mysql.connector.Error as err:
            logging.error(f"Error de base de datos al completar pedido #{pedido_id}: {err}")
        except Exception as err:
            logging.error(f"Error inesperado al completar pedido #{pedido_id}: {err}")

    def _renderizar_en_lock() -> None:
        pendientes: list[Pedido] = estado_cocina["pendientes"]
        total = len(pendientes)
        titulo_contador.value = (
            f"Pedidos en Cocina ({total})" if total > 0 else "Pedidos en Cocina"
        )

        if not pendientes:
            lista_tarjetas.controls = [
                ft.Container(
                    padding=ft.padding.symmetric(vertical=50, horizontal=20),
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(
                                icons.HOURGLASS_EMPTY_ROUNDED,
                                size=44,
                                color=colors.BLUE_ACCENT_700,
                            ),
                            ft.Text(
                                "Esperando pedidos...",
                                size=19,
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
                on_completar=_completar_pedido_accion,
            )
            for ped in pendientes
        ]

    def _sincronizar_desde_bd(forzar_render: bool = False) -> bool:
        pendientes = obtener_pedidos_pendientes()
        nueva_huella = _calcular_huella(pendientes)

        with ui_lock:
            hubo_cambios = (
                forzar_render or nueva_huella != estado_cocina["huella_pendientes"]
            )
            if hubo_cambios:
                estado_cocina["pendientes"] = pendientes
                estado_cocina["huella_pendientes"] = nueva_huella
                _renderizar_en_lock()
            return hubo_cambios

    def _tarea_actualizacion() -> None:
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
                logging.error(f"Error de base de datos en cocina: {err}")
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue
            except Exception as err:
                logging.error(f"Error inesperado en cocina: {err}", exc_info=True)
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue

            if stop_event.wait(POLL_INTERVAL_SECONDS):
                break

        logging.info("Hilo del monitor de cocina detenido limpiamente.")

    try:
        _sincronizar_desde_bd(forzar_render=True)
    except Exception as err:
        logging.warning(f"No se pudo realizar la carga inicial de cocina: {err}")
        with ui_lock:
            _renderizar_en_lock()

    navegacion = crear_navegacion(page, selected_index=0)

    hilo = threading.Thread(target=_tarea_actualizacion, daemon=True)
    hilo.start()

    return ft.View(
        route="/home",
        controls=[
            titulo_contador,
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
