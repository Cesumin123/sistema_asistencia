# AGENTS.md — Sistema de Gestión de Asistencia Estudiantil (Complejo Educativo "Colinas del Llano")

Este documento define la fuente de verdad exacta del repositorio: arquitectura, esquema de base de datos, reglas de negocio, estándares UI/UX multiplataforma, presupuesto de dependencias y criterios de terminado (*Definition of Done*) obligatorios para todos los agentes y subagentes.

---

## 1. Contexto del Proyecto
* **Nombre:** Sistema de Información para la Gestión de Asistencia Estudiantil — Coordinación de 4to Año del Complejo Educativo "Colinas del Llano" (Barinas, Venezuela).
* **Tipo de aplicación:** Aplicación de escritorio **offline-first**, monousuario, ligera y portable (empaquetable en `.exe` con PyInstaller).
* **Normativa legal clave:** Artículo 109 del Reglamento General de la Ley Orgánica de Educación (RGLOE) — exige un mínimo del **75% de asistencia efectiva** para la aprobación escolar.
* **Metodología:** Feature Driven Development (FDD) + Pruebas Unitarias y de Cableado obligatorias por cada módulo.

---

## 2. Stack Tecnológico y Presupuesto de Dependencias (RNF-02)
* **Lenguaje:** Python 3.10+.
* **Interfaz Gráfica (GUI):** `tkinter` y `ttk` (biblioteca estándar), `tkcalendar` (`DateEntry`), `Pillow` (`PIL` para escudo institucional y fotografías optimizadas).
* **Base de Datos:** `sqlite3` (embebida, archivo local `sistema_escolar.db`).
* **Respaldo de contingencia:** `json` (biblioteca estándar, archivo `memoria_emergencia.json`).
* **Reportes PDF:** `reportlab` (`reportlab.platypus`).
* **Pruebas Unitarias:** `pytest` (entorno virtual `.venv/bin/pytest`).
* **Restricción de Presupuesto (RNF-02):** **PROHIBIDO** instalar librerías pesadas (`matplotlib`, `pandas`, `numpy`, frameworks web, ORMs pesados ni dependencias con conexión a Internet) para mantener el binario `< 50 MB` y operando fluidamente en equipos con `2 GB` de RAM. Cualquier gráfico o visualización estadística debe construirse con `tk.Canvas` puro.

---

## 3. Arquitectura Real del Repositorio (Patrón Hexagonal / Puertos y Adaptadores)
Respetar estrictamente la separación de responsabilidades y los principios **SOLID**, verificados automáticamente por `tests/test_arquitectura_hexagonal.py`:

1. **Núcleo de Dominio (`dominio/`):**
   * Python puro. **PROHIBIDO** importar `sqlite3`, `tkinter`, `tkcalendar`, `reportlab`, `adaptadores` o `db_conexion`.
   * Módulos actuales: `asistencia.py`, `clase.py`, `estudiante.py`, `permisos.py`, `profesor.py`, `promocion.py`, `reportes.py`, `usuario.py`.
   * Contiene entidades, validaciones de negocio, cálculo del porcentaje de asistencia (Art. 109 RGLOE), hashing de contraseñas (`hashlib.pbkdf2_hmac` + salt) y reglas de promoción en cascada inversa.
2. **Puertos (`puertos/`):**
   * Contratos e interfaces abstractas (`abc.ABC`) sin dependencias de SQLite, Tkinter ni Adaptadores: `repositorio_asistencia.py`, `repositorio_clase.py`, `repositorio_estudiante.py`, `repositorio_listados.py`, `repositorio_profesor.py`, `repositorio_promocion.py`, `repositorio_reportes.py`, `repositorio_usuario.py`.
