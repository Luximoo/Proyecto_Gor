import flet as ft

from Utilidades.utils import create_info_card, crear_navegacion

import mysql.connector
import time
import threading
import logging 


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


ui_lock = threading.Lock()

displayed_order_ids = set()


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
            mycursor.execute("UPDATE pedidos SET estado = 3 WHERE id = %s AND estado = 1", (order_id_to_delete,))
            mydb.commit()
            logging.info(f"Pedido ID: {order_id_to_delete} marcado como completado en DB (si existía con estado 1). Filas afectadas: {mycursor.rowcount}")
            mycursor.close()
            mydb.close()

           
            with ui_lock:
                card_to_remove = None
                for card in listacartas.controls:
                     
                    if hasattr(card, 'data') and card.data == order_id_to_delete:
                        card_to_remove = card
                        break
                if card_to_remove:
                    listacartas.controls.remove(card_to_remove)
                    if order_id_to_delete in displayed_order_ids:
                         displayed_order_ids.remove(order_id_to_delete)
                    logging.info(f"Tarjeta para pedido ID: {order_id_to_delete} eliminada de la UI inmediatamente.")
                    if page: 
                         page.update()
                else:
                     logging.warning(f"No se encontró la tarjeta con ID {order_id_to_delete} para eliminarla inmediatamente.")


        except mysql.connector.Error as err:
            logging.error(f"Error de base de datos al actualizar pedido {order_id_to_delete}: {err}")
        except Exception as e:
            logging.error(f"Error inesperado al procesar eliminación de pedido {order_id_to_delete}: {e}")

    def get_db_config():
        
        return {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "gorditas",
            "autocommit": False 
        }

    def tarea_actualizacion(page: ft.Page):
        """
        Hilo que consulta periódicamente la BD y actualiza la UI para reflejar
        los pedidos con estado = 1. No modifica el estado en la BD.
        """
        global displayed_order_ids

        while True:
            if not page: 
                logging.info("La página no existe, deteniendo hilo de actualización.")
                break

            current_active_orders = {} 
            try:
                db_config = get_db_config()
                mydb = mysql.connector.connect(**db_config)
                mycursor = mydb.cursor()

               
                mycursor.execute("SELECT id, pedido FROM pedidos WHERE estado = 1")
                resultados = mycursor.fetchall()
                mycursor.close()
                mydb.close()

                
                for order_id, pedido_data in resultados:
                    current_active_orders[order_id] = pedido_data

                current_active_ids_from_db = set(current_active_orders.keys())
              


               
                with ui_lock: 
                    needs_update = False

                   
                    ids_to_add = current_active_ids_from_db - displayed_order_ids
                    if ids_to_add:
                        logging.info(f"Nuevos pedidos para añadir a la UI: {ids_to_add}")
                        for order_id in ids_to_add:
                            pedido_completo = current_active_orders[order_id]
                            items_pedido = pedido_completo.strip().split('\n')
                            nueva_tarjeta = create_info_card(
                                order_id=order_id, # Pasa el ID real
                                title=f"Pedido #{order_id}",
                                description='\n'.join(items_pedido),
                                on_complete_callback=lambda e, oid=order_id: _eliminar_tarjeta_y_actualizar_db(oid)
                              
                            )
                        
                            nueva_tarjeta.data= order_id

                            listacartas.controls.append(nueva_tarjeta)
                            displayed_order_ids.add(order_id) 
                            needs_update = True
                            logging.info(f"Tarjeta para pedido ID: {order_id} añadida a la UI.")

                   
                    ids_to_remove = displayed_order_ids - current_active_ids_from_db
                    if ids_to_remove:
                        logging.info(f"Pedidos ya no activos, eliminar de la UI: {ids_to_remove}")
                        controls_to_remove = []
                        for control in listacartas.controls:
                        
                            if hasattr(control, 'data') and control.data in ids_to_remove:
                                controls_to_remove.append(control)

                        for control in controls_to_remove:
                             control_id = control.data 
                             listacartas.controls.remove(control)
                             if control_id in displayed_order_ids: 
                                 displayed_order_ids.remove(control_id)
                             needs_update = True
                             logging.info(f"Tarjeta para pedido ID: {control_id} eliminada de la UI.")


               
                if needs_update and page:
                    try:
                        page.update()
                        
                    except Exception as update_err:
                         
                         logging.error(f"Error durante page.update(): {update_err}")
                         break


            except mysql.connector.Error as err:
                logging.error(f"Error de base de datos en el hilo de actualización: {err}")
               
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error inesperado en el hilo de actualización: {e}", exc_info=True)
               
                time.sleep(5)

            
            time.sleep(1.5) 

    
    texto_esperando = ft.Row(
        [
            ft.Icon(ft.icons.HOURGLASS_EMPTY_ROUNDED, size=30, color=ft.colors.BLUE_ACCENT_700),
            ft.Text("Esperando pedidos...", size=22, weight=ft.FontWeight.BOLD),
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    navegacion = crear_navegacion(page) 

   
    logging.info("Iniciando hilo de actualización...")
    hilo = threading.Thread(
        target=tarea_actualizacion,
        args=(page,),
        daemon=True
    )
    hilo.start()
    logging.info("Hilo iniciado.")

   
    vi = ft.View(
        route="/home",
        controls=[
            listacartas,      
            texto_esperando,  
            navegacion
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.START, # Empezar desde arriba
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=20,
        bgcolor=ft.colors.BLUE_GREY_50
    )

    return vi
