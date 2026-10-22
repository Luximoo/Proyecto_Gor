"""Pruebas unitarias para el modelo de dominio (`domain.modelos`)."""

import pytest

from domain.modelos import (
    ErrorValidacionDominio,
    EstadoPedido,
    Item,
    Modificador,
    Pedido,
    Plato,
    TipoModificador,
    TipoServicio,
    catalogo_por_defecto,
    formatear_pedido,
)


def test_fusion_items_identicos_en_plato() -> None:
    """Tocar el mismo guiso varias veces debe sumar la cantidad en una sola línea."""
    plato = Plato(numero=1)
    plato.agregar_item(Item(producto="Gordita", guiso="Papas", cantidad=1))
    plato.agregar_item(Item(producto="Gordita", guiso="Papas", cantidad=2))

    assert len(plato.items) == 1
    assert plato.items[0].cantidad == 3
    assert plato.total_piezas == 3


def test_no_fusiona_items_con_distintos_modificadores_o_nota() -> None:
    """Items con distintos extras o notas deben mantenerse como líneas separadas."""
    plato = Plato(numero=1)
    mod_queso = Modificador(TipoModificador.EXTRA, "Queso")

    plato.agregar_item(Item(producto="Gordita", guiso="Papas", cantidad=1))
    plato.agregar_item(
        Item(producto="Gordita", guiso="Papas", cantidad=1, modificadores=[mod_queso])
    )
    plato.agregar_item(
        Item(producto="Gordita", guiso="Papas", cantidad=1, nota="Bien dorada")
    )

    assert len(plato.items) == 3
    assert plato.total_piezas == 3


def test_separar_una_pieza_y_personalizarla() -> None:
    """Permite separar 1 pieza de un grupo de 3 para agregarle crema solo a esa."""
    catalogo = catalogo_por_defecto()
    plato = Plato(numero=1)
    plato.agregar_item(Item(producto="Gordita", guiso="Chicharron", cantidad=3), catalogo)

    nuevo_idx = plato.separar_pieza_de_item(0)

    assert nuevo_idx == 1
    assert len(plato.items) == 2
    assert plato.items[0].cantidad == 2
    assert plato.items[1].cantidad == 1

    # Personalizar la pieza separada con Crema
    pieza_con_crema = plato.items[nuevo_idx].clonar(
        modificadores=[Modificador(TipoModificador.EXTRA, "Crema")]
    )
    plato.actualizar_item(nuevo_idx, pieza_con_crema, catalogo)

    assert plato.items[1].extras == ["Crema"]
    assert plato.total_piezas == 3


def test_actualizar_item_fusiona_si_queda_igual_a_otro() -> None:
    """Si al editar un item queda idéntico a otro del mismo plato, se fusionan."""
    plato = Plato(numero=1)
    mod_crema = Modificador(TipoModificador.EXTRA, "Crema")

    plato.agregar_item(Item(producto="Gordita", guiso="Papas", cantidad=2))
    plato.agregar_item(
        Item(producto="Gordita", guiso="Papas", cantidad=1, modificadores=[mod_crema])
    )
    assert len(plato.items) == 2

    # Si le quitamos la crema al segundo item, debe fusionarse con el primero (2 + 1 = 3)
    sin_modificadores = plato.items[1].clonar(modificadores=[])
    plato.actualizar_item(1, sin_modificadores)

    assert len(plato.items) == 1
    assert plato.items[0].cantidad == 3


def test_reglas_catalogo_gordita_y_sope() -> None:
    """Verifica que Gordita permita Crema/Queso extra pero no 'SIN', y Sope permita 'SIN'."""
    catalogo = catalogo_por_defecto()

    # Gordita con Queso, Crema y otro guiso (Rajas) -> Válido
    gordita_valida = Item(
        producto="Gordita",
        guiso="Papas",
        modificadores=[
            Modificador(TipoModificador.EXTRA, "Queso"),
            Modificador(TipoModificador.EXTRA, "Crema"),
            Modificador(TipoModificador.EXTRA, "Rajas"),
        ],
    )
    catalogo.validar_item(gordita_valida)

    # Gordita 'sin Cebolla' -> Inválido según las reglas del negocio
    gordita_invalida = Item(
        producto="Gordita",
        guiso="Papas",
        modificadores=[Modificador(TipoModificador.SIN, "Cebolla")],
    )
    with pytest.raises(ErrorValidacionDominio):
        catalogo.validar_item(gordita_invalida)

    # Sope 'sin Cebolla' y 'con Chicharron' -> Válido
    sope_valido = Item(
        producto="Sope",
        guiso="Nopales",
        modificadores=[
            Modificador(TipoModificador.SIN, "Cebolla"),
            Modificador(TipoModificador.EXTRA, "Chicharron"),
        ],
    )
    catalogo.validar_item(sope_valido)


def test_validacion_pedido_exige_mesa_o_llevar_y_al_menos_un_item() -> None:
    """Un pedido no puede enviarse sin elegir Mesa/Llevar ni estando vacío."""
    catalogo = catalogo_por_defecto()
    pedido = Pedido()

    # 1. Sin tipo_servicio -> falla
    pedido.platos[0].agregar_item(Item(producto="Gordita", guiso="Rajas", cantidad=2))
    with pytest.raises(ErrorValidacionDominio, match="Mesa o Para llevar"):
        pedido.validar_para_envio(catalogo)

    # 2. Con tipo_servicio pero sin platillos -> falla
    pedido_vacio = Pedido(tipo_servicio=TipoServicio.MESA)
    with pytest.raises(ErrorValidacionDominio, match="al menos un platillo"):
        pedido_vacio.validar_para_envio(catalogo)


def test_division_por_platos_y_limpieza_de_platos_vacios() -> None:
    """Permite armar múltiples platos y descarta platos vacíos renumerando al guardar."""
    catalogo = catalogo_por_defecto()
    pedido = Pedido(id=42, tipo_servicio=TipoServicio.LLEVAR)

    # Plato 1: 4 gorditas
    pedido.platos[0].agregar_item(Item(producto="Gordita", guiso="Chicharron", cantidad=4))

    # Plato 2: se deja vacío por accidente
    pedido.agregar_plato()

    # Plato 3: 1 sope + 1 gordita
    plato_3 = pedido.agregar_plato()
    plato_3.agregar_item(
        Item(
            producto="Sope",
            guiso="Chorizo",
            cantidad=1,
            modificadores=[Modificador(TipoModificador.SIN, "Cebolla")],
        )
    )
    plato_3.agregar_item(
        Item(
            producto="Gordita",
            guiso="Papas",
            cantidad=1,
            modificadores=[
                Modificador(TipoModificador.EXTRA, "Queso"),
                Modificador(TipoModificador.EXTRA, "Crema"),
            ],
        )
    )

    pedido.preparar_para_guardar(catalogo)

    assert len(pedido.platos) == 2
    assert [p.numero for p in pedido.platos] == [1, 2]
    assert pedido.total_platillos == 6
    assert pedido.estado == EstadoPedido.PENDIENTE

    resumen = formatear_pedido(pedido)
    assert "Pedido #42 · Para llevar" in resumen
    assert "── Plato 1 ──" in resumen
    assert "4× Gordita Chicharron" in resumen
    assert "── Plato 2 ──" in resumen
    assert "1× Sope Chorizo (sin Cebolla)" in resumen
    assert "1× Gordita Papas (+ Crema · + Queso)" in resumen
