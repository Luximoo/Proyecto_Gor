import flet as ft
from views.home import *
from views.Rea_Pedido import *

def main(page: ft.Page):
    page.title = "Aplicación con múltiples vistas"
    page.theme_mode = "light"
    page.window.width = 375
    page.window.height = 667
    def route_change(route):
        page.views.clear()
        if page.route == "/home":
            page.views.append(View_home(page))
        elif page.route == "/Pedidos":
            page.views.append(View_RealizarPedido(page))
        """elif page.route == "/login":
            page.views.append(menuView(page))
        elif page.route == "/home":
            page.views.append(menu_view(page))"""

        page.update()
    page.on_route_change = route_change
    page.go("/home")

ft.app(target=main)