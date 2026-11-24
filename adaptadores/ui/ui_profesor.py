# adaptadores/ui/ui_profesor.py
"""
Adaptador de Interfaz de Usuario (UI) para la entidad Profesor.
Tarjeta limpia centrada con logo institucional proporcional,
estilo unificado del sistema de diseño.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from PIL import Image, ImageTk

from dominio.profesor import Profesor
from adaptadores.ui.utilidades_ui import (
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_CLARO, COLOR_SEPARADOR, COLOR_BORDE_TARJETA,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_BOTON,
    crear_boton, crear_tarjeta, crear_separador, maximizar_ventana,
    AyudaVisual, enfocar_siguiente,
)


def resolver_ruta_logo() -> str | None:
    """Busca el archivo de imagen institucional en la raíz o empaquetado."""
    nombres = ["LOGOLICEO.png", "logo_colegio.png", "logo.png"]
    for n in nombres:
        if os.path.exists(n):
            return n
    try:
        base_meipass = sys._MEIPASS  # type: ignore
        for n in nombres:
            p = os.path.join(base_meipass, n)
            if os.path.exists(p):
                return p
    except Exception:
        pass
    dir_actual = os.path.abspath(os.path.dirname(__file__))
    dir_raiz = os.path.abspath(os.path.join(dir_actual, "..", ".."))
    for n in nombres:
        p = os.path.join(dir_raiz, n)
        if os.path.exists(p):
            return p
    return None


class GestorProfesoresUI:
    """Adaptador de Interfaz de Usuario para el registro y gestión de Profesores."""

    def __init__(self, parent_notebook: ttk.Notebook, repositorio_profesor):
        self.notebook = parent_notebook
        self.repositorio = repositorio_profesor
        self.img_logo_tk = None
        self.crear_tab()
        maximizar_ventana(self.notebook.master)

    def convertir_mayus(self, event):
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.icursor(pos)

    def crear_tab(self):
        """Construye la pestaña con tarjeta blanca centrada."""
        tab = tk.Frame(self.notebook, bg=COLOR_FONDO_APP)
        self.notebook.add(tab, text="  👨‍🏫  REGISTRAR PROFESOR  ")

        frame_centro = tk.Frame(tab, bg=COLOR_FONDO_APP)
        frame_centro.pack(expand=True, fill="both", pady=30, padx=20)

        tarjeta = crear_tarjeta(frame_centro, padx=40, pady=30)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        # ── ENCABEZADO INSTITUCIONAL ──
        f_header = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_header.pack(fill="x", pady=(0, 20))

        ruta_logo = resolver_ruta_logo()
        if ruta_logo:
            try:
                img_orig = Image.open(ruta_logo)
                ratio = min(100 / img_orig.width, 100 / img_orig.height)
                nuevo_w = int(img_orig.width * ratio)
                nuevo_h = int(img_orig.height * ratio)
                img_redim = img_orig.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
                self.img_logo_tk = ImageTk.PhotoImage(img_redim)
                tk.Label(f_header, image=self.img_logo_tk, bg=COLOR_TARJETA).pack(side="left", padx=(0, 20))
            except Exception:
                pass

        f_titulos = tk.Frame(f_header, bg=COLOR_TARJETA)
        f_titulos.pack(side="left", fill="y", expand=True)
        tk.Label(f_titulos, text="REGISTRO DE PROFESORES", font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(anchor="w")
        tk.Label(f_titulos, text="Complejo Educativo 'Colinas del Llano'", font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SECUNDARIO).pack(anchor="w", pady=(2, 0))
        tk.Label(f_titulos, text="Ingrese la cédula y nombre completo del docente.", font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SECUNDARIO).pack(anchor="w", pady=(4, 0))

        crear_separador(tarjeta).pack(fill="x", pady=(5, 20))

        # ── FORMULARIO ──
        f_form = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_form.pack(fill="x")

        tk.Label(f_form, text="Cédula de Identidad:", bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA).pack(anchor="w", pady=(0, 4))
        f_ced = tk.Frame(f_form, bg=COLOR_TARJETA)
        f_ced.pack(anchor="w", pady=(0, 15))

        self.combo_nac_prof = ttk.Combobox(f_ced, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac_prof.pack(side="left")
        self.combo_nac_prof.current(0)
        self.combo_nac_prof.bind("<Return>", enfocar_siguiente)

        self.entry_ced_prof = tk.Entry(f_ced, width=18, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_ced_prof.pack(side="left", padx=(8, 0))
        self.entry_ced_prof.bind("<Return>", enfocar_siguiente)
        self.entry_ced_prof.focus()
        AyudaVisual(self.entry_ced_prof, "Solo números sin puntos. Ej: 12345678")

        tk.Label(f_form, text="Nombre Completo del Profesor:", bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA).pack(anchor="w", pady=(0, 4))
        self.entry_nom_prof = tk.Entry(f_form, width=38, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_nom_prof.pack(anchor="w", pady=(0, 25))
        self.entry_nom_prof.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_prof.bind("<Return>", lambda e: self.guardar_click())

        # ── BOTÓN ──
        crear_boton(tarjeta, "💾  GUARDAR PROFESOR", self.guardar_click, COLOR_ACENTO, COLOR_TEXTO_CLARO, COLOR_ACENTO_HOVER).pack(anchor="w")

    def guardar_click(self, event=None):
        nombre = self.entry_nom_prof.get().strip().upper()
        ced_num = self.entry_ced_prof.get().strip()
        cedula = f"{self.combo_nac_prof.get()}-{ced_num}"
        try:
            nuevo = Profesor(cedula=cedula, nombre_completo=nombre)
            nuevo.validar()
            self.repositorio.guardar(nuevo)
            messagebox.showinfo("Éxito", f"Profesor '{nombre}' registrado correctamente.")
            self.entry_ced_prof.delete(0, tk.END)
            self.entry_nom_prof.delete(0, tk.END)
            self.entry_ced_prof.focus()
        except ValueError as e:
            messagebox.showwarning("Dato Inválido", str(e))
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo completar la operación: {e}")
