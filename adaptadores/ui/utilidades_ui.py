# adaptadores/ui/utilidades_ui.py
"""
Sistema de Diseño Unificado — Complejo Educativo 'Colinas del Llano'.

Módulo central que define:
- Paleta institucional coherente
- Tipografías legibles multiplataforma
- Estilos ttk modernos (Treeview zebra, botones hover, tarjetas)
- Utilidades multiplataforma (centrado, maximizado seguro)
- Componente reutilizable de Tooltips (AyudaVisual)
"""

import tkinter as tk
from tkinter import ttk
import platform
import subprocess
import os
from typing import Optional

def abrir_archivo_sistema(ruta_archivo: str) -> bool:
    """
    Abre un archivo con el visor predeterminado del sistema operativo
    de forma segura y no bloqueante (Windows, Linux, macOS).
    """
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return False
    try:
        so = platform.system()
        if so == "Windows":
            os.startfile(ruta_archivo)
            return True
        elif so == "Darwin":
            subprocess.Popen(["open", ruta_archivo])
            return True
        else:
            subprocess.Popen(["xdg-open", ruta_archivo])
            return True
    except Exception as e:
        print(f"Aviso abrir archivo: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════
# 1. PALETA INSTITUCIONAL
# ═══════════════════════════════════════════════════════════════════
COLOR_FONDO_APP = "#F4F6F9"           # Fondo neutro general
COLOR_TARJETA = "#FFFFFF"             # Fondo tarjetas / paneles
COLOR_BORDE_TARJETA = "#DCE1E8"       # Borde sutil de tarjetas
COLOR_PRIMARIO = "#2C3E50"            # Azul institucional oscuro
COLOR_PRIMARIO_HOVER = "#1A252F"      # Hover del primario
COLOR_SECUNDARIO = "#3498DB"          # Azul medio (botones secundarios)
COLOR_SECUNDARIO_HOVER = "#2980B9"    # Hover del secundario
COLOR_ACENTO = "#27AE60"              # Verde (éxito, guardar)
COLOR_ACENTO_HOVER = "#219A52"        # Hover del acento
COLOR_PELIGRO = "#C0392B"             # Rojo (eliminar, alertas críticas)
COLOR_PELIGRO_HOVER = "#A93226"       # Hover del peligro
COLOR_ADVERTENCIA = "#F39C12"         # Ámbar (advertencias)
COLOR_ADVERTENCIA_HOVER = "#D68910"   # Hover de advertencia
COLOR_TEXTO_PRINCIPAL = "#2C3E50"     # Texto principal oscuro
COLOR_TEXTO_SECUNDARIO = "#7F8C8D"    # Texto auxiliar / placeholder
COLOR_TEXTO_CLARO = "#FFFFFF"         # Texto sobre fondos oscuros
COLOR_SEPARADOR = "#E5E7E9"           # Líneas separadoras
COLOR_SIDEBAR = "#2C3E50"             # Panel lateral institucional
COLOR_SIDEBAR_HEADER = "#1A252F"      # Header del sidebar
COLOR_FILA_PAR = "#FFFFFF"            # Treeview fila par (zebra)
COLOR_FILA_IMPAR = "#F2F4F7"          # Treeview fila impar (zebra)
COLOR_TREEVIEW_HEADER = "#34495E"     # Cabecera de tabla
COLOR_ALERTA_RIESGO_BG = "#FADBD8"   # Fondo rojo suave alertas < 75%
COLOR_ALERTA_RIESGO_FG = "#78281F"   # Texto rojo oscuro alertas < 75%
COLOR_BADGE_ADMIN = "#27AE60"
COLOR_BADGE_ASISTENTE = "#2980B9"
COLOR_BADGE_DOCENTE = "#E67E22"

# ═══════════════════════════════════════════════════════════════════
# 2. TIPOGRAFÍAS MULTIPLATAFORMA
# ═══════════════════════════════════════════════════════════════════
_so = platform.system()
if _so == "Windows":
    FUENTE_FAMILIA = "Segoe UI"
elif _so == "Darwin":
    FUENTE_FAMILIA = "Helvetica Neue"
else:
    FUENTE_FAMILIA = "DejaVu Sans"

FUENTE_TITULO = (FUENTE_FAMILIA, 18, "bold")
FUENTE_SUBTITULO = (FUENTE_FAMILIA, 14, "bold")
FUENTE_ENCABEZADO = (FUENTE_FAMILIA, 12, "bold")
FUENTE_CUERPO = (FUENTE_FAMILIA, 10)
FUENTE_CUERPO_BOLD = (FUENTE_FAMILIA, 10, "bold")
FUENTE_PEQUEÑA = (FUENTE_FAMILIA, 9)
FUENTE_PEQUEÑA_BOLD = (FUENTE_FAMILIA, 9, "bold")
FUENTE_ETIQUETA = (FUENTE_FAMILIA, 10, "bold")
FUENTE_BOTON = (FUENTE_FAMILIA, 10, "bold")
FUENTE_TOOLTIP = (FUENTE_FAMILIA, 8)


# ═══════════════════════════════════════════════════════════════════
# 3. ESTILOS TTK GLOBALES
# ═══════════════════════════════════════════════════════════════════
def aplicar_tema_global(root: tk.Tk = None):
    """
    Aplica los estilos ttk modernos a toda la aplicación.
    Debe llamarse una vez tras crear la raíz tk.Tk().
    """
    estilo = ttk.Style()

    # Usar tema base clam (el más personalizable en cross-platform)
    try:
        estilo.theme_use("clam")
    except Exception:
        pass

    # --- Treeview ---
    estilo.configure(
        "Treeview",
        background=COLOR_FILA_PAR,
        foreground=COLOR_TEXTO_PRINCIPAL,
        fieldbackground=COLOR_FILA_PAR,
        font=FUENTE_CUERPO,
        rowheight=28,
        borderwidth=0,
    )
    estilo.configure(
        "Treeview.Heading",
        background=COLOR_TREEVIEW_HEADER,
        foreground=COLOR_TEXTO_CLARO,
        font=FUENTE_PEQUEÑA_BOLD,
        relief="flat",
        padding=(8, 4),
    )
    estilo.map(
        "Treeview.Heading",
        background=[("active", COLOR_PRIMARIO_HOVER)],
    )
    estilo.map(
        "Treeview",
        background=[("selected", COLOR_SECUNDARIO)],
        foreground=[("selected", COLOR_TEXTO_CLARO)],
    )

    # --- Notebook / Pestañas ---
    estilo.configure(
        "TNotebook",
        background=COLOR_FONDO_APP,
        borderwidth=0,
    )
    estilo.configure(
        "TNotebook.Tab",
        background=COLOR_SEPARADOR,
        foreground=COLOR_TEXTO_PRINCIPAL,
        font=FUENTE_PEQUEÑA_BOLD,
        padding=(14, 6),
    )
    estilo.map(
        "TNotebook.Tab",
        background=[("selected", COLOR_TARJETA)],
        foreground=[("selected", COLOR_PRIMARIO)],
    )

    # --- Combobox ---
    estilo.configure(
        "TCombobox",
        font=FUENTE_CUERPO,
    )

    # --- Scrollbar (más fina y moderna) ---
    estilo.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=COLOR_SEPARADOR,
        troughcolor=COLOR_FONDO_APP,
        borderwidth=0,
        width=10,
    )

    # --- Entry ---
    estilo.configure(
        "TEntry",
        font=FUENTE_CUERPO,
    )

    return estilo


