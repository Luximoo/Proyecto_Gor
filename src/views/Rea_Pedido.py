import flet as ft
from Utilidades.utils import *


def View_RealizarPedido(page):
    navegacion = crear_navegacion(page)
    gorLista = ft.ExpansionTile(
            title=ft.Text("Gorditas"),
            affinity=ft.TileAffinity.PLATFORM,
            maintain_state=True,
            collapsed_text_color=ft.Colors.RED,
            text_color=ft.Colors.RED,       
            )
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
    textoG = []
    textfiel = []
    valores = [0,0,0]
    botones_suma = []
    botones_resta = []
    columna = ft.Column()
    for va in range (3):
        textoG.append(ft.Text(value=f"{guisosT[va]}",expand=True))
        botones_suma.append(ft.IconButton(ft.Icons.ADD,on_click=incrementar(va)))
        botones_resta.append(ft.IconButton(ft.Icons.REMOVE,on_click=decrementar(va)))
        textfiel.append(ft.TextField(value=valores[va],width=100))
        guisosF.append(ft.Row(controls=[
        textoG[va],
        botones_resta[va],
        textfiel[va],
        botones_suma[va]
        ]))
        columna.controls.append(guisosF[va])
        print(columna.controls[va])
        gorLista.controls.append(columna.controls[va])
    def prueba(e):
        for va in range (3):
            if int(textfiel[va].value) != 0:
                print(f"Gorditas de {guisosT[va]} {textfiel[va].value}")
            page.update()
    comprueba = ft.ElevatedButton(text="comprobar valor",on_click=prueba)   
    hol = ft.View(
        route="/",
        controls=[
            ft.Divider(height=4, color="green"),
            gorLista,
            navegacion,
            comprueba
        ]
    )
    return hol