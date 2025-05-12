import flet as ft
gradient_start_color = ft.colors.ORANGE_ACCENT_400
gradient_end_color = ft.colors.with_opacity(0.5, ft.colors.RED_ACCENT_700) # Un poco más de púrpura, semitransparente
gradient_start_colorr = ft.colors.BLACK87 # Un púrpura muy claro, casi blanco
gradient_end_colorr = ft.colors.with_opacity(0.5, ft.colors.BLUE_700 ) # Un poco más de púrpura, semitransparente
gradient_start_colorrr = ft.colors.RED_ACCENT_700 # Un púrpura muy claro, casi blanco
gradient_end_colorrr = ft.colors.with_opacity(0.5, ft.colors.BLUE_GREY_400 ) # Un poco más de púrpura, semitransparente
button_color = ft.colors.BLACK87
icon_placeholder_color = ft.colors.BLACK87
decorative_dot_color = ft.colors.with_opacity(0.5, ft.colors.BLACK87)
text_color_primary = ft.colors.BLACK87
text_color_secondary = ft.colors.BLACK54
text_color_tertiary = ft.colors.BLACK45
icon_button_color = ft.colors.WHITE # Icono blanco sobre fondo púrpura
text_button_color = ft.colors.WHITE
button_shadow_color = ft.colors.BLACK87
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
def create_info_card(title, description, creator,on_eliminar_callback):
    def eliminar(e):
        on_eliminar_callback(info_card)
    info_card = ft.Container(
        width=450,  # Ancho fijo para la tarjeta. Considera hacerlo responsivo si es necesario.
        padding=ft.padding.all(20),
        margin=ft.margin.symmetric(vertical=10, horizontal=20),
        border_radius=ft.border_radius.all(15),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[gradient_start_color, gradient_end_color],
        ),
        shadow=ft.BoxShadow( # Sombra sutil para dar profundidad
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.2, ft.colors.BLACK),
            offset=ft.Offset(5, 5),
        ),
        content=ft.ResponsiveRow(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Sección Izquierda (Icono y decoración)
                ft.Row(
                    spacing=10, # Aumentado el espaciado para mejor visualización
                    controls=[
                        ft.Icon(ft.icons.COMPUTER_OUTLINED, size=40, color=icon_placeholder_color), # Tamaño de icono ligeramente aumentado
                        ft.Column(
                            spacing=5, # Espaciado entre puntos
                            controls=[
                                ft.Container(width=8, height=8, border_radius=4, bgcolor=decorative_dot_color),
                                ft.Container(width=12, height=12, border_radius=6, bgcolor=decorative_dot_color),
                            ]
                        )
                    ],
                    # Columna para ResponsiveRow (ocupa 2 de 12 columnas en pantallas grandes)
                    col={"sm": 2, "md": 2} 
                ),

                # Sección Central (Textos)
                ft.Column(
                    [
                        ft.Text(
                            description,
                            weight=ft.FontWeight.BOLD,
                            size=22, # Tamaño de fuente aumentado para descripción
                            color=text_color_primary,
                            text_align=ft.TextAlign.CENTER # Asegura centrado del texto
                        ),
                        ft.Container(height=8), # Espacio aumentado
                        ft.Text(
                            f"{creator}", # Texto más descriptivo
                            size=16, # Tamaño de fuente aumentado para creador
                            color=text_color_tertiary,
                            text_align=ft.TextAlign.CENTER, # Asegura centrado del texto
                            italic=True
                        ),
                    ],
                    spacing=5, # Espacio entre textos
                    alignment=ft.MainAxisAlignment.CENTER, # Centra los elementos verticalmente en la columna
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, # Centra los elementos horizontalmente en la columna
                    expand=True, # Permite que esta columna ocupe el espacio disponible
                    # Columna para ResponsiveRow (ocupa 8 de 12 columnas en pantallas grandes, dejando espacio para icono y botón)
                    col={"sm": 8, "md": 8} 
                ),

                # Sección Derecha (Botón)
                ft.Container(
                    content=ft.Icon(ft.icons.CHEVRON_RIGHT_ROUNDED, color=ft.colors.WHITE, size=24),
                    width=45, # Ligeramente más grande para mejor toque/clic
                    height=45,
                    bgcolor=button_color,
                    border_radius=22.5, # Mitad del ancho/alto para hacerlo círculo
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=eliminar,
                    # Columna para ResponsiveRow (ocupa 2 de 12 columnas en pantallas grandes)
                    col={"sm": 2, "md": 2}
                ),
            ],
        ),
    )
    return info_card
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
                colors=[gradient_start_colorr, gradient_end_colorr],
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
def create_styled_button_opciones(button_text: str):

        # El contenido visual principal del botón
        return ft.Container(
            # Ancho: Podría ser fijo o adaptarse al contenido.
            # Para un botón, usualmente se adapta, pero con padding.
            # width=250, # Descomentar si necesitas un ancho fijo
            padding=ft.padding.symmetric(horizontal=12, vertical=8), # Padding generoso
            border_radius=ft.border_radius.all(12), # Radio para el gradiente
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[gradient_start_colorr, gradient_end_colorr],
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
def create_styled_button_Realizar(button_text: str):

        # El contenido visual principal del botón
        return ft.Container(
            # Ancho: Podría ser fijo o adaptarse al contenido.
            # Para un botón, usualmente se adapta, pero con padding.
            # width=250, # Descomentar si necesitas un ancho fijo
            padding=ft.padding.symmetric(horizontal=10, vertical=8), # Padding generoso
            border_radius=ft.border_radius.all(12), # Radio para el gradiente
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[gradient_start_colorrr, gradient_end_colorrr],
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