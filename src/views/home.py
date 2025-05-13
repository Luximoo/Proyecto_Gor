import flet as ft
# Asumiendo que utils contiene create_info_card y crear_navegacion
from Utilidades.utils import create_info_card, crear_navegacion
# import Utilidades.utils # No necesitas importar dos veces
import mysql.connector
import time
import threading
import logging # Es buena idea usar logging para depurar hilos

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Variables Globales ---
# Usar un Lock para proteger el acceso a controles compartidos si fuera necesario,
# aunque Flet maneja las actualizaciones de UI desde hilos si usas page.update()
ui_lock = threading.Lock()
# Guardaremos los IDs de los pedidos que ya están mostrados en esta instancia
displayed_order_ids = set()

# --- Componentes UI ---
# listacartas debe ser accesible globalmente o pasada correctamente
listacartas = ft.ResponsiveRow()

def View_home(page: ft.Page):

    # --- Funciones Auxiliares ---

    def _eliminar_tarjeta_y_actualizar_db(order_id_to_delete: int):
        """
        Esta función se llamaría desde la tarjeta (p. ej., un botón 'Completar').
        Actualiza la BD y la UI la reflejará en el próximo ciclo.
        Opcionalmente, puedes quitarla de la UI inmediatamente aquí.
        """
        logging.info(f"Intentando marcar como completado el pedido ID: {order_id_to_delete}")
        try:
            db_config = get_db_config() # Helper para obtener config
            mydb = mysql.connector.connect(**db_config)
            mycursor = mydb.cursor()
            # Cambia estado a 3 (o el que signifique 'completado/eliminado de vista')
            mycursor.execute("UPDATE pedidos SET estado = 3 WHERE id = %s AND estado = 1", (order_id_to_delete,))
            mydb.commit()
            logging.info(f"Pedido ID: {order_id_to_delete} marcado como completado en DB (si existía con estado 1). Filas afectadas: {mycursor.rowcount}")
            mycursor.close()
            mydb.close()

            # Opcional: Remover inmediatamente de la UI para mejor respuesta visual
            # (Requiere encontrar la tarjeta específica por ID)
            with ui_lock: # Proteger acceso a controles compartidos
                card_to_remove = None
                for card in listacartas.controls:
                     # Asumiendo que guardas el ID en card.data
                    if hasattr(card, 'data') and card.data == order_id_to_delete:
                        card_to_remove = card
                        break
                if card_to_remove:
                    listacartas.controls.remove(card_to_remove)
                    if order_id_to_delete in displayed_order_ids:
                         displayed_order_ids.remove(order_id_to_delete)
                    logging.info(f"Tarjeta para pedido ID: {order_id_to_delete} eliminada de la UI inmediatamente.")
                    if page: # Asegurarse que la página aún existe
                         page.update()
                else:
                     logging.warning(f"No se encontró la tarjeta con ID {order_id_to_delete} para eliminarla inmediatamente.")


        except mysql.connector.Error as err:
            logging.error(f"Error de base de datos al actualizar pedido {order_id_to_delete}: {err}")
        except Exception as e:
            logging.error(f"Error inesperado al procesar eliminación de pedido {order_id_to_delete}: {e}")

    def get_db_config():
         # Centraliza la configuración de la BD
        return {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "gorditas",
            "autocommit": False # Importante para manejar transacciones si es necesario
        }

    def tarea_actualizacion(page: ft.Page):
        """
        Hilo que consulta periódicamente la BD y actualiza la UI para reflejar
        los pedidos con estado = 1. No modifica el estado en la BD.
        """
        global displayed_order_ids

        while True:
            if not page: # Si la página se cerró, detener el hilo
                logging.info("La página no existe, deteniendo hilo de actualización.")
                break

            current_active_orders = {} # {id: pedido_data}
            try:
                db_config = get_db_config()
                mydb = mysql.connector.connect(**db_config)
                mycursor = mydb.cursor()

                # Selecciona ID y pedido de los que están activos
                # ¡ASEGÚRATE DE TENER UNA COLUMNA 'id' AUTOINCREMENTAL PRIMARY KEY EN TU TABLA pedidos!
                mycursor.execute("SELECT id, pedido FROM pedidos WHERE estado = 1")
                resultados = mycursor.fetchall()
                mycursor.close()
                mydb.close()

                # Crea un diccionario con los pedidos activos actuales de la BD
                for order_id, pedido_data in resultados:
                    current_active_orders[order_id] = pedido_data

                current_active_ids_from_db = set(current_active_orders.keys())
                # logging.debug(f"IDs activos en BD: {current_active_ids_from_db}")
                # logging.debug(f"IDs mostrados en UI (antes de actualizar): {displayed_order_ids}")


                # --- Lógica de Sincronización ---
                with ui_lock: # Proteger el acceso a listacartas.controls y displayed_order_ids
                    needs_update = False

                    # 1. Identificar Tarjetas para Añadir
                    ids_to_add = current_active_ids_from_db - displayed_order_ids
                    if ids_to_add:
                        logging.info(f"Nuevos pedidos para añadir a la UI: {ids_to_add}")
                        for order_id in ids_to_add:
                            pedido_completo = current_active_orders[order_id]
                            items_pedido = pedido_completo.strip().split('\n')
                            # Asegúrate que create_info_card acepta 'order_id' y 'on_complete_callback'
                            # y que guarda el order_id en la tarjeta (ej. card.data = order_id)
                            nueva_tarjeta = create_info_card(
                                order_id=order_id, # Pasa el ID real
                                title=f"Pedido #{order_id}",
                                description='\n'.join(items_pedido),
                                #creator=int(f"Pedido #{order_id}"), # Usar ID tiene más sentido
                                # Pasar una lambda que llame a la función de completar/eliminar con el ID correcto
                                on_complete_callback=lambda e, oid=order_id: _eliminar_tarjeta_y_actualizar_db(oid)
                                # ^ Cambié 'on_eliminar_callback' a 'on_complete_callback' para claridad
                            )
                            # ¡Muy importante! Guardar el ID en la tarjeta para referencia futura
                            nueva_tarjeta.data= order_id

                            listacartas.controls.append(nueva_tarjeta)
                            displayed_order_ids.add(order_id) # Marcar como mostrado en esta instancia
                            needs_update = True
                            logging.info(f"Tarjeta para pedido ID: {order_id} añadida a la UI.")

                    # 2. Identificar Tarjetas para Eliminar
                    ids_to_remove = displayed_order_ids - current_active_ids_from_db
                    if ids_to_remove:
                        logging.info(f"Pedidos ya no activos, eliminar de la UI: {ids_to_remove}")
                        controls_to_remove = []
                        for control in listacartas.controls:
                            # Buscar la tarjeta por su ID guardado en .data
                            if hasattr(control, 'data') and control.data in ids_to_remove:
                                controls_to_remove.append(control)

                        for control in controls_to_remove:
                             control_id = control.data # Guardar ID antes de remover
                             listacartas.controls.remove(control)
                             if control_id in displayed_order_ids: # Asegurar consistencia del set
                                 displayed_order_ids.remove(control_id)
                             needs_update = True
                             logging.info(f"Tarjeta para pedido ID: {control_id} eliminada de la UI.")


                # 3. Actualizar la página Flet SI hubo cambios
                if needs_update and page:
                    try:
                        page.update()
                        # logging.debug("page.update() llamado.")
                    except Exception as update_err:
                         # Flet puede dar error si la página se está cerrando justo ahora
                         logging.error(f"Error durante page.update(): {update_err}")
                         break # Salir del bucle si la página ya no es válida


            except mysql.connector.Error as err:
                logging.error(f"Error de base de datos en el hilo de actualización: {err}")
                # Esperar un poco más antes de reintentar en caso de error de BD
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error inesperado en el hilo de actualización: {e}", exc_info=True)
                # Esperar antes de reintentar
                time.sleep(5)

            # Espera antes de la próxima verificación
            time.sleep(1.5) # Puedes ajustar este intervalo

    # --- Configuración Inicial de la Vista ---
    texto_esperando = ft.Row(
        [
            ft.Icon(ft.icons.HOURGLASS_EMPTY_ROUNDED, size=30, color=ft.colors.BLUE_ACCENT_700),
            ft.Text("Esperando pedidos...", size=22, weight=ft.FontWeight.BOLD),
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    navegacion = crear_navegacion(page) # Asume que esta función existe

    # --- Creación e inicio del Hilo ---
    logging.info("Iniciando hilo de actualización...")
    hilo = threading.Thread(
        target=tarea_actualizacion,
        args=(page,), # Solo pasamos la página
        daemon=True
    )
    hilo.start()
    logging.info("Hilo iniciado.")

    # --- Definición de la Vista ---
    vi = ft.View(
        route="/home",
        controls=[
            listacartas,      # El ResponsiveRow donde se añadirán las tarjetas
            texto_esperando,  # Puedes ocultarlo cuando haya tarjetas si quieres
            navegacion
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START, # Empezar desde arriba
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=20,
        bgcolor=ft.colors.BLUE_GREY_50
    )

    return vi

# --- Asunciones sobre tu código de Utilidades ---
# 1. Necesitas una columna 'id' (INT AUTO_INCREMENT PRIMARY KEY) en tu tabla 'pedidos'.
# 2. Tu función `create_info_card` debe ser modificada para:
#    - Aceptar un parámetro `order_id`.
#    - Aceptar un parámetro `on_complete_callback` (o como lo llames).
#    - Crear un botón (o ícono) dentro de la tarjeta que, al ser presionado, llame a `on_complete_callback` pasándole el `order_id`.
#    - Ejemplo DENTRO de `create_info_card`:
#      ```python
#      def create_info_card(order_id, title, description, on_complete_callback, ...):
#          # ... creación de la tarjeta ...
#          complete_button = ft.ElevatedButton(
#              "Completar",
#              icon=ft.icons.CHECK_CIRCLE,
#              # Usar una lambda para pasar el ID específico a la función callback
#              on_click=lambda e, oid=order_id: on_complete_callback(e, oid)
#          )
#          card_content = ft.Column([
#              ft.Text(title),
#              ft.Text(description),
#              complete_button
#          ])
#          card = ft.Card(content=card_content, ...)
#          # Guardar el ID en la tarjeta es crucial para la lógica de eliminación
#          card.data = order_id
#          return card
#      ```
# 3. Tu función `crear_navegacion(page)` existe y devuelve un control Flet.

# --- Para ejecutar (ejemplo básico) ---
# if __name__ == "__main__":
#     def main(page: ft.Page):
#         page.title = "Pedidos App"
#         page.vertical_alignment = ft.MainAxisAlignment.START
#         page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
#
#         # Limpiar IDs mostrados al iniciar una nueva sesión/página
#         global displayed_order_ids
#         displayed_order_ids = set()
#
#         home_view = View_home(page)
#         page.views.append(home_view) # Añadir la vista inicial
#         page.update()
#
#     ft.app(target=main) # , view=ft.AppView.WEB_BROWSER) # Puedes probar en web también