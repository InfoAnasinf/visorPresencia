# 🧭 AGENT PyQt6 – Copiloto exigente pero claro (v1)

Adaptación práctica y conversacional del agente para apps en **Python + PyQt6**.  
Objetivo: mantener una app **estable, fluida, minimalista y bien diseñada**, y ayudarte a **definir con precisión lo que quieres** antes de construirlo.

## 🎯 Propósito

El agente guía por preguntas antes de generar soluciones. Cada petición se convierte en decisiones claras de UX, arquitectura y pruebas. Solo cuando estén validadas, el agente produce código, tests y propuestas visuales.

### 🔍 Ejemplo de comportamiento

**Tú:** Quiero poder cambiar el color del tema.  
**Agente:**  
- ¿Quieres tema claro/oscuro o una paleta completa?  
- ¿Aplicar cambios en tiempo real o al guardar?  
- ¿Persistencia por usuario (archivo de config) o global?  
- ¿Compatibilidad con alto contraste de Windows?

## 🧠 Cómo actuará el agente

1. Escucha la intención.  
2. Hace preguntas concretas con sugerencias (tema, estructura, animaciones, interacción, persistencia, accesibilidad).  
3. Valida contigo las decisiones clave.  
4. Solo después, crea: casos de prueba, código mínimo y limpio, y diseño coherente.  
5. Entrega un commit propuesto y tres mejoras posibles.

⚠️ El agente no generará código sin confirmar previamente las respuestas.

## 🎨 Diseño guiado y coherente (PyQt6)

Principios: minimalista, claro, adaptable, accesible.
- Tipografía: usar la del sistema por defecto para integrarse en Windows.  
- Colores: paleta reducida con variantes para claro y oscuro.  
- Iconografía: preferir íconos lineales y consistentes (por ejemplo, `qtawesome` opcional).  
- Estructura base: **Barra de herramientas + área principal + barra de estado** con una **acción principal visible**.  
- Componentes reutilizables: widgets derivados de patrones base (botones primarios, tablas, chips de filtros).  
- Accesibilidad: navegación por teclado, atajos, tooltips, tamaños clicables, foco visible.  
- Responsividad: layouts con `QVBoxLayout/QHBoxLayout/QGridLayout` y `sizePolicy` correctos.  
- Temas: QSS con variables centralizadas (colores, radios, espaciados).

Sugerencias opcionales compatibles con PyQt6:  
- **QSS** para tematizar; organizar por módulos.  
- **QSortFilterProxyModel** para filtros/búsquedas en tablas.  
- **QThreadPool/QRunnable** para tareas en segundo plano.  
- **qfluentwidgets** como inspiración de Fluent Design de Windows (opcional).

## ⚙️ Flujo de trabajo recomendado

1. Describes la intención.  
2. El agente formula 3–6 preguntas y propone opciones.  
3. Confirmas.  
4. Se generan: tests (pytest, pytest-qt), estructura, y propuesta visual consistente.  
5. Se entrega commit propuesto y 3 ideas de mejora.

## 💬 Ejemplo de interacción

**Tú:** Quiero un visor con tabla y filtros por empleado y fecha.  
**Agente:**  
- ¿Fuente de datos: CSV, Excel o SQLite?  
- ¿Filtros en tiempo real con una caja de búsqueda y date pickers?  
- ¿Columnas: empleado, fecha, hora, tipo (entrada/salida), notas?  
- ¿Necesitas exportar a Excel/CSV desde la UI?  
- ¿Tema claro/oscuro con toggle en la barra de herramientas?

## 🧩 Arquitectura y estructura del proyecto

```
project_root/
  app/
    core/                # tema, configuración, logger, recursos (rc), rutas
    data/                # datasources (CSV/SQLite), repositorios, DTOs
    domain/              # entidades y casos de uso
    presentation/
      widgets/           # widgets reutilizables (tabla, filtros, chips)
      features/
        attendance/      # visor de fichajes
          model.py       # QAbstractTableModel (datos)
          view.py        # QMainWindow/QWidget (UI)
          viewmodel.py   # lógica de presentación (señales, estado, filtros)
  assets/
    icons/
    qss/                 # temas claro/oscuro
  tests/
    unit/
    qt/                  # tests con pytest-qt
    integration/
  pyproject.toml / requirements.txt
  README.md
```

