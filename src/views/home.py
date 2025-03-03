import flet as ft
hola = ft.Text("hola mundo",size=20)
ho = True
def View_home(page):
    # Variable para almacenar el texto generado (vacía inicialmente)
    def cambiar(e):
        index = e.control.selected_index
        if(index == 0):
            page.go("/home")
        if(index == 2):
            page.go("/login")
        if(index == 1):
            page.go("/dashboard")
    navegacion = ft.NavigationBar(destinations=[
            ft.NavigationBarDestination(icon=ft.icons.EXPLORE,label="Explore"),
            ft.NavigationBarDestination(icon=ft.icons.COMMUTE,label="Comute"),
            ft.NavigationBarDestination(icon=ft.icons.BOOKMARK_BORDER,selected_icon=ft.icons.BOOKMARK,label="Explore")
        ],on_change= cambiar)
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
        route="/",
        controls=[
            ft.ElevatedButton("Generar texto", on_click=on_button_click),
            navegacion
        ]
    )

    return vi