# ═══════════════════════════════════════════════════════════════════
# 4. UTILIDADES MULTIPLATAFORMA
# ═══════════════════════════════════════════════════════════════════
def centrar_ventana(ventana: tk.Tk | tk.Toplevel, ancho: int, alto: int):
    """Centra una ventana en la pantalla de forma segura."""
    try:
        ventana.update_idletasks()
        sw = ventana.winfo_screenwidth()
        sh = ventana.winfo_screenheight()
        x = max(0, int((sw - ancho) / 2))
        y = max(0, int((sh - alto) / 2))
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
    except Exception:
        ventana.geometry(f"{ancho}x{alto}")


def _aplicar_maximizacion(ventana: tk.Tk | tk.Toplevel):
    """Aplica maximización multiplataforma y geometría de respaldo sin lanzar TclError."""
    if ventana is None:
        return
    try:
        if not hasattr(ventana, "winfo_exists") or not ventana.winfo_exists():
            return
    except Exception:
        return

    try:
        ventana.update_idletasks()
    except Exception:
        pass

    # 1. Windows (o entornos que soportan state('zoomed'))
    try:
        ventana.state("zoomed")
        return
    except Exception:
        pass

    # 2. Linux / X11 / Wayland: attributes('-zoomed', True) + geometría de respaldo
    try:
        sw = ventana.winfo_screenwidth()
        sh = ventana.winfo_screenheight()
        if sw > 0 and sh > 0:
            ancho_actual = ventana.winfo_width()
            alto_actual = ventana.winfo_height()
            if ancho_actual < int(sw * 0.9) or alto_actual < int(sh * 0.9):
                ventana.geometry(f"{sw}x{sh}+0+0")
                ventana.update_idletasks()
    except Exception:
        pass

    try:
        ventana.attributes("-zoomed", True)
    except Exception:
        pass

    try:
        ventana.update_idletasks()
    except Exception:
        pass


