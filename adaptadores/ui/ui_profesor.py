# adaptadores/ui/ui_profesor.py
"""
Adaptador de Interfaz de Usuario (UI) para la entidad Profesor.
Presenta una tarjeta limpia, profesional y centrada con el logo institucional
redimensionado proporcionalmente sin superposiciones ni fondos discordantes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from PIL import Image, ImageTk

from dominio.profesor import Profesor
from adaptadores.ui.utilidades_ui import AyudaVisual, enfocar_siguiente


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
    """
    Adaptador de Interfaz de Usuario para el registro y gestión de Profesores.
    """

    def __init__(self, parent_notebook: ttk.Notebook, repositorio_profesor):
        self.notebook = parent_notebook
        self.repositorio = repositorio_profesor
        self.img_logo_tk = None  # Mantener referencia viva de la imagen

        # Construcción visual
        self.crear_tab()

        # Maximizado multiplataforma seguro
        try:
            self.notebook.master.state('zoomed')
        except Exception:
            try:
                self.notebook.master.attributes('-zoomed', True)
            except Exception:
                pass

    def convertir_mayus(self, event):
        """Convierte automáticamente a mayúsculas mientras el usuario escribe."""
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.icursor(pos)

    def crear_tab(self):
        """Construye la pestaña de registro con una tarjeta blanca centrada y paleta uniforme."""
        # Pestaña con fondo claro neutro
        tab = tk.Frame(self.notebook, bg="#f4f6f7")
        self.notebook.add(tab, text="  👨‍🏫  REGISTRAR PROFESOR  ")

        # Contenedor central expandido para centrado vertical y horizontal
        frame_centro = tk.Frame(tab, bg="#f4f6f7")
        frame_centro.pack(expand=True, fill="both", pady=30, padx=20)

        # Tarjeta blanca central bien delimitada
        tarjeta = tk.Frame(frame_centro, bg="white", padx=40, pady=30, relief="solid", bd=1)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        # -------------------------------------------------------------
        # ENCABEZADO INSTITUCIONAL: LOGO REDIMENSIONADO Y TÍTULOS
        # -------------------------------------------------------------
        f_header = tk.Frame(tarjeta, bg="white")
        f_header.pack(fill="x", pady=(0, 20))

        # Carga del logo de forma proporcional (100x100 px) sin recortes
        ruta_logo = resolver_ruta_logo()
        if ruta_logo:
            try:
                img_orig = Image.open(ruta_logo)
                img_redim = img_orig.resize((100, 100), Image.Resampling.LANCZOS)
                self.img_logo_tk = ImageTk.PhotoImage(img_redim)
                lbl_logo = tk.Label(f_header, image=self.img_logo_tk, bg="white")
                lbl_logo.pack(side="left", padx=(0, 20))
            except Exception as e:
                print(f"Aviso: No se pudo cargar el logo del liceo: {e}")

        f_titulos = tk.Frame(f_header, bg="white")
        f_titulos.pack(side="left", fill="y", expand=True)

        tk.Label(
            f_titulos,
            text="REGISTRO DE PROFESORES",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(anchor="w")

        tk.Label(
            f_titulos,
            text="Complejo Educativo 'Colinas del Llano'",
            font=("Arial", 10, "italic"),
            bg="white",
            fg="#7f8c8d"
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            f_titulos,
            text="Ingrese la cédula y nombre completo del docente para habilitar asignaciones.",
            font=("Arial", 9),
            bg="white",
            fg="#95a5a6"
        ).pack(anchor="w", pady=(4, 0))

        # Línea separadora sutil
        sep = tk.Frame(tarjeta, bg="#e5e7e9", height=1)
        sep.pack(fill="x", pady=(5, 20))

        # -------------------------------------------------------------
        # FORMULARIO DE ENTRADA
        # -------------------------------------------------------------
        f_form = tk.Frame(tarjeta, bg="white")
        f_form.pack(fill="x")

        # 1. Cédula de Identidad
        tk.Label(
            f_form,
            text="Cédula de Identidad:",
            bg="white",
            fg="#34495e",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 4))

        f_ced = tk.Frame(f_form, bg="white")
        f_ced.pack(anchor="w", pady=(0, 15))

        self.combo_nac_prof = ttk.Combobox(f_ced, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac_prof.pack(side="left")
        self.combo_nac_prof.current(0)
        AyudaVisual(self.combo_nac_prof, "Seleccione la nacionalidad del profesor.")
        self.combo_nac_prof.bind("<Return>", enfocar_siguiente)

        self.entry_ced_prof = tk.Entry(f_ced, width=18, font=("Arial", 10))
        self.entry_ced_prof.pack(side="left", padx=(8, 0))
        self.entry_ced_prof.bind("<Return>", enfocar_siguiente)
        self.entry_ced_prof.focus()
        AyudaVisual(self.entry_ced_prof, "Ingrese solo números sin puntos. Ej: 12345678")

        # 2. Nombre Completo
        tk.Label(
            f_form,
            text="Nombre Completo del Profesor:",
            bg="white",
            fg="#34495e",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 4))

        self.entry_nom_prof = tk.Entry(f_form, width=38, font=("Arial", 10))
        self.entry_nom_prof.pack(anchor="w", pady=(0, 25))
        self.entry_nom_prof.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_prof.bind("<Return>", lambda e: self.guardar_click())
        AyudaVisual(self.entry_nom_prof, "Nombre y apellido del docente.")

        # -------------------------------------------------------------
        # BOTÓN DE ACCIÓN
        # -------------------------------------------------------------
        btn_guardar = tk.Button(
            tarjeta,
            text="💾 GUARDAR PROFESOR",
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8,
            relief="flat",
            command=self.guardar_click
        )
        btn_guardar.pack(anchor="w")
        AyudaVisual(btn_guardar, "Haz clic para registrar el profesor en el sistema.")

    def guardar_click(self, event=None):
        """Valida y guarda el profesor en la persistencia."""
        nombre = self.entry_nom_prof.get().strip().upper()
        ced_num = self.entry_ced_prof.get().strip()
        cedula = f"{self.combo_nac_prof.get()}-{ced_num}"

        try:
            nuevo_profesor = Profesor(cedula=cedula, nombre_completo=nombre)
            nuevo_profesor.validar()

            self.repositorio.guardar(nuevo_profesor)
            messagebox.showinfo("Éxito", f"Profesor '{nombre}' registrado correctamente.")

            self.entry_ced_prof.delete(0, tk.END)
            self.entry_nom_prof.delete(0, tk.END)
            self.entry_ced_prof.focus()

        except ValueError as e:
            messagebox.showwarning("Dato Inválido", str(e))
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo completar la operación: {e}")
