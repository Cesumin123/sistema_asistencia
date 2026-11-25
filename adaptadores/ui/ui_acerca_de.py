# adaptadores/ui/ui_acerca_de.py
"""
Ventana modal compacta 'Acerca de...' del Sistema de Asistencia Estudiantil.

Muestra información institucional, equipo de desarrollo con fotografía oficial,
contacto técnico (correo y teléfono de soporte), licencia GNU GPLv3, aviso de
confidencialidad LOPNNA, marco normativo y licencias de componentes de terceros.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from PIL import Image, ImageTk

from rutas_app import obtener_ruta_recurso
from dominio.acerca_de import (
    ANIO_PUBLICACION,
    AVISO_CONFIDENCIALIDAD_LOPNNA,
    CONTACTO_TECNICO,
    EQUIPO_DESARROLLADOR,
    INSTITUCION_BENEFICIARIA,
    LICENCIA_NOMBRE,
    NOMBRE_SISTEMA,
    TELEFONO_SOPORTE,
    VERSION_SISTEMA,
    obtener_resumen_legal_y_terceros,
)
from adaptadores.ui.utilidades_ui import (
    AyudaVisual,
    COLOR_BORDE_TARJETA,
    COLOR_FONDO_APP,
    COLOR_PRIMARIO,
    COLOR_PRIMARIO_HOVER,
    COLOR_TARJETA,
    COLOR_TEXTO_PRINCIPAL,
    COLOR_TEXTO_SECUNDARIO,
    FUENTE_CUERPO_BOLD,
    FUENTE_PEQUEÑA,
    FUENTE_PEQUEÑA_BOLD,
    centrar_ventana,
    configurar_ventana_hija,
    crear_boton,
    crear_separador,
    crear_tarjeta,
    restaurar_foco,
)


class ModalAcercaDe:
    """Modal compacto y centrado con créditos, fotografía del equipo y licenciamiento."""

    NOMBRES_FOTO_EQUIPO = (
        "foto_equipo.jpg",
        "foto_equipo.png",
        "foto_equipo.jpeg",
        "nosotros.jpeg",
        "nosotros.jpg",
    )
    ANCHO_MODAL = 540
    ALTO_MODAL = 620

    def __init__(
        self,
        parent: Optional[tk.Misc] = None,
        on_cerrar: Optional[Callable[[], None]] = None,
    ):
        self.parent = parent
        self.on_cerrar = on_cerrar
        self._logo_tk: Optional[ImageTk.PhotoImage] = None
        self._foto_equipo_tk: Optional[ImageTk.PhotoImage] = None
        self.lbl_logo: Optional[tk.Label] = None
        self.lbl_foto: Optional[tk.Label] = None
        self.f_foto_container: Optional[tk.Frame] = None
        self.txt_licencias: Optional[tk.Text] = None
        self.scroll_licencias: Optional[ttk.Scrollbar] = None
        self.btn_cerrar: Optional[tk.Button] = None

        self.win = tk.Toplevel(parent)
        self.win.title("Acerca de — Sistema de Asistencia Estudiantil")
        self.win.resizable(False, False)
        self.win.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.win, self.ANCHO_MODAL, self.ALTO_MODAL)
        configurar_ventana_hija(self.win, parent, es_modal=True)

        try:
            self.win.grab_set()
        except Exception:
            pass

        self.win.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.win.bind("<Escape>", self.cerrar)

        self._construir_contenido()
        self.win.focus_set()

    def esta_abierto(self) -> bool:
        """Indica si la ventana modal sigue viva en Tkinter."""
        try:
            return bool(self.win and self.win.winfo_exists())
        except Exception:
            return False

    def enfocar(self):
        """Eleva y enfoca la ventana modal existente."""
        if self.esta_abierto():
            try:
                self.win.lift()
                self.win.focus_set()
            except Exception:
                pass

    def _construir_contenido(self):
        """Construye la interfaz compacta del modal Acerca de."""
        tarjeta = crear_tarjeta(self.win, padx=14, pady=10)
        tarjeta.pack(expand=True, fill="both", padx=12, pady=10)

        # 1. Cabecera con escudo institucional y título
        f_header = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_header.pack(fill="x", pady=(0, 4))

        self._cargar_logo_institucional(f_header)

        f_titulos = tk.Frame(f_header, bg=COLOR_TARJETA)
        f_titulos.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(
            f_titulos,
            text=NOMBRE_SISTEMA,
            font=FUENTE_CUERPO_BOLD,
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO,
            anchor="w",
            justify="left",
            wraplength=405,
        ).pack(fill="x")

        tk.Label(
            f_titulos,
            text=f"Versión {VERSION_SISTEMA}  •  {INSTITUCION_BENEFICIARIA}",
            font=FUENTE_PEQUEÑA,
            bg=COLOR_TARJETA,
            fg=COLOR_TEXTO_SECUNDARIO,
            anchor="w",
            justify="left",
            wraplength=405,
        ).pack(fill="x", pady=(1, 0))

        crear_separador(tarjeta).pack(fill="x", pady=4)

        # 2. Sección Equipo de Desarrollo + Fotografía
        tk.Label(
            tarjeta,
            text="EQUIPO DE DESARROLLO",
            font=FUENTE_PEQUEÑA_BOLD,
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO,
            anchor="w",
        ).pack(fill="x")

        f_centro_foto = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_centro_foto.pack(fill="x", pady=(3, 4))

        self.f_foto_container = tk.Frame(
            f_centro_foto,
            width=210,
            height=124,
            bg=COLOR_FONDO_APP,
            highlightbackground=COLOR_BORDE_TARJETA,
            highlightthickness=1,
        )
        self.f_foto_container.pack(anchor="center")
        self.f_foto_container.pack_propagate(False)

        self.lbl_foto = tk.Label(
            self.f_foto_container,
            text="[ Fotografía del Equipo ]",
            font=FUENTE_PEQUEÑA,
            bg=COLOR_FONDO_APP,
            fg=COLOR_TEXTO_SECUNDARIO,
        )
        self.lbl_foto.pack(expand=True, fill="both")
        self._cargar_foto_equipo()

        integrantes_texto = "  •  ".join(EQUIPO_DESARROLLADOR[:2]) + "\n" + "  •  ".join(
            EQUIPO_DESARROLLADOR[2:]
        )
        tk.Label(
            tarjeta,
            text=integrantes_texto,
            font=FUENTE_PEQUEÑA_BOLD,
            bg=COLOR_TARJETA,
            fg=COLOR_TEXTO_PRINCIPAL,
            justify="center",
        ).pack(fill="x", pady=(0, 2))

        tk.Label(
            tarjeta,
            text=f"Contacto técnico: {CONTACTO_TECNICO}",
            font=FUENTE_PEQUEÑA,
            bg=COLOR_TARJETA,
            fg=COLOR_TEXTO_SECUNDARIO,
            justify="center",
        ).pack(fill="x")

        tk.Label(
            tarjeta,
            text=f"Teléfono de soporte: {TELEFONO_SOPORTE}",
            font=FUENTE_PEQUEÑA_BOLD,
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO,
            justify="center",
        ).pack(fill="x", pady=(1, 0))

        crear_separador(tarjeta).pack(fill="x", pady=4)

        # 3. Sección Legal y Confidencialidad LOPNNA
        tk.Label(
            tarjeta,
            text=f"© {ANIO_PUBLICACION} Equipo Desarrollador  •  Licencia: {LICENCIA_NOMBRE}",
            font=FUENTE_PEQUEÑA_BOLD,
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO,
            anchor="w",
            justify="left",
            wraplength=480,
        ).pack(fill="x")

        tk.Label(
            tarjeta,
            text=AVISO_CONFIDENCIALIDAD_LOPNNA,
            font=FUENTE_PEQUEÑA,
            bg=COLOR_TARJETA,
            fg=COLOR_TEXTO_SECUNDARIO,
            anchor="w",
            justify="left",
            wraplength=480,
        ).pack(fill="x", pady=(2, 4))

        # 4. Botón Cerrar empaquetado ANTES del tk.Text expandible para garantizar visibilidad
        f_pie = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_pie.pack(side="bottom", fill="x", pady=(6, 0))

        self.btn_cerrar = crear_boton(
            f_pie,
            texto="Cerrar",
            comando=self.cerrar,
            color_bg=COLOR_PRIMARIO,
            color_hover=COLOR_PRIMARIO_HOVER,
            pady=4,
        )
        self.btn_cerrar.pack(side="right")
        AyudaVisual(self.btn_cerrar, "Cerrar ventana (tecla Esc)")

        # 5. Área desplazable de Marco Normativo y Licencias de Terceros (solo lectura)
        f_texto = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_texto.pack(fill="both", expand=True)

        self.txt_licencias = tk.Text(
            f_texto,
            height=8,
            wrap="word",
            font=FUENTE_PEQUEÑA,
            bg=COLOR_FONDO_APP,
            fg=COLOR_TEXTO_PRINCIPAL,
            relief="solid",
            bd=1,
            padx=6,
            pady=4,
        )
        self.scroll_licencias = ttk.Scrollbar(
            f_texto, orient="vertical", command=self.txt_licencias.yview
        )
        self.txt_licencias.configure(yscrollcommand=self.scroll_licencias.set)

        self.scroll_licencias.pack(side="right", fill="y")
        self.txt_licencias.pack(side="left", fill="both", expand=True)

        self.txt_licencias.insert("1.0", obtener_resumen_legal_y_terceros())
        self.txt_licencias.config(state="disabled")

    def _cargar_logo_institucional(self, contenedor: tk.Frame):
        """Carga de forma defensiva el escudo institucional (48x48 px)."""
        ruta_logo = obtener_ruta_recurso("LOGOLICEO.png")
        if os.path.exists(ruta_logo):
            try:
                with Image.open(ruta_logo) as img:
                    img_copia = img.copy()
                img_copia.thumbnail((48, 48), Image.Resampling.LANCZOS)
                self._logo_tk = ImageTk.PhotoImage(img_copia, master=self.win)
                self.lbl_logo = tk.Label(
                    contenedor, image=self._logo_tk, bg=COLOR_TARJETA
                )
                self.lbl_logo.image = self._logo_tk
                self.lbl_logo.pack(side="left")
                return
            except Exception:
                pass

        self.lbl_logo = tk.Label(
            contenedor,
            text="🏫",
            font=(FUENTE_CUERPO_BOLD[0], 22),
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO,
        )
        self.lbl_logo.pack(side="left")

    def _cargar_foto_equipo(self):
        """Carga y escala proporcionalmente la fotografía del equipo con fallback silencioso."""
        ruta_foto = None
        for nombre in self.NOMBRES_FOTO_EQUIPO:
            candidato = obtener_ruta_recurso(nombre)
            if os.path.exists(candidato):
                ruta_foto = candidato
                break

        if not ruta_foto or self.lbl_foto is None:
            return

        try:
            with Image.open(ruta_foto) as img:
                img_rgb = img.convert("RGB")
            img_rgb.thumbnail((206, 120), Image.Resampling.LANCZOS)
            self._foto_equipo_tk = ImageTk.PhotoImage(img_rgb, master=self.win)
            self.lbl_foto.config(image=self._foto_equipo_tk, text="")
            self.lbl_foto.image = self._foto_equipo_tk
        except Exception:
            self._foto_equipo_tk = None

    def cerrar(self, _event=None):
        """Libera referencias gráficas, destruye el modal y restaura el foco."""
        try:
            if self.win.winfo_exists():
                self.win.grab_release()
        except Exception:
            pass

        self._logo_tk = None
        self._foto_equipo_tk = None
        if self.lbl_logo is not None:
            try:
                self.lbl_logo.image = None
            except Exception:
                pass
        if self.lbl_foto is not None:
            try:
                self.lbl_foto.image = None
            except Exception:
                pass

        try:
            if self.win and self.win.winfo_exists():
                self.win.destroy()
        finally:
            if self.on_cerrar:
                self.on_cerrar()
            restaurar_foco(self.parent)
