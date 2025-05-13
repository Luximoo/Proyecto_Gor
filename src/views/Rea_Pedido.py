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

    bs22 = ft.Column(
            tight=True,
            scroll=ft.ScrollMode.ALWAYS
        )
    bs11= ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=12), # Padding interno
            border_radius=ft.border_radius.all(10), # Bordes redondeados para este contenedor
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[gradient_start_color, gradient_end_color],
            ),            
            content=bs22
        )
    bss = ft.BottomSheet(
        on_dismiss=handle_dismissal,
        content=bs11,
    )
    
    def conmas(index):
        def handler(e):
            global son
            print(f" {valores[son]} gordita de: {guisosT[son]} con: {guisosT[index]}")
            resumen.value = resumen.value + f"{valores[son]} Gordita de {guisosT[son]} con {guisosT[index]}  \n"
            textfiel[son].value = 0
            valores[son] = 0
            page.close(bs)
            page.update()
        return handler
    def conmass(index):
        def handler(e):
            global son
            print(f"sope de: {guisosTT[son]} --> {guisosTTT[index]} {valoresa[son]}")
            resumen.value = resumen.value + f"{valoresa[son]} Sope de {guisosTT[son]} {guisosTTT[index]}  \n"
            textfiell[son].value = 0
            valoresa[son] = 0
            page.close(bss)
            page.update()
        return handler

    
    gorLista = ft.ExpansionTile(
            title=create_custom_tile_header("Gorditas",ft.icons.COMPUTER_OUTLINED),
            bgcolor=ft.colors.TRANSPARENT, # Para el fondo general del tile
            collapsed_bgcolor=ft.colors.TRANSPARENT, # Para el fondo cuando está colapsado
            tile_padding=ft.padding.all(0),
            maintain_state=True, # Para que el estado se mantenga
            )
    sopLista = ft.ExpansionTile(
            title=create_custom_tile_header("Sopes",ft.icons.COMPUTER_OUTLINED),
            bgcolor=ft.colors.TRANSPARENT, # Para el fondo general del tile
            collapsed_bgcolor=ft.colors.TRANSPARENT, # Para el fondo cuando está colapsado
            tile_padding=ft.padding.all(0),
            maintain_state=True, # Para que el estado se mantenga
            )
    def holl(e):
        global son
        son = e.control.key
        if(valores[son] !=0):
            page.open(bs)
    def holll(e):
        global son
        son = e.control.key
        if(valoresa[son] !=0):
            page.open(bss)
    def incrementar(index):
        def handler(e):
            valores[index] += 1  # Incrementar el valor
            textfiel[index].value = str(valores[index])  # Actualizar el TextField
            page.update()
        return handler
    def decrementar(index):
        def handler(e):
            if(int(textfiel[index].value) >=1):
                valores[index] -= 1  # Incrementar el valor
                textfiel[index].value = str(valores[index])  # Actualizar el TextField dasdasgdg
            page.update()
        return handler
    
    def incrementarr(index):
        def handler(e):
            valoresa[index] += 1  # Incrementar el valor
            textfiell[index].value = str(valoresa[index])  # Actualizar el TextField
            page.update()
        return handler
    def decrementarr(index):
        def handler(e):
            if(int(textfiell[index].value) >=1):
                valoresa[index] -= 1  # Incrementar el valor
                textfiell[index].value = str(valoresa[index])  # Actualizar el TextField dasdasgdg
            page.update()
        return handler
    guisosT = ["Chicharron","Papas","Huevo rojo","Huevo verde","Nopales","Aldilla","Rajas","Chorizo"] 
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
                bgcolor= ft.colors.ORANGE_ACCENT_400,  # Fondo del contenedor
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
    focused_border_color="#4A90E2",
    disabled=True))
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
        columna.controls.append(ft.ElevatedButton(key=va,content=create_styled_button_opciones(f"Opciones"), on_click=holl))
        #print(columna.controls[va])
    for va in range(len(guisosT)*2):
        gorLista.controls.append(columna.controls[va])
    listaP=[]

    #variables de controles de los sopes
    guisosTT = ["Chicharron","Papas","Huevo rojo","Huevo verde","Nopales","Aldilla","Rajas","Chorizo"]
    guisosTTT = ["Sin Cebolla","Sin Verdura","Sin Crema","Sin Queso","Con Chicharron","Con Papas","Con Huevo rojo","Con Huevo verde","Con Nopales","Con Aldilla","Con Rajas","Con Chorizo"]  
    guisosFF = []
    textoGG = []
    textfiell = []
    textfielCC = []
    valoresa = [0,0,0,0,0,0,0,0]
    botones_sumaa = []
    botones_restaa = []
    botones_complementoo = []
    columnaa = ft.Column(controls=[],spacing=10,scroll=ft.ScrollMode.ALWAYS)
    for va in range (len(guisosTTT)):
        botones_complementoo.append(ft.ElevatedButton(data=[va],on_click=conmass(va),
                                content=create_styled_button(f"{guisosTTT[va]}"),
                                style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12), # Mismo radio que el contenedor interno
                                padding=ft.padding.all(0), # ¡MUY IMPORTANTE! Sin padding extra del botón
                                elevation=4, # Sombra del botón
                                shadow_color=button_shadow_color, # Color de la sombra
                                )))
        bs22.controls.append(botones_complementoo[va])

    for va in range (len(guisosTT)):
        textoGG.append(ft.Container(
                content=ft.Text(f"{guisosTT[va]}",size=16,  # Tamaño del texto
                    weight=ft.FontWeight.BOLD,  # Negrita
                    color="#333333"),
                width=120,  # Ocupa el espacio disponible pero sin empujar demasiado
                alignment=ft.alignment.center_left,
                padding=ft.padding.symmetric(horizontal=15, vertical=10),  # Espaciado interno
                bgcolor= ft.colors.ORANGE,  # Fondo del contenedor
                border_radius=10,  # Bordes redondeados
                shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
                expand=True# Sombra ligera
            ))
        textfielCC.append(ft.TextField(label="Comentario: ",width=50,expand=True))
        botones_sumaa.append(ft.IconButton(ft.Icons.ADD,on_click=incrementarr(va),icon_size=20,
                    icon_color="white",
                    expand=True,
                    style=ft.ButtonStyle(
                        bgcolor="#4A90E2",  # Azul moderno
                        shape=ft.RoundedRectangleBorder(radius=12),  # Bordes redondeados
                        elevation=3,  # Sombra para efecto 3D
                        padding=ft.padding.all(10),  # Tamaño del botón
                    ),))
        botones_restaa.append(ft.IconButton(ft.Icons.REMOVE,on_click=decrementarr(va),icon_size=20,
                    icon_color="white",
                    expand=True,
                    style=ft.ButtonStyle(
                        bgcolor="#4A90E2",  # Azul moderno
                        shape=ft.RoundedRectangleBorder(radius=12),  # Bordes redondeados
                        elevation=3,  # Sombra para efecto 3D
                        padding=ft.padding.all(10),  # Tamaño del botón
                    ),))
        textfiell.append(ft.TextField(value=valores[va],width=75,border_radius=12,
    border_color="#CCCCCC",
    focused_border_color="#4A90E2",
    disabled=True,expand=True))
        guisosFF.append(ft.Row(expand=True,alignment=ft.MainAxisAlignment.START,controls=[
        textoGG[va],
        botones_restaa[va],
        textfiell[va],
        botones_sumaa[va]    
        ]))
        columnaa.controls.append(guisosFF[va])
        #gorLista.controls.append(columna.controls[va])
        """columna.controls.append(ft.Column(controls=[
                ft.Checkbox(label="Con queso", value=False),
                ft.Checkbox(label="Con Frijoles", value=False),
        ],spacing=0) )"""
        columnaa.controls.append(ft.ElevatedButton(key=va,content=create_styled_button_opciones(f"Opciones"), on_click=holll))
        #print(columna.controls[va])
    for va in range(len(guisosT)*2):
        sopLista.controls.append(columnaa.controls[va])


















    def prueba(e):
        for va in range (len(guisosT)):
            if int(textfiel[va].value) != 0:
                print(f"Gorditas de {guisosT[va]} {textfiel[va].value}")
                resumen.value = resumen.value + f" {textfiel[va].value} Gordita de {guisosT[va]}\n"
                textfiel[va].value = 0
                valores[va] = 0
        for va in range (len(guisosTT)):
            if int(textfiell[va].value) != 0:
                print(f"Gorditas de {guisosTT[va]} {textfiell[va].value}")
                resumen.value = resumen.value + f" {textfiell[va].value} Sope de {guisosTT[va]}\n"
                textfiell[va].value = 0
                valoresa[va] = 0
        resumen.value = resumen.value + "-----------------------------------\n"
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
    def ante(e):
        resumen.value = eliminar_ultima_linea(resumen.value)
        resumen.value = resumen.value + "\n"
        resumen.update()
    def eliminar_ultima_linea(texto):
        lineas = texto.splitlines()
        if lineas:  # Asegurarse de que la lista de líneas no esté vacía
            lineas_sin_ultima = lineas[:-1]
            return "\n".join(lineas_sin_ultima)
        else:
            return ""  # Si la cadena está vacía, devuelve una cadena vacía
    comprueba = ft.ElevatedButton(text="REALIZAR PEDIDO",on_click=PedidoRealizado,content=create_styled_button_Realizar(f"Realizar Pedido"))   
    Agregar = ft.ElevatedButton(text="Agregar",content=create_styled_button_opciones(f"Agregar a Pedido"),on_click=prueba)
    Eliminar = ft.ElevatedButton(text="REALIZAR PEDIDO",on_click=ante,content=create_styled_button_eliminar(f"<-"))
    hol = ft.View(
        route="/Pedidos",
        controls=[
            ft.Divider(height=50),
            ft.Column(controls=[
            Agregar,
            Eliminar,
            comprueba],expand=True),
            gorLista,
            sopLista,
            resumen,
            navegacion
            ,
        ],
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment = ft.MainAxisAlignment.CENTER, # Centra el contenido verticalmente en la página
        horizontal_alignment = ft.CrossAxisAlignment.CENTER, # Centra el contenido horizontalmente en la página
        padding = 20, # Añade un poco de padding alrededor de la página
        bgcolor = ft.colors.BLUE_GREY_50, # Un color de fondo suave para la página
    )
    return hol