3. **Capa de Adaptadores (`adaptadores/`):**
   * **Persistencia (`adaptadores/db/`):** `sqlite_asistencia.py`, `sqlite_clase.py`, `sqlite_estudiante.py`, `sqlite_listados.py`, `sqlite_profesor.py`, `sqlite_promocion.py`, `sqlite_reportes.py`, `sqlite_usuario.py`.
   * **Respaldo (`adaptadores/respaldo/`):** `json_asistencia.py` (gestión síncrona en `memoria_emergencia.json` ante apagones).
   * **Documentos e Imágenes (`adaptadores/documentos/`):** `pdf_reportes.py` (ReportLab Platypus) y `gestor_fotos.py` (Pillow, almacenamiento JPEG 240x240 en `fotos/`).
   * **Presentación / UI (`adaptadores/ui/`):** `utilidades_ui.py`, `ui_login.py`, `ui_menu_principal.py`, `ui_profesor.py`, `ui_clase.py`, `ui_estudiante.py`, `ui_asistencia.py`, `ui_listados.py`, `ui_reportes.py`, `ui_promocion.py`, `ui_usuario.py`. **PROHIBIDO** importar `sqlite3` o `db_conexion` dentro de `adaptadores/ui/`.
4. **Infraestructura Base y Ensamblaje (`db_conexion.py`, `main.py`, `scripts/`):**
   * `db_conexion.py`: Conexión SQLite, resolución de rutas portátiles (desarrollo y PyInstaller), soporte `:memory:` para pruebas, activación de `PRAGMA foreign_keys = ON` y `PRAGMA journal_mode = WAL`, DDL inicial y migración en caliente `_migrar_esquema(cursor)`.
   * `main.py`: Punto de entrada y composición raíz (*Composition Root*) para inyección de dependencias y orquestación Login ↔ Dashboard ↔ Módulos.
   * `scripts/`: Scripts auxiliares operativos (p. ej., `scripts/poblar_datos_prueba.py`).
5. **Pruebas (`tests/`) y Referencia Histórica (`Sistema_Legacy/`):**
   * `tests/`: Pruebas unitarias, integración, E2E, resiliencia, cableado de botones y guardrails AST.
   * `Sistema_Legacy/`: Módulos monolíticos originales de referencia funcional. **PROHIBIDO** modificar o eliminar su contenido.

---

## 4. Modelo de Persistencia Real (SQLite 3 — `db_conexion.py`)
Toda conexión en `db_conexion.py` ejecuta obligatoriamente:
```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL; -- cuando ruta_db != ':memory:'
```
Además, `ConexionBD` soporta `:memory:` (conservando la conexión en memoria durante las pruebas con `cerrar()` y liberándola solo con `cerrar_definitivo()`).

