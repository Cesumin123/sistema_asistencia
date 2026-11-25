# adaptadores/ui/ui_menu_principal.py
"""
Adaptador de Interfaz de Usuario para el Menú Principal (Dashboard).
Dashboard profesional con panel lateral institucional, encabezado con
usuario/rol activo, tarjetas de módulos con RBAC y botón de Cerrar Sesión.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Dict, Callable, Optional
from PIL import Image, ImageTk

from rutas_app import obtener_ruta_recurso
from dominio.usuario import Usuario
from dominio.permisos import (
    obtener_permisos_rol,
    MODULO_ESTUDIANTES, MODULO_ACADEMICO, MODULO_ASISTENCIA,
    MODULO_LISTADOS, MODULO_REPORTES, MODULO_ESTADISTICAS,
    MODULO_PROMOCION, MODULO_USUARIOS,
)
from adaptadores.ui.utilidades_ui import (
    aplicar_tema_global, centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_SIDEBAR,
    COLOR_SIDEBAR_HEADER, COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_CLARO, COLOR_SEPARADOR, COLOR_BORDE_TARJETA,
    COLOR_ACENTO, COLOR_PELIGRO, COLOR_ADVERTENCIA, COLOR_SECUNDARIO,
    COLOR_BADGE_ADMIN, COLOR_BADGE_ASISTENTE, COLOR_BADGE_DOCENTE,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_BOTON,
    FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD,
    crear_boton, crear_tarjeta, crear_separador,
)


def resolver_ruta_recurso(nombre_archivo: str) -> str:
    """Resuelve la ruta absoluta del recurso compatible con desarrollo y PyInstaller."""
    return obtener_ruta_recurso(nombre_archivo)


# Configuración de módulos para el dashboard
MODULOS_CONFIG = [
    {
        "id": MODULO_ACADEMICO,
        "icono": "🎓",
        "titulo": "Gestión Académica",
        "desc": "Profesores y Clases",
        "color": COLOR_ADVERTENCIA,
    },
    {
        "id": MODULO_ESTUDIANTES,
        "icono": "👤",
        "titulo": "Inscripciones",
        "desc": "Gestión de Estudiantes",
        "color": COLOR_SECUNDARIO,
    },
    {
        "id": MODULO_ASISTENCIA,
        "icono": "📋",
        "titulo": "Pasar Lista",
        "desc": "Asistencia Diaria",
        "color": COLOR_ACENTO,
    },
    {
        "id": MODULO_LISTADOS,
        "icono": "📑",
        "titulo": "Listados",
        "desc": "Consolidados Generales",
        "color": "#16A085",
    },
    {
        "id": MODULO_REPORTES,
        "icono": "📊",
        "titulo": "Reportes",
        "desc": "Estadísticas y PDF",
        "color": "#8E44AD",
    },
    {
        "id": MODULO_ESTADISTICAS,
        "icono": "📈",
        "titulo": "Estadísticas",
        "desc": "Indicadores y Gráficos",
        "color": "#2E86C1",
    },
    {
        "id": MODULO_PROMOCION,
        "icono": "⚠️",
        "titulo": "Promoción Anual",
        "desc": "Cierre de Año Escolar",
        "color": "#D35400",
    },
    {
        "id": MODULO_USUARIOS,
        "icono": "⚙️",
        "titulo": "Seguridad",
        "desc": "Gestión de Usuarios",
        "color": COLOR_PRIMARIO,
    },
]


class MenuPrincipalUI:
    """Panel de Control Principal del Complejo Educativo Colinas del Llano."""

    def __init__(
        self,
        usuario: Usuario,
        callbacks: Dict[str, Callable[[], None]],
        on_logout: Optional[Callable[[], None]] = None,
        root: Optional[tk.Tk] = None,
    ):
        self.usuario = usuario
        self.callbacks = callbacks
        self.on_logout = on_logout

        if root is None:
            self.root = tk.Tk()
            self._root_propio = True
        else:
            self.root = root
            self._root_propio = False

        aplicar_tema_global(self.root)
        self.root.title("Panel de Control — Complejo Educativo Colinas del Llano")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 1050, 650)
        maximizar_ventana(self.root)

        self.logo_tk = None
        self._crear_interfaz()

    # ──────────────────────────────────────────────────────────
    def _crear_interfaz(self):
        """Distribuye sidebar izquierdo y panel de módulos derecho."""
        # ═══ SIDEBAR IZQUIERDO ═══
        sidebar = tk.Frame(self.root, bg=COLOR_SIDEBAR, width=280)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo institucional
        self._cargar_logo_defensivo(sidebar)

        # Nombre del colegio
        tk.Label(
            sidebar, text="COMPLEJO EDUCATIVO", font=FUENTE_CUERPO_BOLD,
            fg=COLOR_TEXTO_CLARO, bg=COLOR_SIDEBAR,
        ).pack(pady=(10, 0))
        tk.Label(
            sidebar, text="'Colinas del Llano'", font=FUENTE_PEQUEÑA,
            fg="#D5D8DC", bg=COLOR_SIDEBAR,
        ).pack()

        crear_separador(sidebar).pack(fill="x", padx=30, pady=15)

        # Info del usuario activo
        nombre_mostrar = self.usuario.nombre_completo or self.usuario.username
        color_badge = {
            "ADMIN": COLOR_BADGE_ADMIN,
            "ASISTENTE": COLOR_BADGE_ASISTENTE,
        }.get(self.usuario.rol, COLOR_BADGE_DOCENTE)

        tk.Label(
            sidebar, text=f"👤  {nombre_mostrar}", font=FUENTE_CUERPO_BOLD,
            fg=COLOR_TEXTO_CLARO, bg=COLOR_SIDEBAR, wraplength=240,
        ).pack(padx=20, anchor="w")

        # Badge del rol
        f_badge = tk.Frame(sidebar, bg=COLOR_SIDEBAR)
        f_badge.pack(padx=20, anchor="w", pady=(4, 0))
        tk.Label(
            f_badge, text=f"  {self.usuario.rol}  ", font=FUENTE_PEQUEÑA_BOLD,
            fg=COLOR_TEXTO_CLARO, bg=color_badge,
        ).pack(side="left")

        # Spacer flexible
        tk.Frame(sidebar, bg=COLOR_SIDEBAR).pack(expand=True, fill="both")

        # Botón Cerrar Sesión (anclado abajo)
        crear_boton(
            sidebar, texto="🚪  Cerrar Sesión", comando=self.cerrar_sesion,
            color_bg="#95A5A6", color_hover="#7F8C8D",
        ).pack(fill="x", padx=20, pady=(0, 20), ipady=4)

        # ═══ PANEL PRINCIPAL DERECHO ═══
        panel_principal = tk.Frame(self.root, bg=COLOR_FONDO_APP, padx=30, pady=20)
        panel_principal.pack(side="right", fill="both", expand=True)

        # Encabezado
        tk.Label(
            panel_principal, text="PANEL DE CONTROL",
            font=FUENTE_TITULO, bg=COLOR_FONDO_APP, fg=COLOR_TEXTO_PRINCIPAL,
        ).pack(anchor="w", pady=(5, 2))
        tk.Label(
            panel_principal,
            text="Seleccione un módulo para comenzar a trabajar",
            font=FUENTE_PEQUEÑA, bg=COLOR_FONDO_APP, fg=COLOR_TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(0, 20))

        # Grid de tarjetas de módulos
        permisos = obtener_permisos_rol(self.usuario.rol)
        frame_grid = tk.Frame(panel_principal, bg=COLOR_FONDO_APP)
        frame_grid.pack(fill="both", expand=True)

        # Configurar columnas con peso uniforme
        frame_grid.columnconfigure(0, weight=1)
        frame_grid.columnconfigure(1, weight=1)

        for idx, modulo in enumerate(MODULOS_CONFIG):
            fila = idx // 2
            columna = idx % 2
            autorizado = permisos.get(modulo["id"], False)
            callback = self.callbacks.get(modulo["id"])

            self._crear_tarjeta_modulo(
                frame_grid, modulo, autorizado, callback, fila, columna,
            )

    def _crear_tarjeta_modulo(self, parent, modulo: dict, autorizado: bool,
                               callback, fila: int, columna: int):
        """Crea una tarjeta de módulo con icono, título y descripción."""
        tarjeta = tk.Frame(
            parent, bg=COLOR_TARJETA,
            highlightbackground=COLOR_BORDE_TARJETA if autorizado else "#E8E8E8",
            highlightthickness=1,
            padx=16, pady=14,
            cursor="hand2" if autorizado else "arrow",
        )
        tarjeta.grid(row=fila, column=columna, padx=6, pady=6, sticky="nsew")

        # Banda de color lateral
        banda = tk.Frame(tarjeta, bg=modulo["color"] if autorizado else "#BDC3C7", width=4)
        banda.pack(side="left", fill="y", padx=(0, 12))

        # Contenido
        f_contenido = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_contenido.pack(side="left", fill="both", expand=True)

        fg_titulo = COLOR_TEXTO_PRINCIPAL if autorizado else "#BDC3C7"
        fg_desc = COLOR_TEXTO_SECUNDARIO if autorizado else "#D5D8DC"

        tk.Label(
            f_contenido, text=f"{modulo['icono']}  {modulo['titulo']}",
            font=FUENTE_CUERPO_BOLD, bg=COLOR_TARJETA, fg=fg_titulo, anchor="w",
        ).pack(fill="x")
        tk.Label(
            f_contenido, text=modulo["desc"],
            font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=fg_desc, anchor="w",
        ).pack(fill="x")

        if not autorizado:
            tk.Label(
                f_contenido, text="🔒 Sin acceso",
                font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg="#BDC3C7", anchor="w",
            ).pack(fill="x")

        if autorizado and callback:
            for widget in [tarjeta, banda, f_contenido] + f_contenido.winfo_children():
                widget.bind("<Button-1>", lambda e, cb=callback: cb())
                widget.bind("<Enter>", lambda e, t=tarjeta: t.config(highlightbackground=modulo["color"]))
                widget.bind("<Leave>", lambda e, t=tarjeta: t.config(highlightbackground=COLOR_BORDE_TARJETA))

    def _cargar_logo_defensivo(self, contenedor: tk.Frame):
        """Carga defensiva de la imagen institucional."""
        nombres_posibles = ["LOGOLICEO.png", "logo_colegio.png", "logo.png"]
        ruta_encontrada = None
        for nom in nombres_posibles:
            ruta = resolver_ruta_recurso(nom)
            if os.path.exists(ruta):
                ruta_encontrada = ruta
                break

        if ruta_encontrada:
            try:
                img_orig = Image.open(ruta_encontrada)
                # Redimensionar proporcionalmente a max 160px
                ratio = min(160 / img_orig.width, 160 / img_orig.height)
                nuevo_w = int(img_orig.width * ratio)
                nuevo_h = int(img_orig.height * ratio)
                img_redim = img_orig.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img_redim)
                tk.Label(
                    contenedor, image=self.logo_tk, bg=COLOR_SIDEBAR,
                ).pack(pady=(25, 0))
                return
            except Exception:
                pass

        # Fallback textual
        tk.Label(
            contenedor, text="🏫", font=(FUENTE_CUERPO[0], 40),
            fg=COLOR_TEXTO_CLARO, bg=COLOR_SIDEBAR,
        ).pack(pady=(30, 0))

    def cerrar_sesion(self):
        """Cierra el panel de control y regresa al login."""
        self.root.destroy()
        if self.on_logout:
            self.on_logout()


# Alias para compatibilidad
MenuPrincipal = MenuPrincipalUI
