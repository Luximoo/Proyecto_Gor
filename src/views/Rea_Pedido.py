import flet as ft
from Utilidades.utils import *

gorPapas = ft.TextField(value=0,width=40)
gorchicharron = ft.TextField(value=0,width=40)
gorHuevoR = ft.TextField(value=0,width=40)


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
                    gorPapas,
                    ft.IconButton(icon=ft.icons.ADD)
                ]),
                    ft.Row(controls= [
                        ft.Text("Chicarron"),
                        ft.IconButton(icon=ft.icons.REMOVE),
                        gorchicharron,
                        ft.IconButton(icon=ft.icons.ADD)
                    ]),
                    ft.Row(controls= [
                        ft.Text("Huevo rojo"),
                        ft.IconButton(icon=ft.icons.REMOVE),
                        gorHuevoR,
                        ft.IconButton(icon=ft.icons.ADD)
                    ]),

                ],alignment=ft.alignment.center)],
            ),
            navegacion
        ]
    )
    return hol