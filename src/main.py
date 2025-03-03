import flet as ft
from views.home import *

def main(page: ft.Page):
    page.title = "Aplicación con múltiples vistas"
    page.theme_mode = "light"

    def route_change(route):
        page.views.clear()
        if page.route == "/":
           #page.views.append(menu_view(page))
            #page.views.append(menuView(page))
            page.views.append(View_home(page))
        """elif page.route == "/dashboard":
            page.views.append(View(page))
        elif page.route == "/login":
            page.views.append(menuView(page))
        elif page.route == "/home":
            page.views.append(menu_view(page))"""

        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)