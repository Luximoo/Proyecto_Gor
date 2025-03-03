import flet as ft
from Utilidades.utils import *
hola = ft.Text("hola mundo",size=20)
ho = True
def View_RealizarPedido(page):
    navegacion = crear_navegacion(page)
    # Función que se llama cuando se presiona el botón
    def on_button_click(e):
        global ho
        if ho == True:
            vi.controls.append(hola)
            page.update()  # Actualiza la vista
            ho = False
        else: 
            vi.controls.remove(hola)
            page.update()
            ho = True
        page.update()  # Actualiza la vista
    vi = ft.View(
        route="/Pedidos",
        controls=[
            ft.Text(value="Pagina donde se realizaran los pedidos"),
            navegacion
        ]
    )

    return vi