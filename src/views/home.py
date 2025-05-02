import flet as ft
from Utilidades.utils import *
import mysql.connector
import time
import threading
hola = ft.Text("hola mundo",size=20)
ho = ''

def View_home(page):
    def tarea_actualizacion(page: ft.Page, texto_control: ft.Text):
        global ho
        """
        Esta función se ejecuta en segundo plano. Contiene el bucle
        que actualiza el control de texto y llama a page.update().
        """
        try:
            while True:
                # 1. Obtén o calcula los datos nuevos
                #      En este caso, la hora actual.
                hora_actual = time.strftime("%H:%M:%S %p") # Formato HH:MM:SS AM/PM
                db_config = {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "gorditas"
                }
                texto_completo_con_saltos = ""  # Inicializamos una cadena vacía
                mydb = mysql.connector.connect(**db_config)
                mycursor = mydb.cursor()
                mycursor.execute("SELECT pedido FROM pedidos WHERE estado = 1")
                resultados = mycursor.fetchall()
                texto_completo_con_saltos = ""  # Inicializamos una cadena vacía
                for fila in resultados:
                    texto_completo_con_saltos += fila[0]  # Concatenamos el texto de cada fila
                print("Texto completo con saltos de línea:")
                print(texto_completo_con_saltos)
                # 2. Actualiza la propiedad del control Flet
                #    Es importante asegurarse de que el control todavía existe.
                if texto_control: # Comprueba si el control aún es válido
                    texto_control.value = f"Pedidos> {texto_completo_con_saltos}"
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
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "gorditas"
    }
    texto_dinamico = ft.Text(
        "Esperando actualización...",
        size=30,
        text_align=ft.TextAlign.CENTER,
        width=page.width # Opcional: ajustar ancho
    )
    # Variable para almacenar el texto generado (vacía inicialmente)
    navegacion = crear_navegacion(page)
    mydb = mysql.connector.connect(**db_config)
    mycursor = mydb.cursor()
    mycursor.execute("SELECT pedido FROM pedidos WHERE estado = 1")
    resultados = mycursor.fetchall()
    texto_completo_con_saltos = ""  # Inicializamos una cadena vacía
    for fila in resultados:
        texto_completo_con_saltos += fila[0]  # Concatenamos el texto de cada fila

    # Ahora la variable 'texto_completo_con_saltos' contiene todo el texto
    # de todas las filas seleccionadas, manteniendo los saltos de línea (\n).

    # Ejemplo de cómo podrías imprimir esta variable:
    print("Texto completo con saltos de línea:")
    print(texto_completo_con_saltos)
    global ho
    ho = texto_completo_con_saltos
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
            ft.Text(value=texto_completo_con_saltos),
            texto_dinamico,
            navegacion
        ]
    )

    return vi