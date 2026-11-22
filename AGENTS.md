# AGENTS.md — Sistema de Gestión de Asistencia Estudiantil (Complejo Educativo "Colinas del Llano")

Este documento define las reglas arquitectónicas, el modelo de datos, los requerimientos funcionales y los estándares de calidad obligatorios para todos los agentes y subagentes que trabajen en este repositorio.

---

## 1. Contexto del Proyecto
* **Nombre:** Sistema de Información para la Gestión de Asistencia Estudiantil — Coordinación de 4to Año del Complejo Educativo "Colinas del Llano" (Barinas, Venezuela).
* **Tipo de aplicación:** Aplicación de escritorio **offline-first**, monousuario, ligera y portable (empaquetable en `.exe` con PyInstaller).
* **Normativa legal clave:** Artículo 109 del Reglamento General de la Ley Orgánica de Educación (RGLOE) — exige un mínimo del **75% de asistencia efectiva** para la aprobación escolar.
* **Metodología:** Feature Driven Development (FDD) + Pruebas Unitarias obligatorias por cada módulo.

---

## 2. Stack Tecnológico Permitido (Estrictamente Software Libre / Local)
* **Lenguaje:** Python 3.10+.
* **Interfaz Gráfica (GUI):** `tkinter` y `ttk` (biblioteca estándar), `tkcalendar` (`DateEntry`), `Pillow` (`PIL` para carga de escudo institucional).
* **Base de Datos:** `sqlite3` (embebida, archivo local `sistema_escolar.db`).
* **Respaldo de contingencia:** `json` (biblioteca estándar, archivo `memoria_emergencia.json`).
* **Reportes PDF:** `reportlab` (`reportlab.platypus`).
* **Pruebas Unitarias:** `pytest` (o `unittest`).
* **Restricción:** NO agregar frameworks web, ORMs pesados, ni dependencias que requieran conexión a Internet o servidores externos.

---

## 3. Arquitectura de Software (Patrón Hexagonal / Puertos y Adaptadores)
Respetar estrictamente la separación de responsabilidades y los principios **SOLID**:

1. **Núcleo de Dominio (`dominio/`):**
   * Python puro. **PROHIBIDO** importar `tkinter` o ejecutar SQL directo dentro del dominio puro.
   * Contiene las entidades, validaciones de negocio, cálculo del porcentaje de asistencia (regla legal del 75% Art. 109 RGLOE), lógica de seguridad/hashing de contraseñas (`hashlib.pbkdf2_hmac` + salt) y reglas de promoción en cascada inversa.
2. **Puertos (`puertos/`):**
   * Contratos e interfaces abstractas (`abc.ABC`) que declaran las operaciones que el dominio necesita de la infraestructura (repositorios de datos, respaldos de emergencia y exportación a PDF).
3. **Capa de Adaptadores (`adaptadores/`):**
   * **Persistencia (`adaptadores/db/`):** SQLite 3 cumpliendo los contratos de los puertos.
   * **Respaldo (`adaptadores/respaldo/`):** Gestión síncrona en archivo JSON de emergencia ante apagones.
   * **Presentación / UI (`adaptadores/ui/`):** Interfaces gráficas en Tkinter / ttk desacopladas del SQL.
   * **Documentos / PDF (`adaptadores/documentos/` o `adaptadores/pdf/`):** Generación de documentos oficiales con ReportLab Platypus.
4. **Infraestructura Base y Ensamblaje (`db_conexion.py`, `main.py`):**
   * `db_conexion.py`: Conexión SQLite, resolución de rutas portátiles, activación de `PRAGMA foreign_keys = ON` y `PRAGMA journal_mode = WAL`, y DDL inicial.
   * `main.py`: Punto de entrada y composición raíz (*Composition Root*) para inyección de dependencias.
5. **Código Previo de Referencia (`Sistema Legacy/`):**
   * Contiene los módulos monolíticos originales que sirven de especificación y referencia funcional durante la migración hacia adaptadores hexagonales.

