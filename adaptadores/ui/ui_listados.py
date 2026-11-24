# adaptadores/ui/ui_listados.py
"""
Adaptador de Interfaz Gráfica para Listados Centralizados (RF-13).
Desacoplado de SQL: interactúa únicamente con PuertoRepositorioListados
y opcionalmente con PuertoExportadorPDF para generar reportes impresos.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any

from puertos.repositorio_listados import PuertoRepositorioListados
from puertos.repositorio_reportes import PuertoExportadorPDF


class UIListados:
    """
    Visor centralizado de nóminas institucionales:
    - Pestaña 1: Alumnos Activos
    - Pestaña 2: Materias / Clases y Docentes
    - Pestaña 3: Profesores Activos
    """

    def __init__(
        self,
        repo_listados: PuertoRepositorioListados,
        exportador_pdf: Optional[PuertoExportadorPDF] = None,
        parent: Optional[tk.Widget] = None
    ):
        self.repo = repo_listados
        self.exportador_pdf = exportador_pdf

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Listados Generales y Consolidados (Hexagonal)")
        self.root.geometry("1100x680")
        try:
            self.root.state('zoomed')
        except Exception:
            pass

        # Cachés locales para soporte de filtrado en vivo
        self._datos_alumnos: List[Dict[str, Any]] = []
        self._datos_materias: List[Dict[str, Any]] = []
        self._datos_profesores: List[Dict[str, Any]] = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        """Crea el contenedor con pestañas independientes."""
        frame_titulo = tk.Frame(self.root, bg="#34495e", pady=10)
        frame_titulo.pack(fill="x")
        tk.Label(
            frame_titulo,
            text="SISTEMA ESCOLAR — LISTADOS Y CONSOLIDADOS INSTITUCIONALES",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#34495e"
        ).pack()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=10)

        self._crear_tab_alumnos()
        self._crear_tab_materias()
        self._crear_tab_profesores()

    # -------------------------------------------------------------------------
    # PESTAÑA 1: ALUMNOS
    # -------------------------------------------------------------------------
    def _crear_tab_alumnos(self):
        tab = tk.Frame(self.notebook, padx=10, pady=5)
        self.notebook.add(tab, text="👤 Alumnos Activos")

        # Barra superior con buscador y botones
        f_top = tk.Frame(tab, pady=6)
        f_top.pack(fill="x")

        tk.Label(f_top, text="🔍 Filtrar:", font=("Arial", 9, "bold")).pack(side="left", padx=4)
        self.entry_filtro_alumnos = tk.Entry(f_top, width=25)
        self.entry_filtro_alumnos.pack(side="left", padx=5)
        self.entry_filtro_alumnos.bind("<KeyRelease>", lambda e: self._filtrar_alumnos())

        tk.Button(
            f_top, text="🔄 Refrescar", command=self.cargar_alumnos, cursor="hand2"
        ).pack(side="left", padx=8)

        if self.exportador_pdf:
            tk.Button(
                f_top, text="🖨️ Exportar a PDF", bg="#c0392b", fg="white",
                font=("Arial", 9, "bold"), cursor="hand2",
                command=lambda: self._exportar_tabla_pdf(
                    self.tree_alumnos,
                    "LISTADO GENERAL DE ALUMNOS ACTIVOS",
                    ["Cédula", "Estudiante", "Nacimiento", "Representante", "Teléfono", "Gen", "Año", "Sec"]
                )
            ).pack(side="right", padx=5)

        # Tabla de alumnos
        cols = ("cedula", "nombre", "nacimiento", "representante", "telefono", "genero", "grado", "seccion", "condicion", "turno")
        self.tree_alumnos = ttk.Treeview(tab, columns=cols, show="headings")

        self.tree_alumnos.heading("cedula", text="Cédula"); self.tree_alumnos.column("cedula", width=90, anchor="center")
        self.tree_alumnos.heading("nombre", text="Estudiante"); self.tree_alumnos.column("nombre", width=220, anchor="w")
        self.tree_alumnos.heading("nacimiento", text="F. Nac"); self.tree_alumnos.column("nacimiento", width=90, anchor="center")
        self.tree_alumnos.heading("representante", text="Representante"); self.tree_alumnos.column("representante", width=180, anchor="w")
        self.tree_alumnos.heading("telefono", text="Teléfono"); self.tree_alumnos.column("telefono", width=100, anchor="center")
        self.tree_alumnos.heading("genero", text="Gen"); self.tree_alumnos.column("genero", width=40, anchor="center")
        self.tree_alumnos.heading("grado", text="Año"); self.tree_alumnos.column("grado", width=80, anchor="center")
        self.tree_alumnos.heading("seccion", text="Sec"); self.tree_alumnos.column("seccion", width=50, anchor="center")
        self.tree_alumnos.heading("condicion", text="Condición"); self.tree_alumnos.column("condicion", width=80, anchor="center")
        self.tree_alumnos.heading("turno", text="Turno"); self.tree_alumnos.column("turno", width=80, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.tree_alumnos.yview)
        self.tree_alumnos.configure(yscrollcommand=scroll.set)

        self.tree_alumnos.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.cargar_alumnos()

    def cargar_alumnos(self):
        """Consulta el repositorio y llena la tabla de alumnos."""
        for item in self.tree_alumnos.get_children():
            self.tree_alumnos.delete(item)

        self._datos_alumnos = self.repo.obtener_estudiantes_activos()
        for a in self._datos_alumnos:
            self.tree_alumnos.insert(
                "", "end",
                values=(
                    a["cedula"], a["nombre"], a["nacimiento"], a["representante"],
                    a["telefono"], a["genero"], a["grado"], a["seccion"],
                    a["condicion"], a["turno"]
                )
            )

    def _filtrar_alumnos(self):
        """Filtra en vivo la lista de alumnos según el texto ingresado."""
        termino = self.entry_filtro_alumnos.get().strip().lower()
        for item in self.tree_alumnos.get_children():
            self.tree_alumnos.delete(item)

        for a in self._datos_alumnos:
            if (termino in a["cedula"].lower() or
                termino in a["nombre"].lower() or
                termino in a["representante"].lower() or
                termino in a["grado"].lower()):
                self.tree_alumnos.insert(
                    "", "end",
                    values=(
                        a["cedula"], a["nombre"], a["nacimiento"], a["representante"],
                        a["telefono"], a["genero"], a["grado"], a["seccion"],
                        a["condicion"], a["turno"]
                    )
                )

    # -------------------------------------------------------------------------
    # PESTAÑA 2: MATERIAS
    # -------------------------------------------------------------------------
    def _crear_tab_materias(self):
        tab = tk.Frame(self.notebook, padx=10, pady=5)
        self.notebook.add(tab, text="📚 Materias y Clases")

        f_top = tk.Frame(tab, pady=6)
        f_top.pack(fill="x")

        tk.Label(f_top, text="🔍 Filtrar:", font=("Arial", 9, "bold")).pack(side="left", padx=4)
        self.entry_filtro_materias = tk.Entry(f_top, width=25)
        self.entry_filtro_materias.pack(side="left", padx=5)
        self.entry_filtro_materias.bind("<KeyRelease>", lambda e: self._filtrar_materias())

        tk.Button(
            f_top, text="🔄 Refrescar", command=self.cargar_materias, cursor="hand2"
        ).pack(side="left", padx=8)

        if self.exportador_pdf:
            tk.Button(
                f_top, text="🖨️ Exportar a PDF", bg="#c0392b", fg="white",
                font=("Arial", 9, "bold"), cursor="hand2",
                command=lambda: self._exportar_tabla_pdf(
                    self.tree_materias,
                    "LISTADO GENERAL DE MATERIAS Y CLASES",
                    ["ID", "Materia", "Profesor Encargado", "Año / Grado", "Sección"]
                )
            ).pack(side="right", padx=5)

        cols = ("id_clase", "materia", "profesor", "grado", "seccion")
        self.tree_materias = ttk.Treeview(tab, columns=cols, show="headings")

        self.tree_materias.heading("id_clase", text="ID"); self.tree_materias.column("id_clase", width=50, anchor="center")
        self.tree_materias.heading("materia", text="Materia"); self.tree_materias.column("materia", width=220, anchor="w")
        self.tree_materias.heading("profesor", text="Profesor Encargado"); self.tree_materias.column("profesor", width=250, anchor="w")
        self.tree_materias.heading("grado", text="Año"); self.tree_materias.column("grado", width=120, anchor="center")
        self.tree_materias.heading("seccion", text="Sección"); self.tree_materias.column("seccion", width=80, anchor="center")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.tree_materias.yview)
        self.tree_materias.configure(yscrollcommand=scroll.set)

        self.tree_materias.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.cargar_materias()

    def cargar_materias(self):
        for item in self.tree_materias.get_children():
            self.tree_materias.delete(item)

        self._datos_materias = self.repo.obtener_materias_consolidadas()
        for m in self._datos_materias:
            self.tree_materias.insert(
                "", "end",
                values=(m["id_clase"], m["materia"], m["profesor"], m["grado"], m["seccion"])
            )

    def _filtrar_materias(self):
        termino = self.entry_filtro_materias.get().strip().lower()
        for item in self.tree_materias.get_children():
            self.tree_materias.delete(item)

        for m in self._datos_materias:
            if (termino in str(m["materia"]).lower() or
                termino in str(m["profesor"]).lower() or
                termino in str(m["grado"]).lower()):
                self.tree_materias.insert(
                    "", "end",
                    values=(m["id_clase"], m["materia"], m["profesor"], m["grado"], m["seccion"])
                )

    # -------------------------------------------------------------------------
    # PESTAÑA 3: PROFESORES
    # -------------------------------------------------------------------------
    def _crear_tab_profesores(self):
        tab = tk.Frame(self.notebook, padx=10, pady=5)
        self.notebook.add(tab, text="👨‍🏫 Nómina de Profesores")

        f_top = tk.Frame(tab, pady=6)
        f_top.pack(fill="x")

        tk.Label(f_top, text="🔍 Filtrar:", font=("Arial", 9, "bold")).pack(side="left", padx=4)
        self.entry_filtro_profesores = tk.Entry(f_top, width=25)
        self.entry_filtro_profesores.pack(side="left", padx=5)
        self.entry_filtro_profesores.bind("<KeyRelease>", lambda e: self._filtrar_profesores())

        tk.Button(
            f_top, text="🔄 Refrescar", command=self.cargar_profesores, cursor="hand2"
        ).pack(side="left", padx=8)

        if self.exportador_pdf:
            tk.Button(
                f_top, text="🖨️ Exportar a PDF", bg="#c0392b", fg="white",
                font=("Arial", 9, "bold"), cursor="hand2",
                command=lambda: self._exportar_tabla_pdf(
                    self.tree_profesores,
                    "NOMINA GENERAL DE PROFESORES",
                    ["ID", "Cédula", "Nombre Completo del Docente"]
                )
            ).pack(side="right", padx=5)

        cols = ("id_profesor", "cedula", "nombre")
        self.tree_profesores = ttk.Treeview(tab, columns=cols, show="headings")

        self.tree_profesores.heading("id_profesor", text="ID"); self.tree_profesores.column("id_profesor", width=60, anchor="center")
        self.tree_profesores.heading("cedula", text="Cédula"); self.tree_profesores.column("cedula", width=120, anchor="center")
        self.tree_profesores.heading("nombre", text="Nombre Completo del Docente"); self.tree_profesores.column("nombre", width=350, anchor="w")

        scroll = ttk.Scrollbar(tab, orient="vertical", command=self.tree_profesores.yview)
        self.tree_profesores.configure(yscrollcommand=scroll.set)

        self.tree_profesores.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.cargar_profesores()

    def cargar_profesores(self):
        for item in self.tree_profesores.get_children():
            self.tree_profesores.delete(item)

        self._datos_profesores = self.repo.obtener_profesores_activos()
        for p in self._datos_profesores:
            self.tree_profesores.insert(
                "", "end",
                values=(p["id_profesor"], p["cedula"], p["nombre"])
            )

    def _filtrar_profesores(self):
        termino = self.entry_filtro_profesores.get().strip().lower()
        for item in self.tree_profesores.get_children():
            self.tree_profesores.delete(item)

        for p in self._datos_profesores:
            if (termino in str(p["cedula"]).lower() or
                termino in str(p["nombre"]).lower()):
                self.tree_profesores.insert(
                    "", "end",
                    values=(p["id_profesor"], p["cedula"], p["nombre"])
                )

    def _exportar_tabla_pdf(self, tree: ttk.Treeview, titulo: str, encabezados: List[str]):
        """Exporta el contenido actual visible del treeview a un archivo PDF."""
        if not tree.get_children():
            messagebox.showwarning("Vacío", "No hay datos para exportar en este listado.")
            return

        nombre_archivo = f"{titulo.replace(' ', '_')}.pdf"
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documentos PDF", "*.pdf")],
            initialfile=nombre_archivo
        )
        if not ruta:
            return

        try:
            datos_filas = []
            for item in tree.get_children():
                vals = tree.item(item)['values']
                fila = [str(v) for v in vals[:len(encabezados)]]
                datos_filas.append(fila)

            exito = self.exportador_pdf.exportar_tabla(titulo, encabezados, datos_filas, ruta)
            if exito:
                messagebox.showinfo("Éxito", f"Listado PDF generado exitosamente en:\n{ruta}")
            else:
                messagebox.showerror("Error", "No se pudo generar el documento PDF.")
        except Exception as error:
            messagebox.showerror("Error", f"Fallo al exportar PDF: {error}")


# Alias para compatibilidad
VisorListadosUI = UIListados
