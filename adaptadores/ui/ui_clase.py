# adaptadores/ui/ui_clase.py
"""
Adaptador de Interfaz de Usuario (UI) para la entidad Clase (Materias).
Presenta una tarjeta limpia y profesional coherente con el módulo de Profesores,
con fondo claro neutro y formulario alineado.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from dominio.clase import Clase
from adaptadores.ui.utilidades_ui import AyudaVisual, enfocar_siguiente


class GestorClasesUI:
    """
    Adaptador de Interfaz de Usuario para la asignación y registro de Materias/Clases.
    """

    def __init__(self, parent_notebook: ttk.Notebook, repositorio_clase):
        self.notebook = parent_notebook
        self.repositorio = repositorio_clase
        self.mapa_secciones = {}
        self.crear_tab()
        self.cargar_datos_en_listas()

    def convertir_mayus(self, event):
        """Convierte automáticamente a mayúsculas mientras se escribe."""
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.icursor(pos)

    def crear_tab(self):
        """Construye la pestaña de asignación de materias con una tarjeta blanca centrada."""
        # Fondo claro neutro
        tab = tk.Frame(self.notebook, bg="#f4f6f7")
        self.notebook.add(tab, text="  📚  ASIGNAR MATERIAS  ")

        # Contenedor para centrado
        frame_centro = tk.Frame(tab, bg="#f4f6f7")
        frame_centro.pack(expand=True, fill="both", pady=25, padx=20)

        # Tarjeta blanca central
        tarjeta = tk.Frame(frame_centro, bg="white", padx=40, pady=25, relief="solid", bd=1)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        # -------------------------------------------------------------
        # ENCABEZADO
        # -------------------------------------------------------------
        tk.Label(
            tarjeta,
            text="ASIGNACIÓN ACADÉMICA DE MATERIAS",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(anchor="w")

        tk.Label(
            tarjeta,
            text="Vincule la materia curricular con el profesor titular, año escolar y secciones.",
            font=("Arial", 9),
            bg="white",
            fg="#7f8c8d"
        ).pack(anchor="w", pady=(2, 15))

        sep = tk.Frame(tarjeta, bg="#e5e7e9", height=1)
        sep.pack(fill="x", pady=(0, 20))

        # -------------------------------------------------------------
        # FORMULARIO CON GRID
        # -------------------------------------------------------------
        f_grid = tk.Frame(tarjeta, bg="white")
        f_grid.pack(fill="x")

        # 1. Nombre de la Materia
        tk.Label(
            f_grid,
            text="Nombre de la Materia:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#34495e"
        ).grid(row=0, column=0, sticky="w", pady=8)

        self.entry_nom_mat = tk.Entry(f_grid, width=32, font=("Arial", 10))
        self.entry_nom_mat.grid(row=0, column=1, sticky="w", padx=(15, 0), pady=8)
        self.entry_nom_mat.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_mat.bind("<Return>", enfocar_siguiente)
        self.entry_nom_mat.focus()
        AyudaVisual(self.entry_nom_mat, "Ej: MATEMÁTICAS, CASTELLANO, QUÍMICA...")

        # 2. Profesor Encargado
        tk.Label(
            f_grid,
            text="Profesor Encargado:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#34495e"
        ).grid(row=1, column=0, sticky="w", pady=8)

        self.combo_prof = ttk.Combobox(f_grid, width=30, state="readonly")
        self.combo_prof.grid(row=1, column=1, sticky="w", padx=(15, 0), pady=8)
        self.combo_prof.bind("<Return>", enfocar_siguiente)
        AyudaVisual(self.combo_prof, "Seleccione el profesor que dictará esta materia.")

        # 3. Año / Grado
        tk.Label(
            f_grid,
            text="Año Escolar / Grado:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#34495e"
        ).grid(row=2, column=0, sticky="w", pady=8)

        self.combo_grado = ttk.Combobox(f_grid, width=30, state="readonly")
        self.combo_grado['values'] = [
            "1 - 1er AÑO", "2 - 2do AÑO", "3 - 3er AÑO", "4 - 4to AÑO", "5 - 5to AÑO"
        ]
        self.combo_grado.grid(row=2, column=1, sticky="w", padx=(15, 0), pady=8)
        self.combo_grado.bind("<Return>", enfocar_siguiente)
        AyudaVisual(self.combo_grado, "Seleccione a qué año pertenece la materia.")

        # 4. Secciones (Selección Múltiple)
        tk.Label(
            f_grid,
            text="Secciones Destino:\n(Puede elegir varias)",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#34495e",
            justify="left"
        ).grid(row=3, column=0, sticky="nw", pady=8)

        f_list = tk.Frame(f_grid, bg="white")
        f_list.grid(row=3, column=1, sticky="w", padx=(15, 0), pady=8)

        self.listbox_secciones = tk.Listbox(
            f_list,
            height=5,
            width=28,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            font=("Arial", 9)
        )
        scroll_sec = ttk.Scrollbar(f_list, orient="vertical", command=self.listbox_secciones.yview)
        self.listbox_secciones.configure(yscrollcommand=scroll_sec.set)

        self.listbox_secciones.pack(side="left")
        scroll_sec.pack(side="right", fill="y")

        secciones_disponibles = [
            "Sección A", "Sección B", "Sección C", "Sección D", "Sección E",
            "Sección F", "Sección G", "Sección H", "Sección I", "Sección J"
        ]
        for seccion in secciones_disponibles:
            self.listbox_secciones.insert(tk.END, seccion)

        AyudaVisual(self.listbox_secciones, "Haga clic en todas las secciones donde se impartirá la materia.")

        # -------------------------------------------------------------
        # BOTÓN DE ACCIÓN
        # -------------------------------------------------------------
        btn_guardar = tk.Button(
            tarjeta,
            text="💾 INSCRIBIR MATERIA",
            bg="#2980b9",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8,
            relief="flat",
            command=self.guardar_click
        )
        btn_guardar.pack(anchor="w", pady=(15, 0))
        AyudaVisual(btn_guardar, "Guarda la materia para todas las secciones seleccionadas.")

    def cargar_datos_en_listas(self):
        """Carga en los menús desplegables los profesores, grados y secciones de la base de datos."""
        profesores = self.repositorio.obtener_profesores_activos()
        self.combo_prof['values'] = [f"{p[0]} - {p[1]}" for p in profesores]

        grados = self.repositorio.obtener_grados()
        self.combo_grado['values'] = [f"{g[0]} - {g[1]}" for g in grados]

        secciones = self.repositorio.obtener_secciones()
        self.listbox_secciones.delete(0, tk.END)
        self.mapa_secciones.clear()

        for sec in secciones:
            id_sec = sec[0]
            texto_pantalla = f"Sección {sec[1]}"
            self.listbox_secciones.insert(tk.END, texto_pantalla)
            self.mapa_secciones[texto_pantalla] = id_sec

    def guardar_click(self):
        """Valida, construye las entidades y delega el guardado en lote."""
        materia = self.entry_nom_mat.get().strip().upper()
        prof_seleccionado = self.combo_prof.get()
        grado_seleccionado = self.combo_grado.get()
        indices_secciones = self.listbox_secciones.curselection()

        if not materia or not prof_seleccionado or not grado_seleccionado or not indices_secciones:
            messagebox.showwarning("Faltan Datos", "Complete todos los campos y elija al menos una sección.")
            return

        try:
            id_prof = int(prof_seleccionado.split(" - ")[0])
            id_grado = int(grado_seleccionado.split(" - ")[0])

            lista_materias_nuevas = []
            for idx in indices_secciones:
                texto_seccion = self.listbox_secciones.get(idx)
                id_seccion = self.mapa_secciones[texto_seccion]

                nueva_clase = Clase(materia, id_prof, id_grado, id_seccion)
                nueva_clase.validar()
                lista_materias_nuevas.append(nueva_clase)

            self.repositorio.guardar_lote(lista_materias_nuevas)
            messagebox.showinfo(
                "Éxito",
                f"Materia '{materia}' registrada correctamente para {len(lista_materias_nuevas)} sección(es)."
            )

            self.entry_nom_mat.delete(0, tk.END)
            self.combo_prof.set('')
            self.combo_grado.set('')
            self.listbox_secciones.selection_clear(0, tk.END)
            self.entry_nom_mat.focus()

        except ValueError as e:
            messagebox.showwarning("Regla de Negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")
