"""Punto de entrada principal de la aplicación y gestión de rutas."""

import flet as ft

# Compatibilidad bidireccional entre versiones de Flet (ft.colors / ft.Colors, ft.icons / ft.Icons)
_colors = getattr(ft, "Colors", getattr(ft, "colors", None))
_icons = getattr(ft, "Icons", getattr(ft, "icons", None))

if not hasattr(ft, "colors") and _colors:
    ft.colors = _colors
if not hasattr(ft, "icons") and _icons:
    ft.icons = _icons
if not hasattr(ft, "Colors") and _colors:
    ft.Colors = _colors
if not hasattr(ft, "Icons") and _icons:
    ft.Icons = _icons

# Compatibilidad entre flet-web 0.28.x y versiones recientes de FastAPI (que eliminaron openapi_prefix)
try:
    import inspect
    import fastapi

    if "openapi_prefix" not in inspect.signature(fastapi.FastAPI.__init__).parameters:
        _orig_fastapi_init = fastapi.FastAPI.__init__

        def _patched_fastapi_init(self, *args, **kwargs):
            kwargs.pop("openapi_prefix", None)
            return _orig_fastapi_init(self, *args, **kwargs)

        fastapi.FastAPI.__init__ = _patched_fastapi_init
except Exception:
    pass

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from views.corte import view_corte_dia
from views.editar_pedidos import view_editar_pedidos
from views.home import view_home
from views.pedido import view_realizar_pedido


def _extraer_pedido_id_de_ruta(ruta: str) -> int | None:
    """Si la ruta tiene formato `/pedido/{id}`, devuelve el entero `id`; si no, `None`."""
    partes = [p for p in ruta.strip("/").split("/") if p]
    if len(partes) == 2 and partes[0].lower() == "pedido" and partes[1].isdigit():
        return int(partes[1])
    return None


def main(page: ft.Page) -> None:
    """Inicializa la configuración de la ventana y registra el enrutador de vistas."""
    page.title = "Gorditas y Sopes - Gestión de Pedidos"
    page.theme_mode = ft.ThemeMode.LIGHT

    try:
        page.window.width = WINDOW_WIDTH
        page.window.height = WINDOW_HEIGHT
    except AttributeError:
        try:
            page.window_width = WINDOW_WIDTH
            page.window_height = WINDOW_HEIGHT
        except Exception:
            pass

    def route_change(_e: ft.RouteChangeEvent) -> None:
        ruta = page.route or "/home"

        # Si salimos de /home, detener inmediatamente el hilo de sondeo de cocina
        if ruta != "/home":
            stop_event = getattr(page, "_home_stop_event", None)
            if stop_event is not None:
                stop_event.set()

        page.views.clear()
        pedido_id_editar = _extraer_pedido_id_de_ruta(ruta)

        if pedido_id_editar is not None:
            page.views.append(view_realizar_pedido(page, pedido_id_editar=pedido_id_editar))
        elif ruta == "/corte":
            page.views.append(view_corte_dia(page))
        elif ruta == "/editar-pedidos":
            page.views.append(view_editar_pedidos(page))
        elif ruta in ("/Pedidos", "/pedido"):
            page.views.append(view_realizar_pedido(page))
        else:
            page.views.append(view_home(page))

        page.update()

    page.on_route_change = route_change
    page.go("/home")


if __name__ == "__main__":
    ft.app(target=main)
