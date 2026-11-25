# adaptadores/ui/ui_clase.py
"""
Adaptador de Interfaz de Usuario (UI) para la entidad Clase (Materias).
Tarjeta limpia centrada con formulario grid alineado.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from dominio.clase import Clase
from adaptadores.ui.utilidades_ui import (
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_SECUNDARIO,
    COLOR_SECUNDARIO_HOVER, COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_CLARO, COLOR_SEPARADOR,
    FUENTE_SUBTITULO, FUENTE_CUERPO, FUENTE_ETIQUETA, FUENTE_PEQUEÑA,
    crear_boton, crear_tarjeta, crear_separador,
    AyudaVisual, enfocar_siguiente, restaurar_foco,
)


class GestorClasesUI:
    """Adaptador de Interfaz de Usuario para la asignación de Materias/Clases."""

    def __init__(self, parent_notebook: ttk.Notebook, repositorio_clase):
        self.notebook = parent_notebook
        self.repositorio = repositorio_clase
        self.mapa_secciones = {}
        self.crear_tab()
        self.cargar_datos_en_listas()

    def convertir_mayus(self, event):
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.icursor(pos)

    def crear_tab(self):
        tab = tk.Frame(self.notebook, bg=COLOR_FONDO_APP)
        self.notebook.add(tab, text="  📚  ASIGNAR MATERIAS  ")

        frame_centro = tk.Frame(tab, bg=COLOR_FONDO_APP)
        frame_centro.pack(expand=True, fill="both", pady=25, padx=20)

        tarjeta = crear_tarjeta(frame_centro, padx=40, pady=25)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")

        # Encabezado
        tk.Label(tarjeta, text="ASIGNACIÓN ACADÉMICA DE MATERIAS", font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(anchor="w")
        tk.Label(
            tarjeta,
            text="Vincule la materia con el profesor titular, año y secciones.",
            font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SECUNDARIO,
            wraplength=460, justify="left",
        ).pack(anchor="w", pady=(2, 12))
        crear_separador(tarjeta).pack(fill="x", pady=(0, 16))

        # Formulario Grid
        f_grid = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_grid.pack(fill="x")

        tk.Label(f_grid, text="Nombre de la Materia:", font=FUENTE_ETIQUETA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL).grid(row=0, column=0, sticky="w", pady=8)
        self.entry_nom_mat = tk.Entry(f_grid, width=32, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_nom_mat.grid(row=0, column=1, sticky="w", padx=(15, 0), pady=8)
        self.entry_nom_mat.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_mat.bind("<Return>", enfocar_siguiente)
        self.entry_nom_mat.focus()
        AyudaVisual(self.entry_nom_mat, "Ej: MATEMÁTICAS, CASTELLANO, QUÍMICA...")

        tk.Label(f_grid, text="Profesor Encargado:", font=FUENTE_ETIQUETA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL).grid(row=1, column=0, sticky="w", pady=8)
        self.combo_prof = ttk.Combobox(f_grid, width=30, state="readonly")
        self.combo_prof.grid(row=1, column=1, sticky="w", padx=(15, 0), pady=8)
        self.combo_prof.bind("<Return>", enfocar_siguiente)

        tk.Label(f_grid, text="Año Escolar / Grado:", font=FUENTE_ETIQUETA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL).grid(row=2, column=0, sticky="w", pady=8)
        self.combo_grado = ttk.Combobox(f_grid, width=30, state="readonly")
        self.combo_grado['values'] = ["1 - 1er AÑO", "2 - 2do AÑO", "3 - 3er AÑO", "4 - 4to AÑO", "5 - 5to AÑO"]
        self.combo_grado.grid(row=2, column=1, sticky="w", padx=(15, 0), pady=8)
        self.combo_grado.bind("<Return>", enfocar_siguiente)

        tk.Label(f_grid, text="Secciones Destino:\n(Puede elegir varias)", font=FUENTE_ETIQUETA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, justify="left").grid(row=3, column=0, sticky="nw", pady=8)
        f_list = tk.Frame(f_grid, bg=COLOR_TARJETA)
        f_list.grid(row=3, column=1, sticky="w", padx=(15, 0), pady=8)

        self.listbox_secciones = tk.Listbox(f_list, height=5, width=28, selectmode=tk.MULTIPLE, exportselection=False, font=FUENTE_CUERPO)
        scroll_sec = ttk.Scrollbar(f_list, orient="vertical", command=self.listbox_secciones.yview)
        self.listbox_secciones.configure(yscrollcommand=scroll_sec.set)
        self.listbox_secciones.pack(side="left")
        scroll_sec.pack(side="right", fill="y")
        AyudaVisual(self.listbox_secciones, "Haga clic para seleccionar una o varias secciones (A–Z)")

        # Botón
        self.btn_inscribir = crear_boton(tarjeta, "💾  INSCRIBIR MATERIA", self.guardar_click, COLOR_SECUNDARIO, COLOR_TEXTO_CLARO, COLOR_SECUNDARIO_HOVER)
        self.btn_inscribir.pack(anchor="w", pady=(15, 0))
        AyudaVisual(self.btn_inscribir, "Asignar la materia seleccionada a todas las secciones marcadas")

    def cargar_datos_en_listas(self):
        profesores = self.repositorio.obtener_profesores_activos()
        self.combo_prof['values'] = [f"{p[0]} - {p[1]}" for p in profesores]

        grados = self.repositorio.obtener_grados()
        self.combo_grado['values'] = [f"{g[0]} - {g[1]}" for g in grados]

        secciones = self.repositorio.obtener_secciones()
        self.listbox_secciones.delete(0, tk.END)
        self.mapa_secciones.clear()
        for sec in secciones:
            texto_pantalla = f"Sección {sec[1]}"
            self.listbox_secciones.insert(tk.END, texto_pantalla)
            self.mapa_secciones[texto_pantalla] = sec[0]

    def guardar_click(self):
        parent = self.notebook.winfo_toplevel()
        materia = self.entry_nom_mat.get().strip().upper()
        prof_seleccionado = self.combo_prof.get()
        grado_seleccionado = self.combo_grado.get()
        indices_secciones = self.listbox_secciones.curselection()

        if not materia or not prof_seleccionado or not grado_seleccionado or not indices_secciones:
            messagebox.showwarning("Faltan Datos", "Complete todos los campos y elija al menos una sección.", parent=parent)
            restaurar_foco(self.notebook)
            return

        try:
            id_prof = int(prof_seleccionado.split(" - ")[0])
            id_grado = int(grado_seleccionado.split(" - ")[0])

            lista_nuevas = []
            for idx in indices_secciones:
                texto_sec = self.listbox_secciones.get(idx)
                id_seccion = self.mapa_secciones[texto_sec]
                nueva = Clase(materia, id_prof, id_grado, id_seccion)
                nueva.validar()
                lista_nuevas.append(nueva)

            self.repositorio.guardar_lote(lista_nuevas)
            messagebox.showinfo("Éxito", f"Materia '{materia}' registrada para {len(lista_nuevas)} sección(es).", parent=parent)
            self.entry_nom_mat.delete(0, tk.END)
            self.combo_prof.set('')
            self.combo_grado.set('')
            self.listbox_secciones.selection_clear(0, tk.END)
            self.entry_nom_mat.focus()
        except ValueError as e:
            messagebox.showwarning("Regla de Negocio", str(e), parent=parent)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}", parent=parent)
        finally:
            restaurar_foco(self.notebook)
