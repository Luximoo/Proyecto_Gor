import flet as ft
from Utilidades.utils import *

gorPapas = ft.TextField(value=0,width=40)
gorchicharron = ft.TextField(value=0,width=40)
gorHuevoR = ft.TextField(value=0,width=40)
biblioteca = {}
lista = ft.ExpansionTile(
            title=ft.Text("Gorditas"),
            affinity=ft.TileAffinity.PLATFORM,
            maintain_state=True,
            collapsed_text_color=ft.Colors.RED,
            text_color=ft.Colors.RED,
            )
def View_RealizarPedido(page):
    navegacion = crear_navegacion(page)
    def incrementar(index):
        def handler(e):
            valores[index] += 1  # Incrementar el valor
            textfiel[index].value = str(valores[index])  # Actualizar el TextField
            page.update()
        return handler
    def decrementar(index):
        def handler(e):
            valores[index] -= 1  # Incrementar el valor
            textfiel[index].value = str(valores[index])  # Actualizar el TextField
            page.update()
        return handler
    guisosT = ["chicarron","papas","huevo rojo"] 
    guisosF = []
    textfiel = []
    valores = [0,0,0]
    botones_suma = []
    botones_resta = []
    columna = ft.Column()
    for va in range (3):
        botones_suma.append(ft.IconButton(ft.Icons.ADD,on_click=incrementar(va)))
    for va in range (3):
        botones_resta.append(ft.IconButton(ft.Icons.REMOVE,on_click=decrementar(va)))
    for va in range (3):
        textfiel.append(ft.TextField(value=valores[va]))
    for va in range (3):
        guisosF.append(ft.Row(controls=[
        botones_resta[va],
        textfiel[va],
        botones_suma[va]
        ]))
    for va in range (3):
        columna.controls.append(guisosF[va])
    def prueba(e):
        for va in range (3):
            if textfiel[va].value != 0:
                print(f"Gorditas de {guisosT[va]} {textfiel[va].value}")
    comprueba = ft.ElevatedButton(text="comprobar valor",on_click=prueba)   
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
            navegacion,
            columna,
            comprueba
        ]
    )
    return hol