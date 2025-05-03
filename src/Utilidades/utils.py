import flet as ft
gradient_start_color = ft.colors.PURPLE_50 # Un púrpura muy claro, casi blanco
gradient_end_color = ft.colors.with_opacity(0.5, ft.colors.PURPLE_100) # Un poco más de púrpura, semitransparente
button_color = ft.colors.PURPLE_400
icon_placeholder_color = ft.colors.PURPLE_200
decorative_dot_color = ft.colors.with_opacity(0.5, ft.colors.PURPLE_300)
text_color_primary = ft.colors.BLACK87
text_color_secondary = ft.colors.BLACK54
text_color_tertiary = ft.colors.BLACK45
texto =  ft.Text("", weight=ft.FontWeight.BOLD, size=12, color=text_color_primary)
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
            ft.NavigationBarDestination(icon=ft.icons.EXPLORE, label="Pedidos"),
            ft.NavigationBarDestination(icon=ft.icons.COMMUTE, label="Ordenar"),
        ],
        on_change=lambda e: cambiar(page, e)  # Usamos una lambda para pasar el `page` a la función `cambiar`
    )
def create_info_card(title, description, creator):
        texto.value = description
        return ft.Container(
            width=450, # Ancho fijo para el ejemplo
            padding=ft.padding.all(20),
            margin=ft.margin.symmetric(vertical=10, horizontal=20), # Margen alrededor
            border_radius=ft.border_radius.all(15),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[gradient_start_color, gradient_end_color],
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, # Separa los elementos
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Sección Izquierda (Icono y decoración) - Simplificada
                    ft.Row(
                        spacing=5,
                        controls=[
                             # Icono principal placeholder
                            ft.Icon(ft.icons.COMPUTER_OUTLINED, size=35, color=icon_placeholder_color),
                            # Puntos decorativos
                             ft.Column(
                                 spacing=4,
                                 controls=[
                                     ft.Container(width=8, height=8, border_radius=4, bgcolor=decorative_dot_color),
                                     ft.Container(width=12, height=12, border_radius=6, bgcolor=decorative_dot_color),
                                 ]
                             )
                        ]
                    ),

                    # Sección Central (Textos) - Usamos expand=True para que ocupe el espacio disponible
                    ft.Column(
                        [
                            texto,
                            ft.Container(height=5), # Pequeño espacio
                            ft.Text(f"Created by {creator}", size=11, color=text_color_tertiary),
                        ],
                        spacing=4, # Espacio entre textos
                        alignment=ft.MainAxisAlignment.CENTER,
                        # Horizontal alignment might be needed depending on text length variation
                        # horizontal_alignment=ft.CrossAxisAlignment.START,
                        expand=True # Importante para empujar el botón a la derecha
                    ),

                    # Sección Derecha (Botón)
                    ft.Container(
                        content=ft.Icon(ft.icons.CHEVRON_RIGHT_ROUNDED, color=ft.colors.WHITE),
                        width=40,
                        height=40,
                        bgcolor=button_color,
                        border_radius=20, # Mitad del ancho/alto para hacerlo círculo
                        alignment=ft.alignment.center,
                        ink=True, # Efecto visual al hacer clic
                        on_click=lambda e: print(f"Botón '{title}' presionado!"),
                    ),
                ],
            ),
        )
