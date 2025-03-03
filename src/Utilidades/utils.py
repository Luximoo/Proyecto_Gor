import flet as ft

# Función para manejar el cambio de vista
def cambiar(page, e):
    index = e.control.selected_index
    if index == 0:
        page.go("/home")
    elif index == 1:
        page.go("/Pedidos")
    elif index == 2:
        page.go("/dashboard")

# Función para crear la barra de navegación
def crear_navegacion(page):
    return ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.EXPLORE, label="Explore"),
            ft.NavigationBarDestination(icon=ft.icons.COMMUTE, label="Comute"),
            ft.NavigationBarDestination(
                icon=ft.icons.BOOKMARK_BORDER,
                selected_icon=ft.icons.BOOKMARK,
                label="Explore"
            )
        ],
        on_change=lambda e: cambiar(page, e)  # Usamos una lambda para pasar el `page` a la función `cambiar`
    )
