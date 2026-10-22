# Proyecto Gorditas y Sopes - Sistema de Pedidos y Monitor de Cocina

Aplicación de toma de pedidos por platos y monitor de cocina en tiempo real desarrollada con **Python**, **Flet** y **MySQL**.

## Características Principales

- **Toma de pedidos rápida para meseros**:
  - Selección obligatoria de modalidad: **Comer aquí (Mesa)** o **Para llevar**.
  - **División por platos** (`Plato 1`, `Plato 2`, `+ Plato`).
  - Cuadrícula de guisos de **un solo toque** con fusión automática de cantidades.
- **Personalización completa por platillo**:
  - Cambiar guiso base, agregar múltiples extras (**Con Queso**, **Con Crema**, otros guisos), quitar ingredientes en sopes (**Sin Cebolla**, **Sin Verdura**, etc.) y nota especial.
  - Función **"Separar 1 pieza"** para personalizar individualmente una unidad de un grupo.
- **Monitor de cocina en tiempo real**:
  - Tarjetas agrupadas por platos con insignia de **MESA** o **PARA LLEVAR**.
  - Pestañas de **Pendientes** y **Completados del día**.
  - Detección automática de ediciones con etiqueta **MODIFICADO** y control de concurrencia por versión.
- **Edición en cualquier momento**:
  - Permite editar pedidos tanto pendientes como ya completados, con protección contra ediciones simultáneas y aviso al salir con cambios sin guardar.

## Estructura del Proyecto

- `src/main.py`: Punto de entrada y enrutador (`/home`, `/Pedidos`, `/pedido/{id}`).
- `src/config.py`: Carga de variables de entorno (`.env`) y constantes globales.
- `src/domain/modelos.py`: Entidades del dominio (`Pedido`, `Plato`, `Item`, `Modificador`, `Catalogo`).
- `src/data/`: Conexión a MySQL (`db.py`) y repositorio transaccional (`repositorio.py`).
- `src/ui/`: Tema visual (`theme.py`), tarjetas y navegación (`components.py`) y modal de personalización (`personalizacion.py`).
- `src/views/`: Monitor de cocina (`home.py`) y pantalla de toma/edición de pedidos (`pedido.py`).
- `db/schema.sql` y `db/seed.sql`: Esquema relacional y catálogo inicial.
- `tests/test_modelos.py`: Pruebas unitarias del dominio con `pytest`.

## Instalación y Configuración

1. Instala las dependencias:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Configura tus credenciales de MySQL en `.env` (puedes copiar `.env.example`).
3. Importa en MySQL (p. ej. desde phpMyAdmin) primero `db/schema.sql` y luego `db/seed.sql`.

## Ejecución y Pruebas

- **Iniciar la aplicación:**
  ```bash
  python src/main.py
  ```
- **Ejecutar pruebas unitarias:**
  ```bash
  python -m pytest -v
  ```
- **Ejecutar prueba de integración con MySQL:**
  ```bash
  python scripts/probar_repositorio.py
  ```
