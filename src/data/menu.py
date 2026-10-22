"""Catálogo de guisos y opciones de personalización para los platillos."""

from dataclasses import dataclass

# Lista única de guisados disponibles (antes duplicada en guisosT y guisosTT)
GUISOS: list[str] = [
    "Chicharron",
    "Papas",
    "Huevo rojo",
    "Huevo verde",
    "Nopales",
    "Aldilla",
    "Rajas",
    "Chorizo",
]

# Modificadores exclusivos de sopes
MODIFICADORES_SOPE: list[str] = [
    "Sin Cebolla",
    "Sin Verdura",
    "Sin Crema",
    "Sin Queso",
]

# Lista de opciones para sopes (antes guisosTTT)
OPCIONES_SOPE: list[str] = [
    *MODIFICADORES_SOPE,
    *[f"Con {guiso}" for guiso in GUISOS],
]


@dataclass(frozen=True)
class OpcionComplemento:
    """Representa un botón de opción dentro del BottomSheet de un platillo."""

    etiqueta_boton: str
    texto_resumen: str


# Opciones estructuradas para reutilizar el mismo componente en Gorditas y Sopes
OPCIONES_COMPLEMENTO_GORDITA: list[OpcionComplemento] = [
    OpcionComplemento(etiqueta_boton=f"Con: {guiso}", texto_resumen=f"con {guiso}")
    for guiso in GUISOS
]

OPCIONES_COMPLEMENTO_SOPE: list[OpcionComplemento] = [
    OpcionComplemento(etiqueta_boton=opcion, texto_resumen=opcion)
    for opcion in OPCIONES_SOPE
]