### Tablas Oficiales (`sistema_escolar.db`)
1. **`TBL_AUDITORIA`**: `ID_AUDITORIA` (INTEGER PK AUTOINCREMENT), `FECHA_HORA` (TEXT), `USUARIO` (TEXT), `MODULO` (TEXT), `ACCION` (TEXT), `DETALLES` (TEXT).
2. **`TBL_USUARIOS`**: `ID_USUARIO` (INTEGER PK AUTOINCREMENT), `NOMBRE_COMPLETO` (TEXT), `USERNAME` (TEXT UNIQUE), `PASSWORD` (TEXT — hash PBKDF2-HMAC-SHA256 `salt$hash`), `ROL` (TEXT: `'ADMIN'`, `'ASISTENTE'`, `'DOCENTE'`), `ESTADO_ACTIVO` (INTEGER DEFAULT 1).
3. **`TBL_GRADOS`**: `ID_GRADO` (INTEGER PK, valores `1` al `6`: `'1er AÑO'` al `'5to AÑO'` y `6` = `'GRADUADO'`).
4. **`TBL_SECCIONES`**: `ID_SECCION` (INTEGER PK AUTOINCREMENT), `DESCRIPCION` (TEXT UNIQUE — catálogo dinámico completo de 26 secciones `'A'`–`'Z'`).
5. **`TBL_PROFESORES`**: `ID_PROFESOR` (INTEGER PK AUTOINCREMENT), `CEDULA` (TEXT UNIQUE), `NOMBRE_COMPLETO` (TEXT), `ESTADO_ACTIVO` (INTEGER DEFAULT 1), `PROFESION` (TEXT DEFAULT `''`), `FOTO_PATH` (TEXT DEFAULT `''`).
6. **`TBL_ESTUDIANTES`**: `ID_ESTUDIANTE` (TEXT PK), `NOMBRE` (TEXT NOT NULL), `FECHA_NACIMIENTO` (TEXT), `REPRESENTANTE` (TEXT), `TELEFONO` (TEXT), `GENERO` (TEXT), `ESCOLARIDAD` (TEXT), `TURNO` (TEXT), `CONDICION` (TEXT), `ID_GRADO` (INTEGER FK -> `TBL_GRADOS`), `ID_SECCION` (INTEGER FK -> `TBL_SECCIONES`), `ESTADO_ACTIVO` (INTEGER DEFAULT 1), `NOMBRE_MADRE` (TEXT DEFAULT `''`), `TELEFONO_MADRE` (TEXT DEFAULT `''`), `NOMBRE_PADRE` (TEXT DEFAULT `''`), `TELEFONO_PADRE` (TEXT DEFAULT `''`), `FOTO_PATH` (TEXT DEFAULT `''`). *(Nota: las columnas de Fase A de madre/padre/foto conviven conservando `REPRESENTANTE` y `TELEFONO`).*
7. **`TBL_CLASES`**: `ID_CLASE` (INTEGER PK AUTOINCREMENT), `NOMBRE_MATERIA` (TEXT), `ID_PROFESOR` (INTEGER FK -> `TBL_PROFESORES`), `ID_GRADO` (INTEGER FK -> `TBL_GRADOS`), `ID_SECCION` (INTEGER FK -> `TBL_SECCIONES`).
8. **`TBL_ASISTENCIA`**: `ID_ASISTENCIA` (INTEGER PK AUTOINCREMENT), `ID_CLASE` (INTEGER FK -> `TBL_CLASES` `ON DELETE CASCADE`), `ID_ESTUDIANTE` (TEXT FK -> `TBL_ESTUDIANTES` `ON DELETE CASCADE ON UPDATE CASCADE`), `FECHA` (TEXT), `ESTADO` (TEXT: `'P'`, `'A'`, `'J'`).
9. **`TBL_JUSTIFICACIONES`**: `ID_JUSTIFICACION` (INTEGER PK AUTOINCREMENT), `ID_ASISTENCIA` (INTEGER UNIQUE FK -> `TBL_ASISTENCIA` `ON DELETE CASCADE`), `MOTIVO` (TEXT).

### Regla Obligatoria de Migración en Caliente
* `sistema_escolar.db` **ya existe en disco** en producción y desarrollo.
* Todo cambio de esquema o catálogo **DEBE** implementarse de forma **idempotente** dentro de `ConexionBD._migrar_esquema(cursor)` en `db_conexion.py`, inspeccionando primero mediante `PRAGMA table_info(...)` antes de ejecutar `ALTER TABLE ... ADD COLUMN`, y usando inserciones no duplicadas (`INSERT OR IGNORE`) para catálogos.
* Nunca asumir que la base de datos se creará desde cero en ejecución real.

---

## 5. Reglas de Negocio Invariables (Invariants)
* **Consultas SQL Parametrizadas:** NUNCA concatenar variables en strings SQL. Usar siempre marcadores `?`.
* **Borrado Lógico (*Soft Delete*):** `TBL_USUARIOS`, `TBL_PROFESORES` y `TBL_ESTUDIANTES` usan `ESTADO_ACTIVO = 1` (activo) y `0` (desactivado).
* **Control de Permisos (RBAC — `dominio/permisos.py`):**
  * `ADMIN`: Acceso total a los 7 módulos.
  * `ASISTENTE`: Estudiantes, Asistencia, Listados y Reportes PDF. Sin acceso a Gestión Académica, Promoción Anual ni Gestión de Usuarios.
  * `DOCENTE`: Asistencia y Listados. Sin acceso a Estudiantes, Gestión Académica, Reportes PDF, Promoción ni Usuarios.
* **Tolerancia a Fallos Eléctricos (Anti-Apagones):**
  * Cada marcaje (`P`, `A`, `J`) se serializa síncronamente en `memoria_emergencia.json`.
  * Al abrir una clase, si existe respaldo concordante para `(ID_CLASE, FECHA)`, ofrecer restaurar la sesión inconclusa.
  * Al guardar definitivamente: transacción atómica con `DELETE` previo en `TBL_ASISTENCIA` para `(ID_CLASE, FECHA)`, inserción de registros y justificaciones, `COMMIT` y limpieza de `memoria_emergencia.json`.
