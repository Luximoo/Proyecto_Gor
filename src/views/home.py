"""Vista del monitor de cocina (`/home`): muestra pedidos activos en tiempo real."""

import logging
import threading

import flet as ft
import mysql.connector

from config import ERROR_RETRY_SECONDS, POLL_INTERVAL_SECONDS
from data.db import completar_pedido, obtener_pedidos_activos
from ui.components import crear_navegacion, create_info_card
from ui.theme import COLOR_FONDO_PAGINA, colors, icons

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def view_home(page: ft.Page) -> ft.View:
    """
    Construye la vista `/home` y gestiona un único hilo de sondeo para la página.
    Si existía un hilo previo de una visita anterior a `/home`, lo detiene limpiamente.
    """
    # Detener cualquier hilo de sondeo anterior asociado a esta página
    evento_anterior: threading.Event | None = getattr(page, "_home_stop_event", None)
    if evento_anterior is not None:
        evento_anterior.set()

    stop_event = threading.Event()
    setattr(page, "_home_stop_event", stop_event)

    ui_lock = threading.Lock()
    displayed_order_ids: set[int] = set()
    lista_cartas = ft.ResponsiveRow()

    texto_esperando = ft.Row(
        controls=[
            ft.Icon(
                icons.HOURGLASS_EMPTY_ROUNDED,
                size=30,
                color=colors.BLUE_ACCENT_700,
            ),
            ft.Text("Esperando pedidos...", size=22, weight=ft.FontWeight.BOLD),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        visible=True,
    )

    def _actualizar_visibilidad_espera() -> None:
        """Muestra el indicador 'Esperando pedidos...' solo cuando no hay tarjetas activas."""
        texto_esperando.visible = len(displayed_order_ids) == 0

    def _completar_y_eliminar_tarjeta(order_id_to_delete: int) -> None:
        """Marca el pedido como completado en BD y retira su tarjeta de la UI de inmediato."""
        logging.info(f"Intentando marcar como completado el pedido ID: {order_id_to_delete}")
        try:
            completar_pedido(order_id_to_delete)

            with ui_lock:
                tarjeta_a_quitar = next(
                    (
                        card
                        for card in lista_cartas.controls
                        if getattr(card, "data", None) == order_id_to_delete
                    ),
                    None,
                )
                if tarjeta_a_quitar is not None:
                    lista_cartas.controls.remove(tarjeta_a_quitar)
                    displayed_order_ids.discard(order_id_to_delete)
                    _actualizar_visibilidad_espera()
                    logging.info(
                        f"Tarjeta para pedido ID: {order_id_to_delete} eliminada de la UI inmediatamente."
                    )
                    if page:
                        page.update()
                else:
                    logging.warning(
                        f"No se encontró la tarjeta con ID {order_id_to_delete} para eliminarla inmediatamente."
                    )

        except mysql.connector.Error as err:
            logging.error(
                f"Error de base de datos al actualizar pedido {order_id_to_delete}: {err}"
            )
        except Exception as err:
            logging.error(
                f"Error inesperado al procesar eliminación de pedido {order_id_to_delete}: {err}"
            )

    def _sincronizar_tarjetas(pedidos_activos: dict[int, str]) -> bool:
        """
        Sincroniza los controles de `lista_cartas` con los pedidos activos en BD.
        Retorna True si hubo cambios que requieren `page.update()`.
        """
        ids_activos_db = set(pedidos_activos.keys())
        hubo_cambios = False

        with ui_lock:
            # 1. Añadir nuevos pedidos que aún no están en pantalla
            ids_por_agregar = sorted(ids_activos_db - displayed_order_ids)
            if ids_por_agregar:
                logging.info(f"Nuevos pedidos para añadir a la UI: {ids_por_agregar}")
                for order_id in ids_por_agregar:
                    lineas_pedido = pedidos_activos[order_id].strip().split("\n")
                    nueva_tarjeta = create_info_card(
                        order_id=order_id,
                        title=f"Numero de orden {order_id}",
                        description="\n".join(lineas_pedido),
                        on_complete_callback=_completar_y_eliminar_tarjeta,
                    )
                    lista_cartas.controls.append(nueva_tarjeta)
                    displayed_order_ids.add(order_id)
                    hubo_cambios = True
                    logging.info(f"Tarjeta para pedido ID: {order_id} añadida a la UI.")

            # 2. Quitar pedidos que ya fueron completados (p. ej. desde otra ventana)
            ids_por_quitar = displayed_order_ids - ids_activos_db
            if ids_por_quitar:
                logging.info(f"Pedidos ya no activos, eliminar de la UI: {ids_por_quitar}")
                controles_a_quitar = [
                    control
                    for control in lista_cartas.controls
                    if getattr(control, "data", None) in ids_por_quitar
                ]
                for control in controles_a_quitar:
                    control_id = getattr(control, "data", None)
                    lista_cartas.controls.remove(control)
                    displayed_order_ids.discard(control_id)
                    hubo_cambios = True
                    logging.info(f"Tarjeta para pedido ID: {control_id} eliminada de la UI.")

            if hubo_cambios:
                _actualizar_visibilidad_espera()

        return hubo_cambios

    def _tarea_actualizacion() -> None:
        """Hilo en segundo plano que consulta periódicamente la BD mientras `/home` esté activo."""
        logging.info("Hilo de actualización de pedidos iniciado.")
        while not stop_event.is_set():
            if not page or page.route != "/home":
                logging.info("Saliendo de /home, deteniendo hilo de actualización.")
                break

            try:
                pedidos_activos = obtener_pedidos_activos()
                if _sincronizar_tarjetas(pedidos_activos) and page and not stop_event.is_set():
                    try:
                        page.update()
                    except Exception as update_err:
                        logging.error(f"Error durante page.update(): {update_err}")
                        break

            except mysql.connector.Error as err:
                logging.error(f"Error de base de datos en el hilo de actualización: {err}")
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue
            except Exception as err:
                logging.error(
                    f"Error inesperado en el hilo de actualización: {err}",
                    exc_info=True,
                )
                if stop_event.wait(ERROR_RETRY_SECONDS):
                    break
                continue

            if stop_event.wait(POLL_INTERVAL_SECONDS):
                break

        logging.info("Hilo de actualización detenido limpiamente.")

    navegacion = crear_navegacion(page, selected_index=0)

    hilo = threading.Thread(target=_tarea_actualizacion, daemon=True)
    hilo.start()

    return ft.View(
        route="/home",
        controls=[
            lista_cartas,
            texto_esperando,
            navegacion,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=20,
        bgcolor=COLOR_FONDO_PAGINA,
    )


# Alias de compatibilidad hacia atrás
View_home = view_home
