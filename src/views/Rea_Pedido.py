import flet as ft
from Utilidades.utils import *
hola = ft.Text("hola mundo",size=20)
ho = True
def View_RealizarPedido(page):
    navegacion = crear_navegacion(page)
    hol = ft.View(
        route="/",
        controls=[
            ft.ExpansionTile(
            title=ft.Text("Gorditas"),
            affinity=ft.TileAffinity.PLATFORM,
            maintain_state=True,
            collapsed_text_color=ft.Colors.RED,
            text_color=ft.Colors.RED,
            controls=[
                ft.Column(controls=[
                    ft.Row(controls=[
                    ft.Text("Papas"),
                    ft.IconButton(icon=ft.icons.REMOVE),
                    ft.TextField(value=0,width=40),
                    ft.IconButton(icon=ft.icons.ADD)
                ]),
                    ft.Row(controls= [
                        ft.Text("Chicarron"),
                        ft.IconButton(icon=ft.icons.REMOVE),
                        ft.TextField(value=0,width=40),
                        ft.IconButton(icon=ft.icons.ADD)
                    ]),
                    ft.Row(controls= [
                        ft.Text("Huevo rojo"),
                        ft.IconButton(icon=ft.icons.REMOVE),
                        ft.TextField(value=0,width=40),
                        ft.IconButton(icon=ft.icons.ADD)
                    ]),

                ],alignment=ft.alignment.center)],
            ),
            navegacion
        ]
    )
    return hol