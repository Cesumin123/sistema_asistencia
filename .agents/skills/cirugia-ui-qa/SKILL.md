---
name: cirugia-ui-qa
description: Protocolo de cirugía mínima y QA obligatorio al agregar o modificar campos, botones, pantallas Tkinter o funcionalidades de extremo a extremo en este repositorio.
---

# Cirugía Mínima y QA en Tkinter / Arquitectura Hexagonal

Activa esta skill cada vez que debas añadir o modificar campos, botones, pestañas, flujos de usuario o funcionalidades completas (Dominio → Puertos → Persistencia → UI → PDF) sin romper la arquitectura ni la compatibilidad Linux/X11 + Windows.

## Protocolo Obligatorio en 6 Pasos

### 1. Auditar contratos antes de editar
- Verifica las firmas exactas de clases, métodos y constructores en `dominio/`, `puertos/`, `adaptadores/` y el *Composition Root* en `main.py` antes de escribir una sola línea de cambio.
- Comprueba qué repositorios o servicios se inyectan en `main.py` para prevenir errores de argumentos faltantes (`TypeError`) o atributos inexistentes (`AttributeError`).

### 2. Retrocompatibilidad y migración en caliente
- En `dominio/`, agrega todo atributo nuevo **siempre al final** de `__init__` o `@dataclass` con un valor por defecto seguro.
- `sistema_escolar.db` ya existe en disco: todo cambio de tabla, columna o catálogo debe implementarse de forma **idempotente** en `ConexionBD._migrar_esquema(cursor)` (`db_conexion.py`) usando `PRAGMA table_info(...)` + `ALTER TABLE` o `INSERT OR IGNORE`.
- Agrega un test que verifique la migración partiendo de una BD con el esquema previo.

### 3. Cirugía mínima en Tkinter (base 1024x768)
- **PROHIBIDO** rediseñar paletas, tipografías, estilos globales ni layouts existentes que ya funcionan.
- Agrega únicamente los controles solicitados, manteniendo legibilidad en `1024x768`.
- Evita filas sobrecargadas con demasiados botones: si un bloque tiene **4 o más acciones**, organízalas en cuadrícula `2x2` (`grid`) con `uniform`.
- Añade tooltips descriptivos con `AyudaVisual(widget, texto)` de `adaptadores/ui/utilidades_ui.py` a los botones o campos nuevos.

### 4. Checklist Multiplataforma Linux/X11 + Windows
- **Ventanas post-login maximizadas:** Invoca `maximizar_ventana(...)` de `utilidades_ui.py` en el Panel de Control y en toda ventana principal de módulo (`Toplevel`). Nunca llames `state('zoomed')` crudo ni maximices `ui_login.py` o modales pequeños.
- **Z-Order y foco:** Pasa `parent=` explícito en el 100% de llamadas a `messagebox.*`, `filedialog.*` y `simpledialog.*`, y llama a `restaurar_foco(...)` tras cerrarse. Usa `configurar_ventana_hija(...)` y `agregar_barra_superior_volver(...)` en ventanas secundarias.
- **Imágenes con Pillow:** Pasa `master=` en `ImageTk.PhotoImage`, retén referencia viva en el widget y en la instancia (`self._foto_preview_ref`), y usa un contenedor `Frame` fijo con `pack_propagate(False)`. Nunca guardes BLOBs ni rutas absolutas.
- **Desacoplamiento estricto:** 0 importaciones de `sqlite3` o `db_conexion` en `adaptadores/ui/`, `dominio/` y `puertos/`. Sin librerías pesadas (`matplotlib`, `pandas`, `numpy`).

### 5. Pruebas obligatorias de cableado y guardrails
- Escribe pruebas unitarias y de integración usando `:memory:` o `tmp_path` (nunca `sistema_escolar.db` de producción).
- Añade una prueba de clic real para cada botón nuevo en `tests/test_ui_botones_cableado.py` (invocando el comando/callback real con `messagebox`/`filedialog`/`simpledialog` mockeados para atrapar desfases de firma).
- Verifica los guardrails AST en `tests/test_arquitectura_hexagonal.py` y `tests/test_ux_ventanas_y_widgets.py`.

### 6. Validación final
- Ejecuta `.venv/bin/pytest -v` y exige **0 fallos y 0 tests saltados**.
- Reporta de forma exacta los archivos creados/modificados y el resumen real de las pruebas ejecutadas.
