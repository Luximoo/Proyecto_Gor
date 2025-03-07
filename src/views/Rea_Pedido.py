import flet as ft
from Utilidades.utils import *


def View_RealizarPedido(page):
    navegacion = crear_navegacion(page)
    gorLista = ft.ExpansionTile(
            title=ft.Text("Gorditas"),
            leading=ft.Icon(ft.icons.INFO_OUTLINE, color="#4A90E2"),
            icon_color="#4A90E2",
            shape=ft.RoundedRectangleBorder(radius=12),
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
    textfielC = []
    valores = [0,0,0]
    botones_suma = []
    botones_resta = []
    columna = ft.Column()
    for va in range (3):
        textoG.append(ft.Container(
                content=ft.Text(f"{guisosT[va]}",size=16,  # Tamaño del texto
                    weight=ft.FontWeight.BOLD,  # Negrita
                    color="#333333"),
                width=120,  # Ocupa el espacio disponible pero sin empujar demasiado
                alignment=ft.alignment.center_left,
                padding=ft.padding.symmetric(horizontal=15, vertical=10),  # Espaciado interno
                bgcolor= ft.colors.ORANGE,  # Fondo del contenedor
                border_radius=10,  # Bordes redondeados
                shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),  # Sombra ligera
            ))
        textfielC.append(ft.TextField(label="Comentario: ",width=50))
        botones_suma.append(ft.IconButton(ft.Icons.ADD,on_click=incrementar(va),icon_size=20,
                    icon_color="white",
                    style=ft.ButtonStyle(
                        bgcolor="#4A90E2",  # Azul moderno
                        shape=ft.RoundedRectangleBorder(radius=12),  # Bordes redondeados
                        elevation=3,  # Sombra para efecto 3D
                        padding=ft.padding.all(10),  # Tamaño del botón
                    ),))
        botones_resta.append(ft.IconButton(ft.Icons.REMOVE,on_click=decrementar(va),icon_size=20,
                    icon_color="white",
                    style=ft.ButtonStyle(
                        bgcolor="#4A90E2",  # Azul moderno
                        shape=ft.RoundedRectangleBorder(radius=12),  # Bordes redondeados
                        elevation=3,  # Sombra para efecto 3D
                        padding=ft.padding.all(10),  # Tamaño del botón
                    ),))
        textfiel.append(ft.TextField(value=valores[va],width=75,border_radius=12,
    border_color="#CCCCCC",
    focused_border_color="#4A90E2",))
        guisosF.append(ft.Row( alignment=ft.MainAxisAlignment.START,controls=[
        textoG[va],
        botones_resta[va],
        textfiel[va],
        botones_suma[va]    
        ]))
        columna.controls.append(guisosF[va])
        columna.controls.append(ft.Column(controls=[
                ft.Checkbox(label="Con queso", value=False),
                ft.Checkbox(label="Con Frijoles", value=False),
        ],spacing=0) )
        print(columna.controls[va])
    for va in range(6):
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
            ft.Divider(height=50),
            gorLista,
            navegacion,
            comprueba
        ]
    )
    return hol