* **Cálculo Legal del 75% (Art. 109 RGLOE — `dominio/reportes.py`):**
  * Fórmula: `porcentaje = round((asistencias_efectivas / total_clases) * 100.0, 2)` donde `asistencias_efectivas = presentes + justificadas`.
  * Si `total_clases <= 0`, retorna `100.0` (sin `ZeroDivisionError` ni falsa alarma).
  * Si `porcentaje < 75.0`, marcar en **ALERTA DE RIESGO**.
* **Promoción Anual en Cascada Inversa (`dominio/promocion.py`):**
  * Transiciones descendentes `(5->6, 4->5, 3->4, 2->3, 1->2)` en una única transacción atómica protegida por clave maestra.

---

## 6. Reglas de UI/UX y Tkinter Multiplataforma (Linux/X11 + Windows, Base 1024x768)
1. **Cirugía Mínima en UI:**
   * **PROHIBIDO** rediseñar ventanas, paletas de colores, tipografías o layouts existentes que ya funcionan.
   * Solo agregar los campos, controles o pestañas estrictamente solicitados, manteniendo legibilidad y ajuste limpio en resolución base `1024x768` (si hay 4+ botones en un bloque, preferir cuadrícula 2x2 y añadir tooltips con `AyudaVisual`).
2. **Ventanas Maximizadas Post-Login:**
   * El Login (`adaptadores/ui/ui_login.py`) y los modales emergentes compactos (alta rápida de usuario desde login, diálogo de justificación de falta, modal de alertas de riesgo, selector compacto de clase) permanecen compactos y centrados con `centrar_ventana(...)`.
   * El Panel de Control (`adaptadores/ui/ui_menu_principal.py`) y **todas** las ventanas principales de módulos (`Toplevel`: Gestión Académica, Estudiantes, Planilla de Asistencia, Listados, Reportes, Promoción Anual y Usuarios) **DEBEN** abrirse maximizadas por defecto usando el helper central `maximizar_ventana(...)` de `adaptadores/ui/utilidades_ui.py` (nunca llamar `state('zoomed')` crudo fuera de `utilidades_ui.py`).
3. **Z-Order y Foco en Linux/X11:**
   * El **100%** de llamadas a `messagebox.*`, `filedialog.*` y `simpledialog.*` en `adaptadores/ui/` **DEBEN** pasar `parent=` explícito y llamar a `restaurar_foco(...)` tras cerrarse.
   * Toda ventana secundaria abierta desde el Panel de Control usa `configurar_ventana_hija(...)` y `agregar_barra_superior_volver(...)`.
4. **Imágenes con Pillow (`adaptadores/documentos/gestor_fotos.py`):**
   * Nunca guardar BLOBs en SQLite ni rutas absolutas. Guardar JPEG optimizado (`240x240` px) en `fotos/` (ignorado en `.gitignore`) almacenando únicamente la ruta relativa POSIX (ej. `fotos/estudiantes/V_31201101.jpg`).
   * En vistas previas Tkinter: pasar siempre `master=widget` al crear `ImageTk.PhotoImage`, retener referencia viva en el widget (`lbl_foto.image`) y en la instancia (`self._foto_preview_ref`), y encerrar la vista previa en un `Frame` fijo con `pack_propagate(False)`.

---

## 7. Estándares de Código y Criterio de Terminado (Definition of Done)
* **Estilo:** PEP 8, `snake_case` para funciones/variables/archivos, `PascalCase` para clases, *type hints* en el núcleo y docstrings claros en español.
* **Aislamiento de pruebas:** Todas las pruebas de BD deben usar `:memory:` o `tmp_path` de `pytest`, **NUNCA** `sistema_escolar.db` de producción.
* **Criterio de Terminado Obligatorio (DoD):**
  1. Ejecutar `.venv/bin/pytest -v` con **0 fallos y 0 tests saltados** (100% en verde).
  2. Mantener en verde los guardrails AST: `tests/test_arquitectura_hexagonal.py` y `tests/test_ux_ventanas_y_widgets.py`.
  3. Todo botón o acción nueva en la UI debe quedar cubierto en `tests/test_ui_botones_cableado.py`, invocando su acción real con diálogos mockeados para detectar desfases de firma o errores de cableado.
