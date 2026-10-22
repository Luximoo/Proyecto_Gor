"""Paleta de colores, gradientes y constantes visuales de la aplicación."""

import flet as ft

# Compatibilidad con versiones de Flet (ft.colors vs ft.Colors, ft.icons vs ft.Icons)
colors = getattr(ft, "Colors", getattr(ft, "colors", None))
icons = getattr(ft, "Icons", getattr(ft, "icons", None))

if not hasattr(ft, "colors") and colors:
    ft.colors = colors
if not hasattr(ft, "icons") and icons:
    ft.icons = icons
if not hasattr(ft, "Colors") and colors:
    ft.Colors = colors
if not hasattr(ft, "Icons") and icons:
    ft.Icons = icons


def with_opacity(opacity: float, color: str) -> str:
    """Aplica opacidad a un color de forma compatible entre versiones de Flet."""
    for module in (colors, getattr(ft, "colors", None), getattr(ft, "Colors", None)):
        if module and hasattr(module, "with_opacity"):
            return module.with_opacity(opacity, color)
    return f"{color},{opacity}"


# Gradientes principales (naranja cálido para encabezados y tarjetas)
COLOR_GRADIENTE_PRIMARIO_INICIO = colors.ORANGE_ACCENT_400
COLOR_GRADIENTE_PRIMARIO_FIN = with_opacity(0.85, colors.RED_ACCENT_700)
GRADIENTE_PRIMARIO = [COLOR_GRADIENTE_PRIMARIO_INICIO, COLOR_GRADIENTE_PRIMARIO_FIN]

# Gradientes de acción y botones
GRADIENTE_AGREGAR = [colors.BLUE_700, colors.BLUE_500]
COLOR_GRADIENTE_BOTON_INICIO = colors.BLUE_GREY_800
COLOR_GRADIENTE_BOTON_FIN = colors.BLUE_GREY_600
GRADIENTE_BOTON = [COLOR_GRADIENTE_BOTON_INICIO, COLOR_GRADIENTE_BOTON_FIN]

# Gradientes de acción (Realizar pedido / Eliminar última línea)
GRADIENTE_REALIZAR = [colors.GREEN_700, colors.GREEN_500]
GRADIENTE_ELIMINAR = [colors.RED_700, colors.RED_500]

# Colores de texto e iconos
COLOR_TEXTO_PRIMARIO = colors.BLACK87
COLOR_TEXTO_TERCIARIO = colors.BLACK45
COLOR_TEXTO_ETIQUETA = "#333333"
COLOR_TEXTO_BOTON = colors.WHITE
COLOR_ICONO_PRINCIPAL = colors.BLACK87
COLOR_PUNTO_DECORATIVO = with_opacity(0.5, colors.BLACK87)

# Colores de contenedores, botones y controles
COLOR_FONDO_PAGINA = colors.BLUE_GREY_50
COLOR_BOTON_CIRCULAR = colors.BLACK87
COLOR_SOMBRA_BOTON = colors.BLACK87
COLOR_BOTON_CONTADOR = "#4A90E2"
COLOR_BORDE_INPUT = "#CCCCCC"
COLOR_ETIQUETA_GORDITA = colors.ORANGE_ACCENT_400
COLOR_ETIQUETA_SOPE = colors.ORANGE
