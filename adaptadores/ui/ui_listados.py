# adaptadores/ui/ui_listados.py
"""
Adaptador de Interfaz Gráfica para Listados Centralizados (RF-13).
Desacoplado de SQL. Pestañas limpias con filtrado en vivo, Treeview zebra
y exportación a PDF. Sistema de diseño unificado.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any

from puertos.repositorio_listados import PuertoRepositorioListados
from puertos.repositorio_reportes import PuertoExportadorPDF
from adaptadores.ui.utilidades_ui import (
    centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER, COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_CLARO, COLOR_SEPARADOR,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD,
    crear_boton, crear_treeview_zebra, insertar_fila_zebra, restaurar_foco,
)


class UIListados:
    """Visor centralizado de nóminas institucionales con 3 pestañas."""

    def __init__(self, repo_listados: PuertoRepositorioListados,
                 exportador_pdf: Optional[PuertoExportadorPDF] = None,
                 parent: Optional[tk.Widget] = None):
        self.repo = repo_listados
        self.exportador_pdf = exportador_pdf

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Listados Institucionales del Liceo")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 980, 660)
        maximizar_ventana(self.root)

        self._datos_alumnos: List[Dict[str, Any]] = []
        self._datos_materias: List[Dict[str, Any]] = []
        self._datos_profesores: List[Dict[str, Any]] = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        # Encabezado
        f_header = tk.Frame(self.root, bg=COLOR_PRIMARIO, pady=10)
        f_header.pack(fill="x")
        tk.Label(f_header, text="📑  LISTADOS  INSTITUCIONALES", font=FUENTE_ENCABEZADO, fg=COLOR_TEXTO_CLARO, bg=COLOR_PRIMARIO).pack()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=10)

        self._crear_tab_alumnos()
        self._crear_tab_materias()
        self._crear_tab_profesores()

    # ── PESTAÑA 1: ALUMNOS ──
    def _crear_tab_alumnos(self):
        tab = tk.Frame(self.notebook, padx=10, pady=5, bg=COLOR_FONDO_APP)
        self.notebook.add(tab, text="👤 Alumnos Activos")

        f_top = tk.Frame(tab, pady=6, bg=COLOR_FONDO_APP)
        f_top.pack(fill="x")
        tk.Label(f_top, text="🔍 Filtrar:", font=FUENTE_PEQUEÑA_BOLD, bg=COLOR_FONDO_APP).pack(side="left", padx=4)
        self.entry_filtro_alumnos = tk.Entry(f_top, width=25, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_filtro_alumnos.pack(side="left", padx=5)
        self.entry_filtro_alumnos.bind("<KeyRelease>", lambda e: self._filtrar_alumnos())
        crear_boton(f_top, "🔄 Refrescar", self.cargar_alumnos, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="left", padx=8)

        if self.exportador_pdf:
            crear_boton(
                f_top, "🖨️ PDF", lambda: self._exportar_tabla_pdf(
                    self.tree_alumnos, "LISTADO GENERAL DE ALUMNOS ACTIVOS",
                    ["Cédula", "Estudiante", "Nacimiento", "Representante", "Teléfono", "Gen", "Año", "Sec"]
                ), COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER,
            ).pack(side="right", padx=5)

        cols = ("cedula", "nombre", "nacimiento", "representante", "telefono", "genero", "grado", "seccion", "condicion", "turno")
        enc = ["Cédula", "Estudiante", "F. Nac", "Representante", "Teléfono", "Gen", "Año", "Sec", "Condición", "Turno"]
        anch = [85, 195, 80, 155, 92, 42, 75, 45, 78, 78]
        anclas = ["center", "w", "center", "w", "center", "center", "center", "center", "center", "center"]

        self.tree_alumnos, frame_tree = crear_treeview_zebra(tab, cols, enc, anch, anclas)
        frame_tree.pack(fill="both", expand=True)
        self.cargar_alumnos()

    def cargar_alumnos(self):
        for item in self.tree_alumnos.get_children():
            self.tree_alumnos.delete(item)
        self._datos_alumnos = self.repo.obtener_estudiantes_activos()
        for a in self._datos_alumnos:
            insertar_fila_zebra(self.tree_alumnos, (
                a["cedula"], a["nombre"], a["nacimiento"], a["representante"],
                a["telefono"], a["genero"], a["grado"], a["seccion"],
                a["condicion"], a["turno"],
            ))

    def _filtrar_alumnos(self):
        termino = self.entry_filtro_alumnos.get().strip().lower()
        for item in self.tree_alumnos.get_children():
            self.tree_alumnos.delete(item)
        for a in self._datos_alumnos:
            if any(termino in str(a.get(k, "")).lower() for k in ("cedula", "nombre", "representante", "grado")):
                insertar_fila_zebra(self.tree_alumnos, (
                    a["cedula"], a["nombre"], a["nacimiento"], a["representante"],
                    a["telefono"], a["genero"], a["grado"], a["seccion"],
                    a["condicion"], a["turno"],
                ))

    # ── PESTAÑA 2: MATERIAS ──
    def _crear_tab_materias(self):
        tab = tk.Frame(self.notebook, padx=10, pady=5, bg=COLOR_FONDO_APP)
        self.notebook.add(tab, text="📚 Materias y Clases")

        f_top = tk.Frame(tab, pady=6, bg=COLOR_FONDO_APP)
        f_top.pack(fill="x")
        tk.Label(f_top, text="🔍 Filtrar:", font=FUENTE_PEQUEÑA_BOLD, bg=COLOR_FONDO_APP).pack(side="left", padx=4)
        self.entry_filtro_materias = tk.Entry(f_top, width=25, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_filtro_materias.pack(side="left", padx=5)
        self.entry_filtro_materias.bind("<KeyRelease>", lambda e: self._filtrar_materias())
        crear_boton(f_top, "🔄 Refrescar", self.cargar_materias, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="left", padx=8)

        if self.exportador_pdf:
            crear_boton(
                f_top, "🖨️ PDF", lambda: self._exportar_tabla_pdf(
                    self.tree_materias, "LISTADO GENERAL DE MATERIAS",
                    ["ID", "Materia", "Profesor", "Año", "Sección"]
                ), COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER,
            ).pack(side="right", padx=5)

        cols = ("id_clase", "materia", "profesor", "grado", "seccion")
        enc = ["ID", "Materia", "Profesor Encargado", "Año", "Sección"]
        anch = [50, 220, 250, 120, 80]
        anclas = ["center", "w", "w", "center", "center"]

        self.tree_materias, frame_tree = crear_treeview_zebra(tab, cols, enc, anch, anclas)
        frame_tree.pack(fill="both", expand=True)
        self.cargar_materias()

    def cargar_materias(self):
        for item in self.tree_materias.get_children():
            self.tree_materias.delete(item)
        self._datos_materias = self.repo.obtener_materias_consolidadas()
        for m in self._datos_materias:
            insertar_fila_zebra(self.tree_materias, (m["id_clase"], m["materia"], m["profesor"], m["grado"], m["seccion"]))

    def _filtrar_materias(self):
        termino = self.entry_filtro_materias.get().strip().lower()
        for item in self.tree_materias.get_children():
            self.tree_materias.delete(item)
        for m in self._datos_materias:
            if any(termino in str(m.get(k, "")).lower() for k in ("materia", "profesor", "grado")):
                insertar_fila_zebra(self.tree_materias, (m["id_clase"], m["materia"], m["profesor"], m["grado"], m["seccion"]))

    # ── PESTAÑA 3: PROFESORES ──
    def _crear_tab_profesores(self):
        tab = tk.Frame(self.notebook, padx=10, pady=5, bg=COLOR_FONDO_APP)
        self.notebook.add(tab, text="👨‍🏫 Nómina de Profesores")

        f_top = tk.Frame(tab, pady=6, bg=COLOR_FONDO_APP)
        f_top.pack(fill="x")
        tk.Label(f_top, text="🔍 Filtrar:", font=FUENTE_PEQUEÑA_BOLD, bg=COLOR_FONDO_APP).pack(side="left", padx=4)
        self.entry_filtro_profesores = tk.Entry(f_top, width=25, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_filtro_profesores.pack(side="left", padx=5)
        self.entry_filtro_profesores.bind("<KeyRelease>", lambda e: self._filtrar_profesores())
        crear_boton(f_top, "🔄 Refrescar", self.cargar_profesores, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="left", padx=8)

        if self.exportador_pdf:
            crear_boton(
                f_top, "🖨️ PDF", lambda: self._exportar_tabla_pdf(
                    self.tree_profesores, "NOMINA GENERAL DE PROFESORES",
                    ["ID", "Cédula", "Nombre Completo", "Teléfono"]
                ), COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER,
            ).pack(side="right", padx=5)

        cols = ("id_profesor", "cedula", "nombre", "telefono")
        enc = ["ID", "Cédula", "Nombre Completo", "Teléfono"]
        anch = [55, 115, 310, 120]
        anclas = ["center", "center", "w", "center"]

        self.tree_profesores, frame_tree = crear_treeview_zebra(tab, cols, enc, anch, anclas)
        frame_tree.pack(fill="both", expand=True)
        self.cargar_profesores()

    def cargar_profesores(self):
        for item in self.tree_profesores.get_children():
            self.tree_profesores.delete(item)
        self._datos_profesores = self.repo.obtener_profesores_activos()
        for p in self._datos_profesores:
            insertar_fila_zebra(self.tree_profesores, (p["id_profesor"], p["cedula"], p["nombre"], p.get("telefono", "-")))

    def _filtrar_profesores(self):
        termino = self.entry_filtro_profesores.get().strip().lower()
        for item in self.tree_profesores.get_children():
            self.tree_profesores.delete(item)
        for p in self._datos_profesores:
            if any(termino in str(p.get(k, "")).lower() for k in ("cedula", "nombre", "telefono")):
                insertar_fila_zebra(self.tree_profesores, (p["id_profesor"], p["cedula"], p["nombre"], p.get("telefono", "-")))

    # ── EXPORTAR PDF ──
    def _exportar_tabla_pdf(self, tree: ttk.Treeview, titulo: str, encabezados: List[str]):
        if not tree.get_children():
            messagebox.showwarning("Vacío", "No hay datos para exportar.", parent=self.root)
            restaurar_foco(self.root)
            return
        nombre_archivo = f"{titulo.replace(' ', '_')}.pdf"
        ruta = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=nombre_archivo
        )
        restaurar_foco(self.root)
        if not ruta:
            return
        try:
            datos = [[str(v) for v in tree.item(item)['values'][:len(encabezados)]] for item in tree.get_children()]
            if self.exportador_pdf.exportar_tabla(titulo, encabezados, datos, ruta):
                messagebox.showinfo("Éxito", f"PDF generado en:\n{ruta}", parent=self.root)
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF.", parent=self.root)
        except Exception as error:
            messagebox.showerror("Error", f"Fallo al exportar: {error}", parent=self.root)
        finally:
            restaurar_foco(self.root)


# Alias
VisorListadosUI = UIListados
