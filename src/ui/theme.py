"""Paleta de colores, gradientes y constantes visuales de la aplicación."""

import flet as ft

# Gradientes principales (naranja cálido a rojo semitransparente)
COLOR_GRADIENTE_PRIMARIO_INICIO = ft.colors.ORANGE_ACCENT_400
COLOR_GRADIENTE_PRIMARIO_FIN = ft.colors.with_opacity(0.5, ft.colors.RED_ACCENT_700)
GRADIENTE_PRIMARIO = [COLOR_GRADIENTE_PRIMARIO_INICIO, COLOR_GRADIENTE_PRIMARIO_FIN]

# Gradiente oscuro/azul para botones de opciones y complementos
COLOR_GRADIENTE_BOTON_INICIO = ft.colors.BLACK87
COLOR_GRADIENTE_BOTON_FIN = ft.colors.with_opacity(0.5, ft.colors.BLUE_700)
GRADIENTE_BOTON = [COLOR_GRADIENTE_BOTON_INICIO, COLOR_GRADIENTE_BOTON_FIN]

# Gradientes de acción (Realizar pedido / Eliminar última línea)
GRADIENTE_REALIZAR = [ft.colors.GREEN_ACCENT_700, ft.colors.GREEN_ACCENT_200]
GRADIENTE_ELIMINAR = [ft.colors.RED_ACCENT_700, ft.colors.RED_ACCENT_200]

# Colores de texto e iconos
COLOR_TEXTO_PRIMARIO = ft.colors.BLACK87
COLOR_TEXTO_TERCIARIO = ft.colors.BLACK45
COLOR_TEXTO_ETIQUETA = "#333333"
COLOR_TEXTO_BOTON = ft.colors.WHITE
COLOR_ICONO_PRINCIPAL = ft.colors.BLACK87
COLOR_PUNTO_DECORATIVO = ft.colors.with_opacity(0.5, ft.colors.BLACK87)

# Colores de contenedores, botones y controles
COLOR_FONDO_PAGINA = ft.colors.BLUE_GREY_50
COLOR_BOTON_CIRCULAR = ft.colors.BLACK87
COLOR_SOMBRA_BOTON = ft.colors.BLACK87
COLOR_BOTON_CONTADOR = "#4A90E2"
COLOR_BORDE_INPUT = "#CCCCCC"
COLOR_ETIQUETA_GORDITA = ft.colors.ORANGE_ACCENT_400
COLOR_ETIQUETA_SOPE = ft.colors.ORANGE
