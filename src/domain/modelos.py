"""Entidades del dominio y reglas de negocio para pedidos de Gorditas y Sopes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


PRECIOS_POR_DEFECTO: dict[str, float] = {
    "GORDITA": 17.0,
    "SOPE_FRIJOLES": 30.0,
    "SOPE_GUISO": 35.0,
    "QUESADILLA": 45.0,
}


def formatear_moneda(monto: float) -> str:
    """Formatea un monto en pesos (ej. '$85' si es entero o '$85.50' si tiene decimales)."""
    if abs(monto - round(monto)) < 0.005:
        return f"${int(round(monto))}"
    return f"${monto:.2f}"


class ErrorValidacionDominio(ValueError):
    """Excepción lanzada cuando una operación viola las reglas del dominio."""


class TipoServicio(str, Enum):
    """Modalidad de entrega del pedido."""

    MESA = "MESA"
    LLEVAR = "LLEVAR"

    @property
    def etiqueta(self) -> str:
        return "Mesa" if self == TipoServicio.MESA else "Para llevar"


class EstadoPedido(str, Enum):
    """Estados posibles de un pedido en el sistema."""

    PENDIENTE = "PENDIENTE"
    COMPLETADO = "COMPLETADO"


class TipoModificador(str, Enum):
    """Tipo de personalización aplicada a un platillo."""

    EXTRA = "EXTRA"
    SIN = "SIN"


@dataclass(frozen=True, order=True)
class Modificador:
    """Representa una personalización sobre un platillo (p. ej. + Queso, + Crema, sin Cebolla)."""

    tipo: TipoModificador
    ingrediente: str

    def __post_init__(self) -> None:
        if not isinstance(self.tipo, TipoModificador):
            object.__setattr__(self, "tipo", TipoModificador(self.tipo))
        ingrediente_limpio = self.ingrediente.strip()
        if not ingrediente_limpio:
            raise ErrorValidacionDominio("El nombre del ingrediente no puede estar vacío.")
        object.__setattr__(self, "ingrediente", ingrediente_limpio)

    def formatear(self) -> str:
        """Devuelve la representación legible del modificador."""
        if self.tipo == TipoModificador.EXTRA:
            return f"+ {self.ingrediente}"
        return f"sin {self.ingrediente}"


def _normalizar_modificadores(modificadores: list[Modificador] | tuple[Modificador, ...]) -> list[Modificador]:
    """Elimina duplicados y ordena primero los EXTRA y luego los SIN por nombre de ingrediente."""
    unicos = set(modificadores)
    return sorted(
        unicos,
        key=lambda m: (0 if m.tipo == TipoModificador.EXTRA else 1, m.ingrediente.lower()),
    )


@dataclass
class Item:
    """Representa una línea de platillos idénticos dentro de un plato."""

    producto: str
    guiso: str
    cantidad: int = 1
    modificadores: list[Modificador] = field(default_factory=list)
    nota: str = ""

    def __post_init__(self) -> None:
        self.producto = self.producto.strip()
        self.guiso = self.guiso.strip()
        self.nota = self.nota.strip()
        if not self.producto:
            raise ErrorValidacionDominio("El producto no puede estar vacío.")
        if not self.guiso:
            raise ErrorValidacionDominio("El guiso base no puede estar vacío.")
        if self.cantidad <= 0:
            raise ErrorValidacionDominio("La cantidad de un platillo debe ser mayor a 0.")
        self.modificadores = _normalizar_modificadores(self.modificadores)

    def clave_identidad(self) -> tuple[str, str, tuple[Modificador, ...], str]:
        """Clave inmutable que identifica si dos items tienen exactamente la misma configuración."""
        return (
            self.producto,
            self.guiso,
            tuple(_normalizar_modificadores(self.modificadores)),
            self.nota.strip().lower(),
        )

    def es_equivalente(self, otro: Item) -> bool:
        """Retorna True si ambos items pueden fusionarse sumando sus cantidades."""
        return self.clave_identidad() == otro.clave_identidad()

    def clonar(
        self,
        *,
        producto: str | None = None,
        guiso: str | None = None,
        cantidad: int | None = None,
        modificadores: list[Modificador] | None = None,
        nota: str | None = None,
    ) -> Item:
        """Crea una copia independiente del item con los cambios opcionales indicados."""
        return Item(
            producto=self.producto if producto is None else producto,
            guiso=self.guiso if guiso is None else guiso,
            cantidad=self.cantidad if cantidad is None else cantidad,
            modificadores=list(self.modificadores) if modificadores is None else list(modificadores),
            nota=self.nota if nota is None else nota,
        )

    def separar_pieza(self) -> Item:
        """
        Descuenta 1 unidad de este item y devuelve un nuevo Item con cantidad=1
        para poder personalizarlo por separado.
        """
        if self.cantidad <= 1:
            raise ErrorValidacionDominio(
                "Solo se puede separar una pieza cuando la cantidad es mayor a 1."
            )
        self.cantidad -= 1
        return self.clonar(cantidad=1)

    @property
    def extras(self) -> list[str]:
        """Nombres de los ingredientes agregados como EXTRA."""
        return [m.ingrediente for m in self.modificadores if m.tipo == TipoModificador.EXTRA]

    @property
    def sin_ingredientes(self) -> list[str]:
        """Nombres de los ingredientes excluidos con SIN."""
        return [m.ingrediente for m in self.modificadores if m.tipo == TipoModificador.SIN]

    def formatear_titulo(self) -> str:
        """Encabezado principal de la línea (ej. '3× Gordita Papas')."""
        return f"{self.cantidad}× {self.producto} {self.guiso}"

    def texto_con_extras(self) -> str:
        """Devuelve la frase natural de extras (ej. 'con Queso y Crema') o cadena vacía."""
        extras = self.extras
        if not extras:
            return ""
        if len(extras) == 1:
            return f"con {extras[0]}"
        return "con " + ", ".join(extras[:-1]) + f" y {extras[-1]}"

    def texto_sin_ingredientes(self) -> str:
        """Devuelve la frase natural de exclusiones (ej. 'sin Cebolla y sin Verdura') o cadena vacía."""
        sins = self.sin_ingredientes
        if not sins:
            return ""
        if len(sins) == 1:
            return f"sin {sins[0]}"
        return "sin " + " y sin ".join(sins)

    def formatear_descripcion_completa(self) -> str:
        """
        Devuelve el nombre completo corrido para cocina:
        ej. 'Gordita Chicharron con Queso' o 'Sope Chicharron sin Queso'.
        """
        partes = [f"{self.producto} {self.guiso}"]
        txt_con = self.texto_con_extras()
        txt_sin = self.texto_sin_ingredientes()
        if txt_con:
            partes.append(txt_con)
        if txt_sin:
            partes.append(txt_sin)
        if self.nota:
            partes.append(f"({self.nota})")
        return " ".join(partes)

    def calcular_precio_unitario(self, precios: dict[str, float] | None = None) -> float:
        """
        Calcula el precio unitario del platillo según las reglas del negocio:
        - Gordita: $17 (o valor configurado en 'GORDITA')
        - Sope de Frijoles: $30 ('SOPE_FRIJOLES')
        - Sope de cualquier otro guiso: $35 ('SOPE_GUISO')
        - Quesadilla: $45 ('QUESADILLA')
        """
        tabla = precios or PRECIOS_POR_DEFECTO
        prod = self.producto.strip().lower()
        guiso = self.guiso.strip().lower()

        if prod == "gordita":
            return float(tabla.get("GORDITA", PRECIOS_POR_DEFECTO["GORDITA"]))
        if prod == "sope":
            if "frijol" in guiso:
                return float(tabla.get("SOPE_FRIJOLES", PRECIOS_POR_DEFECTO["SOPE_FRIJOLES"]))
            return float(tabla.get("SOPE_GUISO", PRECIOS_POR_DEFECTO["SOPE_GUISO"]))
        if prod == "quesadilla":
            return float(tabla.get("QUESADILLA", PRECIOS_POR_DEFECTO["QUESADILLA"]))
        return float(tabla.get(self.producto.upper(), 30.0))

    def calcular_subtotal(self, precios: dict[str, float] | None = None) -> float:
        """Devuelve el precio total de esta línea (`cantidad * precio_unitario`)."""
        return round(self.cantidad * self.calcular_precio_unitario(precios), 2)

    def formatear_detalle(self) -> str:
        """Subtítulo con modificadores y nota (ej. '+ Queso · + Crema · Nota: bien dorada')."""
        partes = [m.formatear() for m in self.modificadores]
        if self.nota:
            partes.append(f"Nota: {self.nota}")
        return " · ".join(partes)

    def formatear_linea(self) -> str:
        """Texto completo de una línea para resúmenes o tarjetas."""
        detalle = self.formatear_detalle()
        if detalle:
            return f"{self.formatear_titulo()} ({detalle})"
        return self.formatear_titulo()


@dataclass(frozen=True)
class ReglasProducto:
    """Define qué guisos base y qué modificadores acepta un producto del catálogo."""

    nombre: str
    guisos_base: tuple[str, ...]
    extras_permitidos: tuple[str, ...]
    sin_permitidos: tuple[str, ...] = ()

    def permite_guiso_base(self, guiso: str) -> bool:
        return guiso in self.guisos_base

    def permite_modificador(self, modificador: Modificador) -> bool:
        if modificador.tipo == TipoModificador.EXTRA:
            return modificador.ingrediente in self.extras_permitidos
        return modificador.ingrediente in self.sin_permitidos


@dataclass
class Catalogo:
    """Contenedor de las reglas del menú para validar items y alimentar la UI."""

    productos: dict[str, ReglasProducto] = field(default_factory=dict)

    @property
    def nombres_productos(self) -> list[str]:
        return list(self.productos.keys())

    def obtener_reglas(self, nombre_producto: str) -> ReglasProducto:
        if nombre_producto not in self.productos:
            raise ErrorValidacionDominio(f"El producto '{nombre_producto}' no existe en el catálogo.")
        return self.productos[nombre_producto]

    def validar_item(self, item: Item) -> None:
        """Verifica que el producto, su guiso base y todos sus modificadores sean válidos."""
        reglas = self.obtener_reglas(item.producto)
        if not reglas.permite_guiso_base(item.guiso):
            raise ErrorValidacionDominio(
                f"El guiso '{item.guiso}' no está permitido como base para '{item.producto}'."
            )
        for mod in item.modificadores:
            if not reglas.permite_modificador(mod):
                raise ErrorValidacionDominio(
                    f"El modificador '{mod.formatear()}' no está permitido para '{item.producto}'."
                )


def catalogo_por_defecto() -> Catalogo:
    """Construye el catálogo estándar idéntico al definido en `db/seed.sql`."""
    guisos = (
        "Chicharron",
        "Papas",
        "Frijoles",
        "Huevo rojo",
        "Huevo verde",
        "Nopales",
        "Aldilla",
        "Rajas",
        "Chorizo",
    )
    return Catalogo(
        productos={
            "Gordita": ReglasProducto(
                nombre="Gordita",
                guisos_base=guisos,
                extras_permitidos=(*guisos, "Queso", "Crema"),
                sin_permitidos=(),
            ),
            "Sope": ReglasProducto(
                nombre="Sope",
                guisos_base=guisos,
                extras_permitidos=(*guisos, "Queso"),
                sin_permitidos=("Cebolla", "Verdura", "Crema", "Queso"),
            ),
            "Quesadilla": ReglasProducto(
                nombre="Quesadilla",
                guisos_base=guisos,
                extras_permitidos=(*guisos, "Queso", "Crema"),
                sin_permitidos=("Cebolla", "Verdura", "Crema", "Queso"),
            ),
        }
    )


@dataclass
class Plato:
    """Agrupa los platillos que van servidos en un mismo plato o empaque."""

    numero: int
    items: list[Item] = field(default_factory=list)

    def agregar_item(self, nuevo_item: Item, catalogo: Catalogo | None = None) -> Item:
        """
        Agrega un item al plato. Si ya existe otro equivalente (mismo producto, guiso,
        modificadores y nota), los fusiona sumando la cantidad.
        """
        if catalogo is not None:
            catalogo.validar_item(nuevo_item)

        for existente in self.items:
            if existente.es_equivalente(nuevo_item):
                existente.cantidad += nuevo_item.cantidad
                return existente

        copia = nuevo_item.clonar()
        self.items.append(copia)
        return copia

    def actualizar_item(
        self,
        indice: int,
        item_editado: Item,
        catalogo: Catalogo | None = None,
    ) -> None:
        """
        Actualiza el item en `indice`. Si tras la edición resulta equivalente a otro item
        del mismo plato, fusiona sus cantidades automáticamente.
        """
        if not (0 <= indice < len(self.items)):
            raise IndexError("Índice de item fuera de rango.")
        if catalogo is not None:
            catalogo.validar_item(item_editado)

        item_limpio = item_editado.clonar()
        for otro_idx, existente in enumerate(self.items):
            if otro_idx != indice and existente.es_equivalente(item_limpio):
                existente.cantidad += item_limpio.cantidad
                self.items.pop(indice)
                return

        self.items[indice] = item_limpio

    def cambiar_cantidad(self, indice: int, delta: int) -> None:
        """Modifica la cantidad del item en `indice`. Si llega a 0 o menos, lo elimina del plato."""
        if not (0 <= indice < len(self.items)):
            raise IndexError("Índice de item fuera de rango.")
        nueva_cantidad = self.items[indice].cantidad + delta
        if nueva_cantidad <= 0:
            self.items.pop(indice)
        else:
            self.items[indice].cantidad = nueva_cantidad

    def separar_pieza_de_item(self, indice: int) -> int:
        """
        Separa 1 pieza del item en `indice`, la inserta inmediatamente debajo
        y retorna el índice de la nueva pieza.
        """
        if not (0 <= indice < len(self.items)):
            raise IndexError("Índice de item fuera de rango.")
        pieza_separada = self.items[indice].separar_pieza()
        nuevo_indice = indice + 1
        self.items.insert(nuevo_indice, pieza_separada)
        return nuevo_indice

    @property
    def total_piezas(self) -> int:
        """Suma total de platillos dentro de este plato."""
        return sum(item.cantidad for item in self.items)

    @property
    def esta_vacio(self) -> bool:
        return len(self.items) == 0

    def calcular_subtotal(self, precios: dict[str, float] | None = None) -> float:
        """Suma el importe en pesos de todos los items de este plato."""
        return round(sum(item.calcular_subtotal(precios) for item in self.items), 2)


@dataclass
class Pedido:
    """Entidad raíz que representa un pedido completo con uno o más platos."""

    id: int | None = None
    numero_orden_dia: int = 0
    nombre_cliente: str = ""
    tipo_servicio: TipoServicio | None = None
    estado: EstadoPedido = EstadoPedido.PENDIENTE
    version: int = 1
    solo_en_cocina: bool = False
    total_cobrado: float = 0.0
    pago_cliente: float = 0.0
    cambio_entregado: float = 0.0
    platos: list[Plato] = field(default_factory=lambda: [Plato(numero=1)])
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        self.nombre_cliente = (self.nombre_cliente or "").strip()
        if self.tipo_servicio is not None and not isinstance(self.tipo_servicio, TipoServicio):
            self.tipo_servicio = TipoServicio(self.tipo_servicio)
        if not isinstance(self.estado, EstadoPedido):
            self.estado = EstadoPedido(self.estado)
        if not self.platos:
            self.platos = [Plato(numero=1)]

    @property
    def numero_pedido_mostrar(self) -> int:
        """Número de llegada del pedido en el día (Pedido 1, Pedido 2, ...)."""
        return self.numero_orden_dia if self.numero_orden_dia > 0 else (self.id or 1)

    @property
    def nombre_mostrar(self) -> str:
        """Devuelve el nombre del cliente o un texto por defecto si es un pedido antiguo sin nombre."""
        return self.nombre_cliente.strip() if self.nombre_cliente.strip() else "Cliente"

    def obtener_plato(self, numero: int) -> Plato:
        """Devuelve el plato con el número indicado."""
        for plato in self.platos:
            if plato.numero == numero:
                return plato
        raise ErrorValidacionDominio(f"No existe el Plato {numero} en el pedido.")

    def agregar_plato(self) -> Plato:
        """Crea un nuevo plato al final y lo devuelve."""
        siguiente_numero = len(self.platos) + 1
        nuevo = Plato(numero=siguiente_numero)
        self.platos.append(nuevo)
        return nuevo

    def eliminar_plato(self, numero: int) -> None:
        """
        Elimina el plato indicado y renumera los restantes (1..N).
        Si era el único plato, lo reinicia vacío como Plato 1.
        """
        self.platos = [p for p in self.platos if p.numero != numero]
        if not self.platos:
            self.platos = [Plato(numero=1)]
        else:
            self._renumerar_platos()

    def limpiar_platos_vacios(self) -> None:
        """Descarta los platos sin items y renumera consecutivamente 1..N."""
        platos_con_items = [p for p in self.platos if not p.esta_vacio]
        if platos_con_items:
            self.platos = platos_con_items
            self._renumerar_platos()
        else:
            self.platos = [Plato(numero=1)]

    def _renumerar_platos(self) -> None:
        for idx, plato in enumerate(self.platos, start=1):
            plato.numero = idx

    @property
    def total_platillos(self) -> int:
        """Cantidad total de piezas sumando todos los platos."""
        return sum(plato.total_piezas for plato in self.platos)

    def calcular_total(self, precios: dict[str, float] | None = None) -> float:
        """Calcula el total en pesos de todo el pedido."""
        return round(sum(plato.calcular_subtotal(precios) for plato in self.platos), 2)

    @property
    def total_platos_con_items(self) -> int:
        """Número de platos que contienen al menos un platillo."""
        return sum(1 for plato in self.platos if not plato.esta_vacio)

    @property
    def total_lineas_items(self) -> int:
        """Cantidad total de renglones de platillos sumando todos los platos activos."""
        return sum(len(plato.items) for plato in self.platos if not plato.esta_vacio)

    @property
    def es_grande_por_tamano(self) -> bool:
        """
        Determina automáticamente si el pedido es grande para la pantalla de tablet:
        - Tiene 3 o más platos, o
        - Tiene 2 platos con más de 4 renglones en total, o
        - Tiene 5 o más renglones distintos de platillos.
        """
        num_platos = self.total_platos_con_items
        num_lineas = self.total_lineas_items
        if num_platos >= 3:
            return True
        if num_platos == 2 and num_lineas > 4:
            return True
        if num_lineas >= 5:
            return True
        return False

    @property
    def requiere_pantalla_completa(self) -> bool:
        """
        Indica si este pedido debe mostrarse solo (1 en pantalla completa) en Cocina,
        ya sea por su tamaño (3-4+ platos) o porque el mesero activó `solo_en_cocina`.
        """
        return bool(self.solo_en_cocina) or self.es_grande_por_tamano

    def validar_para_envio(self, catalogo: Catalogo | None = None) -> None:
        """
        Verifica todas las reglas necesarias antes de guardar o enviar a cocina:
        1. Que el mesero haya elegido Mesa o Para llevar.
        2. Que exista al menos un platillo en el pedido.
        3. Que todos los platillos cumplan las reglas del catálogo (si se provee).
        """
        if self.tipo_servicio is None:
            raise ErrorValidacionDominio(
                "Debes elegir si el pedido es para Mesa o Para llevar antes de enviarlo."
            )
        if self.total_platillos <= 0:
            raise ErrorValidacionDominio("El pedido debe contener al menos un platillo.")

        if catalogo is not None:
            for plato in self.platos:
                for item in plato.items:
                    catalogo.validar_item(item)

    def preparar_para_guardar(self, catalogo: Catalogo | None = None) -> None:
        """Valida el pedido y limpia los platos vacíos dejándolo listo para persistir."""
        self.validar_para_envio(catalogo)
        self.limpiar_platos_vacios()


def formatear_pedido(pedido: Pedido) -> str:
    """Genera una representación en texto estructurada por platos para resúmenes y confirmaciones."""
    if pedido.nombre_cliente:
        encabezado_id = f"Cliente: {pedido.nombre_cliente}"
    elif pedido.id is not None:
        encabezado_id = f"Pedido #{pedido.id}"
    else:
        encabezado_id = "Pedido nuevo"
    servicio = pedido.tipo_servicio.etiqueta if pedido.tipo_servicio else "Sin tipo de servicio"
    lineas = [f"{encabezado_id} · {servicio}"]

    platos_no_vacios = [p for p in pedido.platos if not p.esta_vacio]
    for plato in platos_no_vacios:
        lineas.append(f"── Plato {plato.numero} ──")
        for item in plato.items:
            lineas.append(f"  {item.formatear_linea()}")

    return "\n".join(lineas)


def seleccionar_pedidos_visibles_cocina(pendientes: list[Pedido]) -> list[Pedido]:
    """
    Calcula qué pedidos deben mostrarse simultáneamente en la tablet de Cocina
    para que NUNCA sea necesario hacer scroll:
    - Si el primer pedido es grande (3-4 platos o marcado como 'solo en pantalla'),
      se muestra únicamente ese pedido ocupando toda la pantalla.
    - Si el primer pedido es chico (1-2 platos compactos) y el segundo también es chico,
      se muestran los 2 pedidos a la par (mitad y mitad).
    """
    if not pendientes:
        return []

    primero = pendientes[0]
    if primero.requiere_pantalla_completa:
        return [primero]

    if len(pendientes) >= 2 and not pendientes[1].requiere_pantalla_completa:
        return [primero, pendientes[1]]

    return [primero]