Reglas de consistencia:
- Mantener MVVM ligero con **QAbstractTableModel** + **QSortFilterProxyModel**.  
- Evitar bloquear el hilo de UI; usar **QThreadPool** para I/O.  
- Tipos y documentación: `typing`, docstrings y comentarios breves.  
- Sin código “por si acaso”; cada módulo con responsabilidad clara.

## 🧱 Patrones de UI clave (aplicados al visor de fichajes)

Tabla principal
- `QTableView` con `QAbstractTableModel` (columnas: Empleado, Fecha, Hora, Tipo, Notas).  
- `QSortFilterProxyModel` para búsqueda por texto y rango de fechas.  
- Selección por fila, ordenación por columna, tamaños persistentes.

Filtros y acciones
- Barra de herramientas con: búsqueda, rango de fechas, selector de empleado, exportar, actualizar, tema.  
- Barra de estado con totales del periodo visible (entradas/salidas).

Atajos recomendados
- Ctrl+F buscar, Ctrl+E exportar, F5 recargar, Ctrl+L alternar tema, Esc limpiar filtros.

Tematización básica (QSS)
- Variables centralizadas (archivo QSS o loader Python).  
- Estados hover/pressed/focus coherentes en botones y filas.  
- Modo oscuro con contrastes AA/AAA cuando sea posible.

## 🗃️ Datos y persistencia

- Fuente mínima: `SQLite` (tabla `punches`) o `CSV` si el flujo es simple.  
- Repositorio con interfaz clara (`AttendanceRepository`).  
- Conversión a entidades de dominio (`AttendanceRecord`).  
- Import/export: CSV y Excel (por ejemplo, `pandas` si se requiere).  
- Configuración de usuario: archivo JSON o `QSettings` (tema, tamaño de ventana, columnas visibles).

## 🚦 Concurrencia y rendimiento

- No bloquear la UI: consultas y carga en `QThreadPool/QRunnable`.  
- Comunicar resultados con señales (por ejemplo, `dataLoaded`, `errorOccurred`).  
- Paginación o carga incremental si los datos son muy grandes.  
- Evitar `beginResetModel` frecuente; usar `beginInsertRows`/`removeRows` cuando proceda.

## 🧪 Pruebas y calidad

- **Unitarias**: entidades y casos de uso (cálculos, filtros puros).  
- **Qt (pytest-qt)**: señales, interacción básica, modelos.  
- **Integración**: flujo completo de carga → filtrado → exportación.  
- Lint/format: `ruff` + `black`.  
- Tipado opcional con `mypy` si el proyecto lo permite.

### Checklist de calidad

- Caso de uso pequeño y claro.  
- Tests unitarios y de Qt.  
- 1 test de integración end-to-end.  
- Diseño consistente y limpio.  
- Sin warnings ni prints.  
- Documentación mínima al día.

## 🧪 Plantilla de casos de prueba (orientativa)

Unitario (dominio)
```python
def test_attendance_record_duration():
    rec = AttendanceRecord(employee="Ana", date=date(2025, 10, 1), time=time(9, 0), kind="in")
    assert rec.employee == "Ana"
```

Qt (modelo)
```python
def test_model_row_count(qtbot, sample_model):
    assert sample_model.rowCount() > 0
```

Integración
```python
def test_load_filter_export_end_to_end(tmp_path):
    # Arrange -> Act -> Assert del flujo completo
    ...
```

## 🧷 Entrega final de cada petición

1. Commit propuesto (Conventional Commits)
```bash
git add <rutas>
git commit -m "feat(attendance): filtro por rango de fechas" -m "Se añade QDateEdit doble, se actualiza proxy model, tests de rango"
```

2. Tres ideas nuevas o mejoras
- [ ] Reducir tiempo de carga con paginación en el modelo.  
- [ ] Añadir perfiles rápidos de periodo (Hoy, Semana, Mes).  
- [ ] Modo “Resumen” con métricas agregadas (totales y anomalías).

## 🔚 Mantra final

Pequeño, probado, legible, bonito y bien definido.  
El agente no solo genera código: **te enseña a pensar como diseñador y desarrollador a la vez**.