---

## 4. Modelo de Persistencia (SQLite 3 — Tercera Forma Normal 3FN)
Toda conexión en `db_conexion.py` **DEBE** ejecutar obligatoriamente:
```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
```

### Tablas Oficiales (`sistema_escolar.db`)
1. **`TBL_AUDITORIA`**: `ID_AUDITORIA` (INTEGER PK AUTOINCREMENT), `FECHA_HORA` (TEXT), `USUARIO` (TEXT), `MODULO` (TEXT), `ACCION` (TEXT), `DETALLES` (TEXT).
2. **`TBL_USUARIOS`**: `ID_USUARIO` (INTEGER PK AUTOINCREMENT), `NOMBRE_COMPLETO` (TEXT NOT NULL), `USERNAME` (TEXT UNIQUE NOT NULL), `PASSWORD` (TEXT NOT NULL — siempre almacenada con hash seguro PBKDF2 con salt), `ROL` (TEXT NOT NULL DEFAULT `'ASISTENTE'`, valores: `'ADMIN'`, `'ASISTENTE'`, `'DOCENTE'`), `ESTADO_ACTIVO` (INTEGER DEFAULT 1).
3. **`TBL_GRADOS`**: `ID_GRADO` (INTEGER PK, 1 al 6), `DESCRIPCION` (TEXT NOT NULL UNIQUE, ej. `'1er AÑO'` al `'5to AÑO'`, y `'GRADUADO'`).
4. **`TBL_SECCIONES`**: `ID_SECCION` (INTEGER PK AUTOINCREMENT), `DESCRIPCION` (TEXT NOT NULL UNIQUE, `'A'`, `'B'`, `'C'`, `'D'`, `'E'`).
5. **`TBL_PROFESORES`**: `ID_PROFESOR` (INTEGER PK AUTOINCREMENT), `CEDULA` (TEXT UNIQUE NOT NULL), `NOMBRE_COMPLETO` (TEXT NOT NULL), `ESTADO_ACTIVO` (INTEGER DEFAULT 1).
6. **`TBL_ESTUDIANTES`**: `ID_ESTUDIANTE` (TEXT PK — cédula escolar/identidad), `NOMBRE` (TEXT NOT NULL), `FECHA_NACIMIENTO` (TEXT NOT NULL, formato `YYYY-MM-DD`), `REPRESENTANTE` (TEXT NOT NULL), `TELEFONO` (TEXT NULL), `GENERO` (TEXT NOT NULL, `'M'` o `'F'`), `ESCOLARIDAD` (TEXT NOT NULL DEFAULT `'Regular'`, valores: `'Regular'`, `'Materia Pendiente'`, `'Repite'`), `TURNO` (TEXT NOT NULL DEFAULT `'Mañana'`, valores: `'Mañana'`, `'Tarde'`), `CONDICION` (TEXT NOT NULL DEFAULT `'Activo'`, valores: `'Activo'`, `'Preinscrito'`), `ID_GRADO` (INTEGER FK -> `TBL_GRADOS`), `ID_SECCION` (INTEGER FK -> `TBL_SECCIONES`), `ESTADO_ACTIVO` (INTEGER DEFAULT 1).
7. **`TBL_CLASES`**: `ID_CLASE` (INTEGER PK AUTOINCREMENT), `NOMBRE_MATERIA` (TEXT NOT NULL), `ID_PROFESOR` (INTEGER FK -> `TBL_PROFESORES`), `ID_GRADO` (INTEGER FK -> `TBL_GRADOS`), `ID_SECCION` (INTEGER FK -> `TBL_SECCIONES`).
8. **`TBL_ASISTENCIA`**: `ID_ASISTENCIA` (INTEGER PK AUTOINCREMENT), `ID_CLASE` (INTEGER FK -> `TBL_CLASES` `ON DELETE CASCADE`), `ID_ESTUDIANTE` (TEXT FK -> `TBL_ESTUDIANTES` `ON UPDATE CASCADE` `ON DELETE CASCADE`), `FECHA` (TEXT NOT NULL, `YYYY-MM-DD`), `ESTADO` (TEXT NOT NULL, `'P'`, `'A'`, `'J'`).
9. **`TBL_JUSTIFICACIONES`**: `ID_JUSTIFICACION` (INTEGER PK AUTOINCREMENT), `ID_ASISTENCIA` (INTEGER FK -> `TBL_ASISTENCIA` `ON DELETE CASCADE` UNIQUE), `MOTIVO` (TEXT NOT NULL).

