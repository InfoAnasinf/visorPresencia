# Visor de Presencia

Aplicación de escritorio en PyQt6 para visualizar fichajes de personal conectándose a SQL Server.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Herramientas

- PyQt6 para la interfaz.
- SQLAlchemy + pyodbc para la conexión a SQL Server.
- QSettings con cifrado simétrico (`cryptography`) para credenciales.
- Pytest (unitario, Qt, integración), Ruff y Black.

## Estructura

Consulta `app/` para la capa de presentación (MVVM ligero), dominio y datos.
