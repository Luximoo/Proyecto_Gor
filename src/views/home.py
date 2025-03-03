import flet as ft
from Utilidades.utils import *
hola = ft.Text("hola mundo",size=20)
ho = True
def View_home(page):
    # Variable para almacenar el texto generado (vacía inicialmente)
    navegacion = crear_navegacion(page)

    # Función que se llama cuando se presiona el botón
    vi = ft.View(
        route="/home",
        controls=[
            ft.Text(value="Pagina Principal: aqui se va a desarrollar como recomendaciones que poducto se vende mas cosas generales"),
            navegacion
        ]
    )

    return vi