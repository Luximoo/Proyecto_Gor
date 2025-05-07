import flet as ft
from Utilidades.utils import *
import Utilidades.utils
import mysql.connector
import time
import threading
hola = ft.Text("hola mundo",size=20)
listacartas=ft.ResponsiveRow()
contador= 0
def View_home(page):
    def tarea_actualizacion(page: ft.Page, texto_control: ft.Text):
        global ho
        """
        Esta función se ejecuta en segundo plano. Contiene el bucle
        que actualiza el control de texto y llama a page.update().
        """
        try:
            while True:
                db_config = {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "gorditas"
                }
                texto_completo_con_saltos = ""  # Inicializamos una cadena vacía
                mydb = mysql.connector.connect(**db_config)
                mycursor = mydb.cursor()
                mycursor.execute("SELECT COUNT(*) FROM pedidos WHERE estado = 1")
                resultados = mycursor.fetchall()
                for va in resultados:
                    for vaa in va:
                        aux = vaa
                mycursor.execute("SELECT pedido FROM pedidos WHERE estado = 1")
                resultados = mycursor.fetchall()
                if(resultados):
                    for i, fila in enumerate(resultados):
                        global contador
                        contador = contador + 1
                        pedido_completo = fila[0]
                        items_pedido = pedido_completo.strip().split('\n')  # Divide la cadena por saltos de línea
                        print('\n'.join(items_pedido))
                        listacartas.controls.append(
                            create_info_card(
                                title=f"Pedido #{i+1}",
                                description='\n'.join(items_pedido), # Muestra todos los items en la descripción
                                creator=f"Pedido #{contador}"
                            )
                        )
                mycursor.execute("UPDATE pedidos SET estado = 2 WHERE estado = 1")
                mydb.commit()
                
                print("Texto completo con saltos de línea:")
                # 2. Actualiza la propiedad del control Flet
                #    Es importante asegurarse de que el control todavía existe.
                if texto_control: # Comprueba si el control aún es válido
                    texto_control.value ="Esperando pedidos..."
                else:
                    print("El control de texto ya no existe.")
                    break # Salir si el control fue eliminado

                # 3. Llama a page.update() para enviar los cambios a la UI
                #    Esto debe hacerse para que el usuario vea el cambio.
                if page: # Comprueba si la página aún es válida
                    page.update()
                else:
                    print("La página ya no existe.")
                    break # Salir si la página fue cerrada

                # 4. Espera un intervalo antes de la próxima actualización
                #    Ajusta este valor según necesites (ej: 0.5 para medio segundo)
                time.sleep(1) # Actualiza cada 1 segundo

        except Exception as e:
        # Captura cualquier error inesperado en el hilo
            print(f"Error en el hilo de actualización: {e}")
    texto_dinamico = ft.Text(
        "Esperando actualización...",
        size=30,
        text_align=ft.TextAlign.CENTER,
        width=page.width # Opcional: ajustar ancho
    )
    # Variable para almacenar el texto generado (vacía inicialmente)
    navegacion = crear_navegacion(page) 
    # Función que se llama cuando se presiona el botón

    # --- Creación e inicio del Hilo (Thread) ---
    print("Iniciando hilo de actualización...")
    hilo = threading.Thread(
        target=tarea_actualizacion,  # La función que ejecutará el hilo
        args=(page, texto_dinamico), # Argumentos para la función target
        daemon=True                  # True = El hilo termina si el programa principal cierra
    )
    hilo.start() # Inicia la ejecución del hilo en segundo plano
    print("Hilo iniciado.")
    vi = ft.View(
        route="/home",
        controls=[
            listacartas,
            texto_dinamico,
            navegacion
        ],
        scroll=ft.ScrollMode.AUTO
    )

    return vi