def maximizar_ventana(ventana: tk.Tk | tk.Toplevel):
    """Maximiza una ventana de forma segura en Windows/Linux/macOS sin TclError."""
    if ventana is None:
        return
    _aplicar_maximizacion(ventana)
    try:
        if hasattr(ventana, "winfo_exists") and ventana.winfo_exists():
            ventana.after(60, lambda v=ventana: _aplicar_maximizacion(v))
    except Exception:
        pass


def configurar_ventana_hija(ventana: tk.Toplevel, padre: Optional[tk.Misc] = None):
    """Configura transient, lift y foco para ventanas secundarias en Linux/Windows."""
    if padre and hasattr(padre, "winfo_exists") and padre.winfo_exists():
        try:
            ventana.transient(padre)
        except Exception:
            pass
    try:
        ventana.lift()
        ventana.focus_set()
    except Exception:
        pass


def restaurar_foco(widget: tk.Misc):
    """Devuelve el foco y eleva la ventana toplevel actual tras cerrar un diálogo."""
    try:
        if widget and hasattr(widget, "winfo_toplevel"):
            top = widget.winfo_toplevel()
            if top and hasattr(top, "winfo_exists") and top.winfo_exists():
                top.lift()
                top.focus_force()
    except Exception:
        pass


def agregar_barra_superior_volver(ventana: tk.Toplevel, padre: Optional[tk.Misc] = None, titulo: str = "") -> tk.Frame:
    """
    Agrega una barra superior mínima y uniforme con botón '← Volver al Panel'
    que destruye la ventana secundaria y devuelve el foco a la ventana principal.
    """
    barra = tk.Frame(ventana, bg=COLOR_SIDEBAR_HEADER, height=36)
    
    # Ubicarla al tope de la ventana de forma segura
    try:
        slaves = ventana.pack_slaves()
        if slaves:
            barra.pack(side="top", fill="x", before=slaves[0])
        else:
            barra.pack(side="top", fill="x")
    except Exception:
        try:
            barra.pack(side="top", fill="x")
        except Exception:
            pass

    def volver():
        try:
            ventana.destroy()
        finally:
            if padre and hasattr(padre, "winfo_exists") and padre.winfo_exists():
                try:
                    padre.lift()
                    padre.focus_force()
                except Exception:
                    pass

    btn_volver = tk.Button(
        barra,
        text="← Volver al Panel",
        font=FUENTE_PEQUEÑA_BOLD,
        bg=COLOR_PRIMARIO,
        fg=COLOR_TEXTO_CLARO,
        activebackground=COLOR_PRIMARIO_HOVER,
        activeforeground=COLOR_TEXTO_CLARO,
        relief="flat",
        bd=0,
        padx=12,
        pady=4,
        cursor="hand2",
        command=volver,
    )
    btn_volver.pack(side="left", padx=10, pady=4)
    btn_volver.bind("<Enter>", lambda e: btn_volver.config(bg=COLOR_PRIMARIO_HOVER))
    btn_volver.bind("<Leave>", lambda e: btn_volver.config(bg=COLOR_PRIMARIO))

    if titulo:
        lbl_tit = tk.Label(
            barra,
            text=titulo,
            font=FUENTE_PEQUEÑA_BOLD,
            bg=COLOR_SIDEBAR_HEADER,
            fg="#BDC3C7"
        )
        lbl_tit.pack(side="left", padx=10)

    return barra


# ═══════════════════════════════════════════════════════════════════
# 5. FÁBRICAS DE WIDGETS ESTILIZADOS
# ═══════════════════════════════════════════════════════════════════
def crear_boton(
    parent,
    texto: str,
    comando=None,
    color_bg: str = COLOR_SECUNDARIO,
    color_fg: str = COLOR_TEXTO_CLARO,
    color_hover: str = None,
    ancho: int = None,
    fuente=None,
    habilitado: bool = True,
    **kwargs
) -> tk.Button:
    """Crea un botón estilizado con efecto hover y cursor de mano."""
    if fuente is None:
        fuente = FUENTE_BOTON
    if color_hover is None:
        color_hover = _oscurecer_color(color_bg)

    estado = "normal" if habilitado else "disabled"
    bg_real = color_bg if habilitado else "#BDC3C7"
    cursor = "hand2" if habilitado else "arrow"

    btn = tk.Button(
        parent,
        text=texto,
        font=fuente,
        bg=bg_real,
        fg=color_fg,
        activebackground=color_hover,
        activeforeground=color_fg,
        state=estado,
        cursor=cursor,
        relief="flat",
        bd=0,
        padx=16,
        pady=8,
        command=comando if habilitado else None,
        **kwargs,
    )

    if habilitado:
        btn.bind("<Enter>", lambda e: btn.config(bg=color_hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=color_bg))

    return btn


