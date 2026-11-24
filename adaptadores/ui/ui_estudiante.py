# adaptadores/ui/ui_estudiante.py
"""
Adaptador de Interfaz de Usuario para el módulo de Estudiantes.
Formularios alineados con grid, espaciado consistente, validaciones claras
y tabla ttk.Treeview con scrollbar y filas alternas zebra.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import string

from dominio.estudiante import Estudiante
from puertos.repositorio_estudiante import PuertoRepositorioEstudiante
from adaptadores.ui.utilidades_ui import (
    aplicar_tema_global, centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_PELIGRO, COLOR_PELIGRO_HOVER,
    COLOR_ADVERTENCIA, COLOR_ADVERTENCIA_HOVER,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO,
    COLOR_SEPARADOR, COLOR_BORDE_TARJETA,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_BOTON, FUENTE_PEQUEÑA,
    crear_boton, crear_tarjeta, crear_separador,
    crear_treeview_zebra, insertar_fila_zebra,
    AyudaVisual, enfocar_siguiente,
)


class UIEstudiante:
    """Adaptador de Interfaz de Usuario para el módulo de Estudiantes."""

    def __init__(self, repositorio: PuertoRepositorioEstudiante, parent=None):
        self.repositorio = repositorio

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Toplevel()

        self.root.title("Gestión de Estudiantes — Inscripciones")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 1150, 780)
        maximizar_ventana(self.root)

        self.cedula_seleccionada = None
        self.mapa_secciones = {chr(i): i - 64 for i in range(65, 91)}
        self.mapa_secciones_inverso = {v: k for k, v in self.mapa_secciones.items()}

        self.crear_interfaz()
        self.cargar_datos()

    def crear_interfaz(self):
        """Construye la interfaz con formulario en tarjeta y tabla zebra."""
        # ═══ ENCABEZADO ═══
        f_header = tk.Frame(self.root, bg=COLOR_PRIMARIO, pady=12)
        f_header.pack(fill="x")
        tk.Label(
            f_header, text="📋  FICHA TÉCNICA DEL ESTUDIANTE",
            font=FUENTE_SUBTITULO, fg=COLOR_TEXTO_CLARO, bg=COLOR_PRIMARIO,
        ).pack(side="left", padx=20)

        # ═══ TARJETA DE FORMULARIO ═══
        tarjeta = crear_tarjeta(self.root, padx=20, pady=15)
        tarjeta.pack(fill="x", padx=15, pady=(10, 5))

        # Variables Tkinter
        self.var_nac = tk.StringVar(value="V")
        self.var_genero = tk.StringVar(value="M")
        self.var_seccion = tk.StringVar(value="A")
        self.var_escolaridad = tk.StringVar(value="Regular")
        self.var_turno = tk.StringVar(value="Mañana")
        self.var_condicion = tk.StringVar(value="Activo")

        # --- FILA 1: Cédula, Nombre, Género ---
        f1 = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f1.pack(fill="x", pady=4)

        tk.Label(f1, text="Cédula:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_nac = ttk.Combobox(
            f1, textvariable=self.var_nac, values=["V", "E", "P"],
            width=3, state="readonly",
        )
        self.combo_nac.pack(side="left", padx=(4, 0))
        self.entry_cedula = tk.Entry(f1, width=15, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_cedula.pack(side="left", padx=(4, 20))
        AyudaVisual(self.entry_cedula, "Número de cédula sin puntos.")

        tk.Label(f1, text="Nombre Completo:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_nombre = tk.Entry(f1, width=35, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_nombre.pack(side="left", padx=(4, 20))
        self.entry_nombre.bind("<KeyRelease>", self.convertir_mayus)

        tk.Label(f1, text="Género:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_genero = ttk.Combobox(
            f1, textvariable=self.var_genero, values=["M", "F"],
            width=4, state="readonly",
        )
        self.combo_genero.pack(side="left")

        # --- FILA 2: Fecha Nac, Año, Sección ---
        f2 = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f2.pack(fill="x", pady=4)

        tk.Label(f2, text="Fecha Nacimiento:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.calendario = DateEntry(
            f2, width=12, date_pattern='dd/mm/yyyy', locale='es_ES',
            background='darkblue', state="readonly",
        )
        self.calendario.pack(side="left", padx=(4, 20))

        tk.Label(f2, text="Año Escolar (1-5):", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_grado = tk.Entry(f2, width=5, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_grado.pack(side="left", padx=(4, 20))

        tk.Label(f2, text="Sección:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_seccion = ttk.Combobox(
            f2, textvariable=self.var_seccion,
            values=list(string.ascii_uppercase), width=4, state="readonly",
        )
        self.combo_seccion.pack(side="left")

        # --- FILA 3: Representante, Teléfono ---
        f3 = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f3.pack(fill="x", pady=4)

        tk.Label(f3, text="Representante:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA, fg=COLOR_PRIMARIO).pack(side="left")
        self.entry_repre = tk.Entry(f3, width=35, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_repre.pack(side="left", padx=(4, 20))
        self.entry_repre.bind("<KeyRelease>", self.convertir_mayus)

        tk.Label(f3, text="Teléfono:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA, fg=COLOR_PRIMARIO).pack(side="left")
        self.entry_telf = tk.Entry(f3, width=15, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_telf.pack(side="left")

        # --- FILA 4: Escolaridad, Turno, Condición ---
        f4 = tk.Frame(tarjeta, bg="#F0F7F4", pady=6, padx=8)
        f4.pack(fill="x", pady=(8, 0))

        tk.Label(f4, text="Escolaridad:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_escolaridad = ttk.Combobox(
            f4, textvariable=self.var_escolaridad,
            values=["Regular", "Materia Pendiente", "Repite"], width=15, state="readonly",
        )
        self.combo_escolaridad.pack(side="left", padx=(2, 20))

        tk.Label(f4, text="Turno:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_turno = ttk.Combobox(
            f4, textvariable=self.var_turno,
            values=["Mañana", "Tarde"], width=10, state="readonly",
        )
        self.combo_turno.pack(side="left", padx=(2, 20))

        tk.Label(f4, text="Condición:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_condicion = ttk.Combobox(
            f4, textvariable=self.var_condicion,
            values=["Activo", "Preinscrito"], width=12, state="readonly",
        )
        self.combo_condicion.pack(side="left")

        # ═══ BOTONERA ═══
        f_btns = tk.Frame(self.root, bg=COLOR_FONDO_APP)
        f_btns.pack(pady=8)

        crear_boton(f_btns, "💾  GUARDAR", self.guardar_nuevo, COLOR_ACENTO, COLOR_TEXTO_CLARO, COLOR_ACENTO_HOVER).pack(side="left", padx=6)
        crear_boton(f_btns, "📝  MODIFICAR", self.modificar_existente, COLOR_ADVERTENCIA, COLOR_TEXTO_CLARO, COLOR_ADVERTENCIA_HOVER).pack(side="left", padx=6)
        crear_boton(f_btns, "🗑️  ELIMINAR", self.eliminar_estudiante, COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER).pack(side="left", padx=6)
        crear_boton(f_btns, "🧹  Limpiar", self.limpiar_formulario, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="left", padx=6)

        # ═══ TABLA DE DATOS (ZEBRA) ═══
        cols = ("cedula", "nombre", "nac", "repre", "telf", "gen", "esc", "tur", "cond", "anio", "sec")
        encabezados = ["Cédula", "Nombre", "F. Nac", "Representante", "Telf", "Sexo",
                       "Escolaridad", "Turno", "Cond", "Año", "Sec"]
        anchos = [90, 200, 80, 150, 90, 40, 90, 60, 60, 40, 40]
        anclas = ["center", "w", "center", "w", "center", "center", "center", "center", "center", "center", "center"]

        self.tree, frame_tree = crear_treeview_zebra(
            self.root, cols, encabezados, anchos, anclas, alto=12,
        )
        frame_tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.cargar_formulario_desde_tabla)

    # ──────────────────────────────────────────────────────────
    # HERRAMIENTAS ÚTILES
    # ──────────────────────────────────────────────────────────
    def convertir_mayus(self, event):
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.index(pos)

    def limpiar_formulario(self):
        self.cedula_seleccionada = None
        self.entry_cedula.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.entry_repre.delete(0, tk.END)
        self.entry_telf.delete(0, tk.END)
        self.entry_grado.delete(0, tk.END)
        self.combo_nac.current(0)
        self.combo_genero.current(0)
        self.combo_seccion.current(0)
        self.combo_escolaridad.current(0)
        self.combo_turno.current(0)
        self.combo_condicion.current(0)
        self.calendario.set_date(datetime.now())
        self.entry_cedula.focus()

    # ──────────────────────────────────────────────────────────
    # LÓGICA DE CONEXIÓN CON EL DOMINIO
    # ──────────────────────────────────────────────────────────
    def _obtener_entidad_desde_formulario(self) -> Estudiante:
        nac = self.combo_nac.get()
        num = self.entry_cedula.get().strip()
        nombre = self.entry_nombre.get().strip()
        grado_str = self.entry_grado.get().strip()

        if not num or not nombre or not grado_str:
            raise ValueError("La Cédula, Nombre y Año Escolar son campos obligatorios.")

        try:
            grado = int(grado_str)
        except ValueError:
            raise ValueError("El Año Escolar debe ser un número (Ej: 1, 2, 3).")

        seccion_letra = self.combo_seccion.get()
        id_seccion_traducido = self.mapa_secciones.get(seccion_letra, 1)

        return Estudiante(
            cedula=f"{nac}-{num}",
            nombre=nombre,
            fecha_nacimiento=self.calendario.get_date().strftime('%d/%m/%Y'),
            representante=self.entry_repre.get().strip(),
            telefono=self.entry_telf.get().strip(),
            genero=self.combo_genero.get(),
            escolaridad=self.combo_escolaridad.get(),
            turno=self.combo_turno.get(),
            condicion=self.combo_condicion.get(),
            id_grado=grado,
            id_seccion=id_seccion_traducido,
        )

    def cargar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        estudiantes = self.repositorio.obtener_todos_activos()
        for est in estudiantes:
            letra_seccion = self.mapa_secciones_inverso.get(est.id_seccion, "A")
            valores = (
                est.cedula, est.nombre, est.fecha_nacimiento, est.representante,
                est.telefono, est.genero, est.escolaridad, est.turno,
                est.condicion, est.id_grado, letra_seccion,
            )
            insertar_fila_zebra(self.tree, valores)

    def cargar_formulario_desde_tabla(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0])['values']
        self.limpiar_formulario()
        self.cedula_seleccionada = str(valores[0])

        if '-' in self.cedula_seleccionada:
            p = self.cedula_seleccionada.split('-')
            self.combo_nac.set(p[0])
            self.entry_cedula.insert(0, p[1])
        else:
            self.entry_cedula.insert(0, self.cedula_seleccionada)

        self.entry_nombre.insert(0, valores[1])
        try:
            fecha_obj = datetime.strptime(valores[2], '%d/%m/%Y').date()
            self.calendario.set_date(fecha_obj)
        except (ValueError, TypeError):
            pass

        self.entry_repre.insert(0, valores[3] or "")
        self.entry_telf.insert(0, str(valores[4]) if valores[4] else "")
        self.combo_genero.set(valores[5])
        self.combo_escolaridad.set(valores[6] or "Regular")
        self.combo_turno.set(valores[7] or "Mañana")
        self.combo_condicion.set(valores[8] or "Activo")
        self.entry_grado.insert(0, str(valores[9]))
        self.combo_seccion.set(str(valores[10]))

    # ──────────────────────────────────────────────────────────
    # FUNCIONES CRUD
    # ──────────────────────────────────────────────────────────
    def guardar_nuevo(self):
        try:
            nuevo = self._obtener_entidad_desde_formulario()
            nuevo.validar()
            if self.repositorio.guardar(nuevo):
                messagebox.showinfo("Éxito", "Estudiante registrado correctamente.")
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo guardar. Verifica que la cédula no esté duplicada.")
        except ValueError as e:
            messagebox.showwarning("Faltan Datos o Error", str(e))

    def modificar_existente(self):
        if not self.cedula_seleccionada:
            messagebox.showwarning("Atención", "Primero seleccione un estudiante de la tabla.")
            return
        try:
            est = self._obtener_entidad_desde_formulario()
            est.cedula = self.cedula_seleccionada
            est.validar()
            if self.repositorio.actualizar(est):
                messagebox.showinfo("Éxito", "Datos actualizados correctamente.")
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el registro.")
        except ValueError as e:
            messagebox.showwarning("Error en los datos", str(e))

    def eliminar_estudiante(self):
        if not self.cedula_seleccionada:
            messagebox.showwarning("Atención", "Seleccione un estudiante para eliminar.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Seguro que desea eliminar a {self.cedula_seleccionada}?"):
            return
        if self.repositorio.eliminar(self.cedula_seleccionada):
            messagebox.showinfo("Listo", "Estudiante desactivado (borrado lógico).")
            self.limpiar_formulario()
            self.cargar_datos()
        else:
            messagebox.showerror("Error", "No se pudo eliminar al estudiante.")