---

## 5. Reglas de Negocio Invariables (Invariants)
* **Consultas SQL Parametrizadas:** NUNCA concatenar variables en strings SQL. Usar siempre marcadores `?` para evitar inyección SQL.
* **Borrado Lógico (*Soft Delete*):** Entidades como Usuarios, Profesores y Estudiantes usan `ESTADO_ACTIVO = 1` (activo) y `0` (desactivado) para preservar integridad referencial e historial académico.
* **Control de Permisos (RBAC):**
  * `ADMIN`: Acceso total (incluyendo Carga Académica, Promoción Anual y Gestión de Usuarios).
  * `ASISTENTE`: Gestión de Estudiantes, Asistencia, Listados y Reportes PDF. Sin acceso a Carga Académica, Promoción ni alta de usuarios.
  * `DOCENTE`: Toma de Asistencia y Listados (solo lectura). Botones de Estudiantes, Gestión Académica, Reportes y Promoción deshabilitados (`state='disabled'`).
* **Tolerancia a Fallos Eléctricos (Anti-Apagones):**
  * Cada marcaje (`P`, `A`, `J`) en el pase de lista debe serializarse de forma síncrona en `memoria_emergencia.json`.
  * Al abrir una clase, si existe `memoria_emergencia.json` correspondiente a la clase y fecha actual, ofrecer restaurar la sesión inconclusa.
  * Al confirmar el guardado definitivo: abrir transacción atómica, ejecutar `DELETE` previo en `TBL_ASISTENCIA` para `(ID_CLASE, FECHA)` evitando duplicados, insertar asistencias y justificaciones, hacer `COMMIT` y eliminar `memoria_emergencia.json`.
* **Cálculo Legal del 75% (Art. 109 RGLOE):**
  * Fórmula: `porcentaje = (asistencias_efectivas / total_clases_dictadas) * 100`.
  * Manejar división por cero (`total_clases_dictadas == 0` -> retornar estado sin datos o `100.0%` según regla explícita, sin lanzar `ZeroDivisionError`).
  * Si `porcentaje < 75.0`, marcar en estado de **ALERTA DE RIESGO** (visualizado en rojo/ámbar).
* **Promoción Anual en Cascada Inversa:**
  * Actualizar grados estrictamente en orden descendente (5to -> 6to Graduado, 4to -> 5to, 3ro -> 4to, 2do -> 3ro, 1ro -> 2do) dentro de una única transacción atómica protegida por clave maestra.

---

## 6. Estándares de Código y Pruebas Unitarias (Obligatorio)
* **Estilo:** PEP 8, nombres de funciones, variables y archivos en `snake_case`, clases en `PascalCase`, *type hints* en funciones del núcleo y docstrings claros en español.
* **Regla de Finalización (Definition of Done):**
  * Ninguna funcionalidad o módulo está terminado hasta que existan pruebas unitarias en `tests/test_<modulo>.py` y `pytest` pase al **100%**.
  * Todas las pruebas de base de datos deben ejecutarse sobre una base de datos temporal (`tmp_path` de `pytest` o `:memory:`), **NUNCA** sobre `sistema_escolar.db` de producción.
  * Cubrir siempre casos felices y casos límite (campos vacíos, cédula duplicada `IntegrityError`, credenciales inválidas, exactamente `75.0%` vs `74.9%`, simulación de apagón con JSON residual y prevención de registros duplicados en la misma fecha/clase).
