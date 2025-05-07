import flet as ft
from Utilidades.utils import *
import mysql.connector



def View_RealizarPedido(page):
    items_data = [
        { "title": "Sistema Operativo", "icon": ft.icons.COMPUTER_OUTLINED, "details": "Contenido de Sistema Operativo..." },
        { "title": "Inteligencia Artificial", "icon": ft.icons.INSIGHTS_OUTLINED, "details": "Contenido de Inteligencia Artificial..." },
        { "title": "Estructuras de Datos", "icon": ft.icons.DATA_ARRAY_OUTLINED, "details": "Contenido de Estructuras de Datos..." }
    ]
    navegacion = crear_navegacion(page)
    son = 0
    resumen = ft.TextField(label="Resumen de pedido",disabled=True,multiline=True,min_lines=1,max_lines=10)
    def handle_dismissal(e):
        page.add(ft.Text("Bottom sheet dismissed"))
    bs2 = ft.Column(
            tight=True,
            scroll=ft.ScrollMode.ALWAYS
        )
    bs1= ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=12), # Padding interno
            border_radius=ft.border_radius.all(10), # Bordes redondeados para este contenedor
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[gradient_start_color, gradient_end_color],
            ),            
            content=bs2
        )
    bs = ft.BottomSheet(
        on_dismiss=handle_dismissal,
        content=bs1,
    )
    
    def conmas(index):
        def handler(e):
            global son
            print(f"de: {guisosT[son]} con: {guisosT[index]} {valores[son]}")
            resumen.value = resumen.value + f"{guisosT[son]} con {guisosT[index]} {valores[son]} \n"
            textfiel[son].value = 0
            page.update()
        return handler

    
    gorLista = ft.ExpansionTile(
            title=create_custom_tile_header("Gorditas",ft.icons.COMPUTER_OUTLINED),
            bgcolor=ft.colors.TRANSPARENT, # Para el fondo general del tile
            collapsed_bgcolor=ft.colors.TRANSPARENT, # Para el fondo cuando está colapsado
            tile_padding=ft.padding.all(0),
            maintain_state=True, # Para que el estado se mantenga
            )
    def holl(e):
        global son
        son = e.control.key
        page.open(bs)
    def incrementar(index):
        def handler(e):
            valores[index] += 1  # Incrementar el valor
            textfiel[index].value = str(valores[index])  # Actualizar el TextField
            page.update()
        return handler
    def decrementar(index):
        def handler(e):
            valores[index] -= 1  # Incrementar el valor
            textfiel[index].value = str(valores[index])  # Actualizar el TextField dasdasgdg
            page.update()
        return handler
    guisosT = ["Chicarron","Papas","Huevo rojo","Huevo verde","Nopales","Aldilla","Rajas","Chorizo"] 
    guisosF = []
    textoG = []
    textfiel = []
    textfielC = []
    valores = [0,0,0,0,0,0,0,0]
    botones_suma = []
    botones_resta = []
    botones_complemento = []
    columna = ft.Column(controls=[],scroll=ft.ScrollMode.ALWAYS)
    for va in range (len(guisosT)):
        botones_complemento.append(ft.ElevatedButton(data=[va],on_click=conmas(va),
                                content=create_styled_button(f"Con: {guisosT[va]}"),
                                style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12), # Mismo radio que el contenedor interno
                                padding=ft.padding.all(0), # ¡MUY IMPORTANTE! Sin padding extra del botón
                                elevation=4, # Sombra del botón
                                shadow_color=button_shadow_color, # Color de la sombra
                                )))
        bs2.controls.append(botones_complemento[va])
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
        #gorLista.controls.append(columna.controls[va])
        """columna.controls.append(ft.Column(controls=[
                ft.Checkbox(label="Con queso", value=False),
                ft.Checkbox(label="Con Frijoles", value=False),
        ],spacing=0) )"""
        columna.controls.append(ft.ElevatedButton(key=va,text="Opciones", on_click=holl))
        #print(columna.controls[va])
    for va in range(len(guisosT)*2):
        gorLista.controls.append(columna.controls[va])
    listaP=[]
    def prueba(e):
        for va in range (len(guisosT)):
            if int(textfiel[va].value) != 0:
                print(f"Gorditas de {guisosT[va]} {textfiel[va].value}")
                resumen.value = resumen.value + f"Gorditas de {guisosT[va]} {textfiel[va].value} \n"
                textfiel[va].value = 0
        resumen.value = resumen.value + "----------------------------------- \n"
        page.update()
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "gorditas"
    }
    def PedidoRealizado(e):
        pedido = resumen.value
        mydb = mysql.connector.connect(**db_config)
        mycursor = mydb.cursor()
        mycursor.execute(f"INSERT INTO pedidos (estado, pedido) VALUES (1, '{pedido}')")
        mydb.commit()
        mycursor.close()
        mydb.close()
        resumen.value = ""
    comprueba = ft.ElevatedButton(text="REALIZAR PEDIDO",on_click=PedidoRealizado,bgcolor=ft.colors.RED_300)   
    Agregar = ft.ElevatedButton(text="Agregar",bgcolor=ft.colors.CYAN_ACCENT_200,on_click=prueba)
    hol = ft.View(
        route="/Pedidos",
        controls=[
            ft.Divider(height=50),
            gorLista,
            navegacion,
            resumen,
            ft.ResponsiveRow(controls=[
                Agregar,
                comprueba
            ])
        ],
        scroll=ft.ScrollMode.AUTO
    )
    return hol