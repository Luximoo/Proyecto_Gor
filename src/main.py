"""Punto de entrada principal de la aplicación y gestión de rutas."""

import flet as ft

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from views.home import view_home
from views.pedido import view_realizar_pedido


def main(page: ft.Page) -> None:
    """Inicializa la configuración de la ventana y registra el enrutador de vistas."""
    page.title = "Gorditas y Sopes - Gestión de Pedidos"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT

    def route_change(_e: ft.RouteChangeEvent) -> None:
        # Si salimos de /home, detener inmediatamente el hilo de sondeo de cocina
        if page.route != "/home":
            stop_event = getattr(page, "_home_stop_event", None)
            if stop_event is not None:
                stop_event.set()

        page.views.clear()
        if page.route == "/Pedidos":
            page.views.append(view_realizar_pedido(page))
        else:
            page.views.append(view_home(page))

        page.update()

    page.on_route_change = route_change
    page.go("/home")


if __name__ == "__main__":
    ft.app(target=main)
