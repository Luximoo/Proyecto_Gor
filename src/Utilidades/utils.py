import flet as ft
gradient_start_color = ft.colors.PURPLE_50 # Un púrpura muy claro, casi blanco
gradient_end_color = ft.colors.with_opacity(0.5, ft.colors.PURPLE_100) # Un poco más de púrpura, semitransparente
button_color = ft.colors.PURPLE_400
icon_placeholder_color = ft.colors.PURPLE_200
decorative_dot_color = ft.colors.with_opacity(0.5, ft.colors.PURPLE_300)
text_color_primary = ft.colors.BLACK87
text_color_secondary = ft.colors.BLACK54
text_color_tertiary = ft.colors.BLACK45
icon_button_color = ft.colors.WHITE # Icono blanco sobre fondo púrpura
text_button_color = ft.colors.WHITE
button_shadow_color = ft.colors.PURPLE_200
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
        carta = ft.Container(
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
                            ft.Text(description, weight=ft.FontWeight.BOLD, size=12, color=text_color_primary),
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
        return carta
def create_custom_tile_header(title_text, icon_name=ft.icons.APPS_OUTLINED):
        return ft.Container(
            # Este contenedor será el "title" del ExpansionTile
            # Le damos el gradiente y la estructura interna
            padding=ft.padding.symmetric(horizontal=16, vertical=12), # Padding interno
            border_radius=ft.border_radius.all(10), # Bordes redondeados para este contenedor
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[gradient_start_color, gradient_end_color],
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    # Sección Izquierda (Icono y decoración)
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(icon_name, size=26, color=icon_placeholder_color),
                            ft.Column(
                                 spacing=3,
                                 alignment=ft.MainAxisAlignment.CENTER,
                                 controls=[
                                     ft.Container(width=6, height=6, border_radius=3, bgcolor=decorative_dot_color),
                                     ft.Container(width=9, height=9, border_radius=4.5, bgcolor=decorative_dot_color),
                                 ]
                             )
                        ]
                    ),
                    # Título (expand=True para que ocupe el espacio)
                    ft.Text(title_text, weight=ft.FontWeight.BOLD, size=15, color=text_color_primary, expand=True),
                    # El icono de expandir/colapsar (trailing) lo añade automáticamente el ExpansionTile
                ]
            )
        )
def create_styled_button(button_text: str):

        # El contenido visual principal del botón
        return ft.Container(
            # Ancho: Podría ser fijo o adaptarse al contenido.
            # Para un botón, usualmente se adapta, pero con padding.
            # width=250, # Descomentar si necesitas un ancho fijo
            padding=ft.padding.symmetric(horizontal=24, vertical=16), # Padding generoso
            border_radius=ft.border_radius.all(12), # Radio para el gradiente
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[gradient_start_color, gradient_end_color],
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER, # Centrar contenido si no hay icono a la izquierda
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10, # Espacio entre icono/puntos y texto
                controls=[
                    # Sección Izquierda (Icono y decoración opcional),
                    ft.Text(
                        button_text,
                        weight=ft.FontWeight.BOLD,
                        size=15,
                        color=text_button_color
                    ),
                ]
            )
        )