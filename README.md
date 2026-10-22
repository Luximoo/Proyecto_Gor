# Proyecto Gorditas - Sistema de Pedidos y Monitor de Cocina

Aplicación de punto de venta y monitor de pedidos en tiempo real desarrollada con **Python**, **Flet** y **MySQL**.

## Estructura del Proyecto

- `src/main.py`: Punto de entrada de la aplicación y enrutador.
- `src/views/`: Vistas de la aplicación (Toma de pedidos y Monitor de cocina).
- `src/Utilidades/`: Componentes gráficos y temas de interfaz.
- `db/schema.sql`: Script de creación de la base de datos y tabla `pedidos`.

## Requisitos Previos

- Python 3.10 o superior (recomendado 3.11 o 3.13).
- MySQL Server (XAMPP, WampServer o MySQL instalado localmente).

## Instalación

1. Clona el repositorio o abre la carpeta del proyecto.
2. (Opcional) Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura las variables de entorno:
   - Copia `.env.example` como `.env`:
     ```bash
     copy .env.example .env
     ```
   - Modifica `.env` con las credenciales de tu servidor MySQL.
5. Importa la base de datos en MySQL con el archivo `db/schema.sql`.

## Ejecución

Para iniciar la aplicación:

```bash
flet run src/main.py
```
O directamente con Python:
```bash
python src/main.py
```
