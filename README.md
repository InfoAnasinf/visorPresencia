# Visor de Presencia

Aplicacion de escritorio en PyQt6 para visualizar fichajes de personal conectandose a SQL Server.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Herramientas

- PyQt6 para la interfaz.
- SQLAlchemy + pyodbc para la conexion a SQL Server.
- QSettings con cifrado simetrico (`cryptography`) para credenciales.
- Pytest (unitario, Qt, integracion), Ruff y Black.

- La vista principal agrupa los fichajes por dia, muestra el total diario y permite desplegar los pares de fichajes; los dias con incidencias pendientes se resaltan automaticamente.

## Configuracion de base de datos

La primera ejecucion guarda en `QSettings` (cifrados con Fernet) las credenciales por defecto:

- Servidor: `188.213.7.76`
- Base de datos: `Fichajes`
- Usuario: `sa`
- Contrasena: se guarda cifrada (`V!c4W-85bX`)

Puedes cambiarlas con el asistente (`app/core/database.py`) o sobreescribiendo los valores con QSettings (Windows registry) antes de arrancar.

## Estructura

Consulta `app/` para la capa de presentacion (MVVM ligero), dominio y datos.
