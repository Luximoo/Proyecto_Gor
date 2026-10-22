"""Script de prueba de integración para la Fase 3 (`src/data/repositorio.py`)."""

from pathlib import Path
import sys

# Agregar src/ al path para poder ejecutar `python scripts/probar_repositorio.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from data.repositorio import (
    ErrorConcurrenciaPedido,
    actualizar_pedido,
    cargar_catalogo,
    cargar_pedido,
    guardar_pedido,
    marcar_pedido_completado,
    obtener_pedidos_completados_hoy,
    obtener_pedidos_pendientes,
)
from domain.modelos import (
    EstadoPedido,
    Item,
    Modificador,
    Pedido,
    TipoModificador,
    TipoServicio,
    formatear_pedido,
)


def main() -> None:
    print("=== 1. Cargando catálogo desde MySQL ===")
    catalogo = cargar_catalogo()
    print("Productos cargados:", catalogo.nombres_productos)
    assert "Gordita" in catalogo.productos
    assert "Sope" in catalogo.productos
    assert "Crema" in catalogo.obtener_reglas("Gordita").extras_permitidos

    print("\n=== 2. Creando y guardando un pedido con 2 platos ===")
    pedido = Pedido(tipo_servicio=TipoServicio.MESA)

    # Plato 1: 4 gorditas de chicharrón
    pedido.platos[0].agregar_item(
        Item(producto="Gordita", guiso="Chicharron", cantidad=4),
        catalogo,
    )

    # Plato 2: 1 sope sin cebolla + 1 gordita de papas con queso y crema
    plato_2 = pedido.agregar_plato()
    plato_2.agregar_item(
        Item(
            producto="Sope",
            guiso="Chorizo",
            cantidad=1,
            modificadores=[Modificador(TipoModificador.SIN, "Cebolla")],
        ),
        catalogo,
    )
    plato_2.agregar_item(
        Item(
            producto="Gordita",
            guiso="Papas",
            cantidad=1,
            modificadores=[
                Modificador(TipoModificador.EXTRA, "Queso"),
                Modificador(TipoModificador.EXTRA, "Crema"),
            ],
            nota="Bien dorada",
        ),
        catalogo,
    )

    guardado = guardar_pedido(pedido, catalogo)
    assert guardado.id is not None
    assert guardado.version == 1
    assert guardado.estado == EstadoPedido.PENDIENTE
    assert guardado.total_platillos == 6
    print(f"Pedido guardado con ID #{guardado.id} (versión {guardado.version}):")
    print(formatear_pedido(guardado))

    print("\n=== 3. Verificando lectura desde MySQL (`cargar_pedido`) ===")
    recargado = cargar_pedido(guardado.id)
    assert recargado.id == guardado.id
    assert recargado.tipo_servicio == TipoServicio.MESA
    assert len(recargado.platos) == 2
    assert recargado.platos[0].items[0].cantidad == 4
    assert recargado.platos[1].items[1].extras == ["Crema", "Queso"]
    assert recargado.platos[1].items[1].nota == "Bien dorada"
    print("OK -> El pedido recargado desde MySQL coincide exactamente con el original.")

    print("\n=== 4. Probando edición y aumento de versión (`actualizar_pedido`) ===")
    recargado.tipo_servicio = TipoServicio.LLEVAR
    recargado.platos[0].cambiar_cantidad(0, -1)  # De 4 gorditas pasa a 3
    editado = actualizar_pedido(recargado, version_esperada=1, catalogo=catalogo)
    assert editado.version == 2
    assert editado.tipo_servicio == TipoServicio.LLEVAR
    assert editado.total_platillos == 5
    print(f"OK -> Pedido #{editado.id} actualizado a versión {editado.version} (Para llevar, 5 piezas).")

    print("\n=== 5. Probando bloqueo optimista (conflicto de edición concurrente) ===")
    try:
        actualizar_pedido(editado, version_esperada=1, catalogo=catalogo)
        raise AssertionError("Debió lanzar ErrorConcurrenciaPedido")
    except ErrorConcurrenciaPedido as err:
        print(f"OK -> Conflicto detectado correctamente: {err}")

    print("\n=== 6. Probando marcar como COMPLETADO y reabrir al editar ===")
    completado_ok = marcar_pedido_completado(editado.id)
    assert completado_ok is True

    completados_hoy = obtener_pedidos_completados_hoy()
    assert any(p.id == editado.id for p in completados_hoy)
    print(f"OK -> Pedido #{editado.id} aparece en la lista de completados de hoy.")

    # Si editamos un pedido completado, debe regresar a PENDIENTE con versión 3
    pedido_completado = cargar_pedido(editado.id)
    assert pedido_completado.estado == EstadoPedido.COMPLETADO
    pedido_completado.platos[0].agregar_item(
        Item(producto="Gordita", guiso="Rajas", cantidad=1),
        catalogo,
    )
    reabierto = actualizar_pedido(pedido_completado, catalogo=catalogo)
    assert reabierto.estado == EstadoPedido.PENDIENTE
    assert reabierto.version == 3
    pendientes = obtener_pedidos_pendientes()
    assert any(p.id == reabierto.id for p in pendientes)
    print(
        f"OK -> Al editar el pedido completado #{reabierto.id}, regresó a PENDIENTE con versión {reabierto.version}."
    )

    print("\n============================================================")
    print(f"TODAS LAS PRUEBAS DEL REPOSITORIO PASARON EXITOSAMENTE.")
    print(f"Puedes revisar el Pedido #{reabierto.id} en phpMyAdmin.")
    print("============================================================")


if __name__ == "__main__":
    main()
