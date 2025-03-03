import flet as ft
from Utilidades.utils import *
hola = ft.Text("hola mundo",size=20)
ho = True
def View_RealizarPedido(page):
    navegacion = crear_navegacion(page)
    # Función que se llama cuando se presiona el botón
    vi = ft.View(
        route="/Pedidos",
        controls=[
            ft.Text(value="Pagina donde se realizaran los pedidos"),
            navegacion
        ]
    )

    return vi