def crear_tarjeta(parent, **kwargs) -> tk.Frame:
    """Crea un frame tipo tarjeta blanca con borde suave."""
    return tk.Frame(
        parent,
        bg=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE_TARJETA,
        highlightthickness=1,
        padx=kwargs.get("padx", 24),
        pady=kwargs.get("pady", 20),
    )


def crear_separador(parent, orientacion="horizontal") -> tk.Frame:
    """Línea separadora sutil."""
    if orientacion == "horizontal":
        sep = tk.Frame(parent, bg=COLOR_SEPARADOR, height=1)
    else:
        sep = tk.Frame(parent, bg=COLOR_SEPARADOR, width=1)
    return sep


def crear_treeview_zebra(parent, columnas: tuple, encabezados: list,
                         anchos: list, anclas: list = None,
                         alto: int = 15) -> tuple:
    """
    Crea un Treeview con filas alternas zebra, scrollbar vertical y
    tags de riesgo preconfigurados.
    Retorna (tree, frame_contenedor).
    """
    frame = tk.Frame(parent, bg=COLOR_FONDO_APP)
    tree = ttk.Treeview(frame, columns=columnas, show="headings", height=alto)

    if anclas is None:
        anclas = ["w"] * len(columnas)

    for i, col in enumerate(columnas):
        tree.heading(col, text=encabezados[i])
        tree.column(col, width=anchos[i], anchor=anclas[i])

    # Tags para filas alternas
    tree.tag_configure("par", background=COLOR_FILA_PAR)
    tree.tag_configure("impar", background=COLOR_FILA_IMPAR)
    # Tags para alertas de riesgo (Art. 109 RGLOE)
    tree.tag_configure("alerta_riesgo", background=COLOR_ALERTA_RIESGO_BG, foreground=COLOR_ALERTA_RIESGO_FG)
    tree.tag_configure("regular", background=COLOR_FILA_PAR, foreground=COLOR_TEXTO_PRINCIPAL)
    # Tags para asistencia
    tree.tag_configure("presente", foreground="#27AE60")
    tree.tag_configure("ausente", foreground="#C0392B")
    tree.tag_configure("justificado", foreground="#D35400")

    scrollbar_v = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_v.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar_v.pack(side="right", fill="y")

    return tree, frame


def insertar_fila_zebra(tree: ttk.Treeview, valores: tuple, tag_extra: str = None):
    """Inserta una fila aplicando automáticamente el patrón zebra."""
    idx = len(tree.get_children())
    tag_zebra = "par" if idx % 2 == 0 else "impar"
    tags = (tag_extra,) if tag_extra else (tag_zebra,)
    tree.insert("", "end", values=valores, tags=tags)


# ═══════════════════════════════════════════════════════════════════
# 6. COMPONENTE TOOLTIP (AYUDA VISUAL)
# ═══════════════════════════════════════════════════════════════════
class AyudaVisual:
    """
    Tooltips estilizados que aparecen al pasar el mouse sobre un widget.
    """

    def __init__(self, widget, texto: str):
        self.widget = widget
        self.texto = texto
        self.ventana_ayuda = None
        self.widget.bind("<Enter>", self.mostrar_cartel)
        self.widget.bind("<Leave>", self.ocultar_cartel)

    def mostrar_cartel(self, event=None):
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            x, y = 0, 0

        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25

        self.ventana_ayuda = tk.Toplevel(self.widget)
        self.ventana_ayuda.wm_overrideredirect(True)
        self.ventana_ayuda.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.ventana_ayuda,
            text=self.texto,
            justify="left",
            background="#FFFDE7",
            foreground=COLOR_TEXTO_PRINCIPAL,
            relief="solid",
            borderwidth=1,
            font=FUENTE_TOOLTIP,
            padx=8,
            pady=4,
        )
        label.pack()

    def ocultar_cartel(self, event=None):
        if self.ventana_ayuda:
            self.ventana_ayuda.destroy()
            self.ventana_ayuda = None


# ═══════════════════════════════════════════════════════════════════
# 7. NAVEGACIÓN POR TECLADO
# ═══════════════════════════════════════════════════════════════════
def enfocar_siguiente(event):
    """Permite navegar entre campos con la tecla Enter."""
    event.widget.tk_focusNext().focus()
    return "break"


# ═══════════════════════════════════════════════════════════════════
# 8. UTILIDADES INTERNAS
# ═══════════════════════════════════════════════════════════════════
def _oscurecer_color(hex_color: str, factor: float = 0.85) -> str:
    """Oscurece un color hexadecimal para efecto hover."""
    try:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color
