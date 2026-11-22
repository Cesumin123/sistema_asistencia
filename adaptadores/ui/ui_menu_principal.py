# adaptadores/ui/ui_menu_principal.py
"""
Adaptador de Interfaz de Usuario para el Menú Principal (Dashboard).
Controla la navegación central y aplica la matriz RBAC de dominio/permisos.py
deshabilitando botones de módulos no autorizados.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from typing import Dict, Callable, Optional
from PIL import Image, ImageTk

from dominio.usuario import Usuario
from dominio.permisos import (
    obtener_permisos_rol,
    MODULO_ESTUDIANTES,
    MODULO_ACADEMICO,
    MODULO_ASISTENCIA,
    MODULO_LISTADOS,
    MODULO_REPORTES,
    MODULO_PROMOCION,
    MODULO_USUARIOS
)


def resolver_ruta_recurso(nombre_archivo: str) -> str:
    """Resuelve la ruta absoluta del recurso compatible con desarrollo y PyInstaller."""
    try:
        base = sys._MEIPASS  # type: ignore
    except Exception:
        base = os.path.abspath(os.path.dirname(__file__))
        # Intentar buscar en raíz del proyecto
        raiz = os.path.abspath(os.path.join(base, "..", ".."))
        if os.path.exists(os.path.join(raiz, nombre_archivo)):
            return os.path.join(raiz, nombre_archivo)

    return os.path.join(base, nombre_archivo)


class MenuPrincipalUI:
    """
    Panel de Control Principal del Complejo Educativo Colinas del Llano.
    """

    def __init__(
        self,
        usuario: Usuario,
        callbacks: Dict[str, Callable[[], None]],
        on_logout: Optional[Callable[[], None]] = None,
        root: Optional[tk.Tk] = None
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

        self.root.title("Panel de Control - Complejo Educativo Colinas del Llano")
        self.root.geometry("1000x600")
        self.root.resizable(False, False)
        self.root.config(bg="#f4f6f7")

        self._centrar_ventana(1000, 600)
        self.logo_tk = None  # Mantener referencia viva de imagen

        self._crear_interfaz()

    def _centrar_ventana(self, ancho: int, alto: int):
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = max(0, int((sw - ancho) / 2))
            y = max(0, int((sh - alto) / 2))
            self.root.geometry(f"{ancho}x{alto}+{x}+{y}")
        except Exception:
            pass

    def _crear_interfaz(self):
        """Distribuye el panel izquierdo (Logo) y el panel derecho (Botones con RBAC)."""
        # ====================================================================
        # 1. PANEL IZQUIERDO (Blanco con Logo Institucional Defensivo)
        # ====================================================================
        frame_izq = tk.Frame(self.root, bg="white", width=380)
        frame_izq.pack(side="left", fill="both", expand=True)

        self._cargar_logo_defensivo(frame_izq)

        # ====================================================================
        # 2. PANEL DERECHO (Encabezado de Sesión y Módulos RBAC)
        # ====================================================================
        frame_der = tk.Frame(self.root, bg="#f4f6f7", padx=30, pady=15)
        frame_der.pack(side="right", fill="both", expand=True)

        # Encabezado del Sistema y Usuario Activo
        tk.Label(
            frame_der,
            text="PANEL DE CONTROL CENTRAL",
            font=("Arial", 16, "bold"),
            bg="#f4f6f7",
            fg="#2c3e50"
        ).pack(anchor="w", pady=(5, 2))

        nombre_mostrar = self.usuario.nombre_completo or self.usuario.username
        info_usuario = f"👤 Usuario: {nombre_mostrar}   |   Rol: {self.usuario.rol}"
        
        color_badge = "#27ae60" if self.usuario.rol == "ADMIN" else ("#2980b9" if self.usuario.rol == "ASISTENTE" else "#e67e22")
        lbl_user = tk.Label(
            frame_der,
            text=info_usuario,
            font=("Arial", 10, "bold"),
            bg="#f4f6f7",
            fg=color_badge
        )
        lbl_user.pack(anchor="w", pady=(0, 15))

        # Obtener matriz de permisos del rol
        permisos = obtener_permisos_rol(self.usuario.rol)

        # Contenedor de Botones
        f_botones = tk.Frame(frame_der, bg="#f4f6f7")
        f_botones.pack(fill="both", expand=True)

        # 1. Gestión Académica (Profesores y Clases) -> MODULO_ACADEMICO
        self._agregar_boton_modulo(
            f_botones,
            texto="🎓 Gestión Académica (Profesores y Clases)",
            modulo=MODULO_ACADEMICO,
            color_bg="#f39c12",
            color_fg="white",
            autorizado=permisos.get(MODULO_ACADEMICO, False),
            comando=self.callbacks.get(MODULO_ACADEMICO)
        )

        # 2. Gestión de Estudiantes -> MODULO_ESTUDIANTES
        self._agregar_boton_modulo(
            f_botones,
            texto="👤 Oficina de Inscripciones (Estudiantes)",
            modulo=MODULO_ESTUDIANTES,
            color_bg="#2980b9",
            color_fg="white",
            autorizado=permisos.get(MODULO_ESTUDIANTES, False),
            comando=self.callbacks.get(MODULO_ESTUDIANTES)
        )

        # 3. Pasar Asistencia -> MODULO_ASISTENCIA
        self._agregar_boton_modulo(
            f_botones,
            texto="📋 Pasar Lista de Asistencia (Núcleo)",
            modulo=MODULO_ASISTENCIA,
            color_bg="#27ae60",
            color_fg="white",
            autorizado=permisos.get(MODULO_ASISTENCIA, False),
            comando=self.callbacks.get(MODULO_ASISTENCIA)
        )

        # 4. Listados Generales -> MODULO_LISTADOS
        self._agregar_boton_modulo(
            f_botones,
            texto="📑 Listados Generales y Consolidados",
            modulo=MODULO_LISTADOS,
            color_bg="#16a085",
            color_fg="white",
            autorizado=permisos.get(MODULO_LISTADOS, False),
            comando=self.callbacks.get(MODULO_LISTADOS)
        )

        # 5. Reportes y Estadísticas -> MODULO_REPORTES
        self._agregar_boton_modulo(
            f_botones,
            texto="📊 Módulo de Reportes y Estadísticas (PDF)",
            modulo=MODULO_REPORTES,
            color_bg="#8e44ad",
            color_fg="white",
            autorizado=permisos.get(MODULO_REPORTES, False),
            comando=self.callbacks.get(MODULO_REPORTES)
        )

        # 6. Cierre y Promoción Anual -> MODULO_PROMOCION
        self._agregar_boton_modulo(
            f_botones,
            texto="⚠️ Cierre y Promoción de Año Escolar",
            modulo=MODULO_PROMOCION,
            color_bg="#d35400",
            color_fg="white",
            autorizado=permisos.get(MODULO_PROMOCION, False),
            comando=self.callbacks.get(MODULO_PROMOCION)
        )

        # 7. Gestión de Usuarios y Seguridad -> MODULO_USUARIOS
        self._agregar_boton_modulo(
            f_botones,
            texto="⚙️ Panel de Seguridad (Gestión de Usuarios)",
            modulo=MODULO_USUARIOS,
            color_bg="#2c3e50",
            color_fg="white",
            autorizado=permisos.get(MODULO_USUARIOS, False),
            comando=self.callbacks.get(MODULO_USUARIOS)
        )

        # Botón Cerrar Sesión
        tk.Button(
            frame_der,
            text="🚪 Cerrar Sesión",
            font=("Arial", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            cursor="hand2",
            relief="flat",
            command=self.cerrar_sesion
        ).pack(anchor="e", pady=(10, 0))

    def _cargar_logo_defensivo(self, contenedor: tk.Frame):
        """Carga defensiva con Pillow de la imagen institucional (escalada a 300x300 px)."""
        nombres_posibles = ["logo_colegio.png", "LOGOLICEO.png", "logo.png"]
        ruta_encontrada = None

        for nom in nombres_posibles:
            ruta = resolver_ruta_recurso(nom)
            if os.path.exists(ruta):
                ruta_encontrada = ruta
                break

        if ruta_encontrada:
            try:
                img_orig = Image.open(ruta_encontrada)
                img_redim = img_orig.resize((300, 300), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img_redim)

                lbl_img = tk.Label(contenedor, image=self.logo_tk, bg="white")
                lbl_img.pack(expand=True)
                return
            except Exception:
                pass

        # Fallback defensivo si la imagen no existe o Pillow falla
        f_rotulo = tk.Frame(contenedor, bg="white")
        f_rotulo.pack(expand=True)
        tk.Label(
            f_rotulo,
            text="COMPLEJO EDUCATIVO\n'COLINAS DEL LLANO'",
            font=("Arial", 14, "bold"),
            fg="#2c3e50",
            bg="white",
            justify="center"
        ).pack(pady=10)
        tk.Label(
            f_rotulo,
            text="[ Escudo Institucional ]",
            font=("Arial", 10, "italic"),
            fg="#95a5a6",
            bg="white"
        ).pack()

    def _agregar_boton_modulo(
        self,
        contenedor: tk.Frame,
        texto: str,
        modulo: str,
        color_bg: str,
        color_fg: str,
        autorizado: bool,
        comando: Optional[Callable[[], None]]
    ):
        """Crea un botón aplicando el estado habilitado/deshabilitado según la autorización RBAC."""
        if autorizado:
            estado = "normal"
            bg = color_bg
            cursor = "hand2"
        else:
            estado = "disabled"
            bg = "#bdc3c7"
            cursor = "arrow"

        btn = tk.Button(
            contenedor,
            text=texto,
            font=("Arial", 10, "bold"),
            bg=bg,
            fg=color_fg,
            state=estado,
            cursor=cursor,
            relief="flat",
            command=comando if autorizado else None
        )
        btn.pack(fill="x", pady=3)

    def cerrar_sesion(self):
        """Cierra el panel de control y regresa al login si existe callback."""
        self.root.destroy()
        if self.on_logout:
            self.on_logout()


# Alias para compatibilidad
MenuPrincipal = MenuPrincipalUI
