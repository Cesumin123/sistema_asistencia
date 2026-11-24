# adaptadores/ui/ui_estudiante.py
"""
Adaptador de Interfaz de Usuario para el módulo de Estudiantes.
Formulario con sub-bloques bien alineados (datos personales, familiares con madre/padre,
panel de foto 240x240 px), tabla zebra y exportación de Ficha Técnica Estudiantil en PDF.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import string

from dominio.estudiante import Estudiante
from puertos.repositorio_estudiante import PuertoRepositorioEstudiante
from adaptadores.ui.utilidades_ui import (
    centrar_ventana, maximizar_ventana,
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
    AyudaVisual, enfocar_siguiente, abrir_archivo_sistema, restaurar_foco,
)


class UIEstudiante:
    """Adaptador de Interfaz de Usuario para el módulo de Estudiantes."""

    def __init__(
        self,
        repositorio: PuertoRepositorioEstudiante,
        parent=None,
        exportador_pdf=None,
        gestor_fotos=None,
        repositorio_reportes=None
    ):
        self.repositorio = repositorio
        self.exportador_pdf = exportador_pdf
        self.gestor_fotos = gestor_fotos
        self.repositorio_reportes = repositorio_reportes

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Toplevel()

        self.root.title("Gestión de Estudiantes — Inscripciones y Expedientes")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 1200, 800)
        maximizar_ventana(self.root)

        self.cedula_seleccionada = None
        self.foto_path_actual = ""
        self.preview_foto_tk = None
        self._foto_preview_ref = None

        self.mapa_secciones = {chr(i): i - 64 for i in range(65, 91)}
        self.mapa_secciones_inverso = {v: k for k, v in self.mapa_secciones.items()}

        self.crear_interfaz()
        self._cargar_secciones_desde_bd()
        self.cargar_datos()

    def _cargar_secciones_desde_bd(self):
        """Carga dinámicamente las secciones de la BD sin listas hardcodeadas."""
        if hasattr(self.repositorio, "obtener_secciones"):
            try:
                secs = self.repositorio.obtener_secciones()
                if secs:
                    self.mapa_secciones = {s[1]: s[0] for s in secs}
                    self.mapa_secciones_inverso = {s[0]: s[1] for s in secs}
                    self.combo_seccion['values'] = [s[1] for s in secs]
            except Exception:
                pass

    def crear_interfaz(self):
        """Construye la interfaz con formulario en tarjeta, bloque de foto y tabla zebra."""
        # ═══ ENCABEZADO ═══
        f_header = tk.Frame(self.root, bg=COLOR_PRIMARIO, pady=12)
        f_header.pack(fill="x")
        tk.Label(
            f_header, text="📋  EXPEDIENTES Y FICHAS TÉCNICAS DE ESTUDIANTES",
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

        # Contenedor dividido en 2 columnas: Datos (izquierda) y Foto (derecha)
        f_contenedor_form = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_contenedor_form.pack(fill="x")

        f_datos = tk.Frame(f_contenedor_form, bg=COLOR_TARJETA)
        f_datos.pack(side="left", fill="both", expand=True, padx=(0, 15))

        f_foto_est = tk.Frame(f_contenedor_form, bg=COLOR_TARJETA, width=140)
        f_foto_est.pack(side="right", fill="y", padx=(10, 0))

        # ──────────────────────────────────────────────────────────
        # SUB-BLOQUE 1: DATOS PERSONALES Y ACADÉMICOS
        # ──────────────────────────────────────────────────────────
        tk.Label(
            f_datos, text="DATOS PERSONALES Y ACADÉMICOS",
            font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO
        ).pack(anchor="w", pady=(0, 2))

        f1 = tk.Frame(f_datos, bg=COLOR_TARJETA)
        f1.pack(fill="x", pady=2)

        tk.Label(f1, text="Cédula:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_nac = ttk.Combobox(
            f1, textvariable=self.var_nac, values=["V", "E", "P"],
            width=3, state="readonly",
        )
        self.combo_nac.pack(side="left", padx=(4, 0))
        self.entry_cedula = tk.Entry(f1, width=13, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_cedula.pack(side="left", padx=(4, 15))
        AyudaVisual(self.entry_cedula, "Número de cédula sin puntos.")

        tk.Label(f1, text="Nombre Completo:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_nombre = tk.Entry(f1, width=28, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_nombre.pack(side="left", padx=(4, 15))
        self.entry_nombre.bind("<KeyRelease>", self.convertir_mayus)

        tk.Label(f1, text="Género:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_genero = ttk.Combobox(
            f1, textvariable=self.var_genero, values=["M", "F"],
            width=4, state="readonly",
        )
        self.combo_genero.pack(side="left")

        # Fila 2: Fecha Nac, Año, Sección, Escolaridad, Turno, Condición
        f2 = tk.Frame(f_datos, bg=COLOR_TARJETA)
        f2.pack(fill="x", pady=3)

        tk.Label(f2, text="F. Nac:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.calendario = DateEntry(
            f2, width=10, date_pattern='dd/mm/yyyy', locale='es_ES',
            background='darkblue', state="readonly",
        )
        self.calendario.pack(side="left", padx=(4, 12))

        tk.Label(f2, text="Año (1-5):", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_grado = tk.Entry(f2, width=4, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_grado.pack(side="left", padx=(4, 12))

        tk.Label(f2, text="Sección:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_seccion = ttk.Combobox(
            f2, textvariable=self.var_seccion,
            values=list(string.ascii_uppercase), width=3, state="readonly",
        )
        self.combo_seccion.pack(side="left", padx=(4, 12))

        tk.Label(f2, text="Escolaridad:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_escolaridad = ttk.Combobox(
            f2, textvariable=self.var_escolaridad,
            values=["Regular", "Materia Pendiente", "Repite"], width=13, state="readonly",
        )
        self.combo_escolaridad.pack(side="left", padx=(4, 10))

        tk.Label(f2, text="Turno:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_turno = ttk.Combobox(
            f2, textvariable=self.var_turno,
            values=["Mañana", "Tarde"], width=8, state="readonly",
        )
        self.combo_turno.pack(side="left", padx=(4, 10))

        tk.Label(f2, text="Condición:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(side="left")
        self.combo_condicion = ttk.Combobox(
            f2, textvariable=self.var_condicion,
            values=["Activo", "Preinscrito"], width=9, state="readonly",
        )
        self.combo_condicion.pack(side="left", padx=(4, 0))

        # ──────────────────────────────────────────────────────────
        # SUB-BLOQUE 2: DATOS FAMILIARES Y REPRESENTANTES
        # ──────────────────────────────────────────────────────────
        crear_separador(f_datos).pack(fill="x", pady=5)
        tk.Label(
            f_datos, text="NÚCLEO FAMILIAR Y REPRESENTACIÓN LEGAL",
            font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO
        ).pack(anchor="w", pady=(0, 2))

        # Fila 3: Representante Legal y Teléfono
        f3 = tk.Frame(f_datos, bg=COLOR_TARJETA)
        f3.pack(fill="x", pady=2)

        tk.Label(f3, text="Representante Legal:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA, fg=COLOR_PRIMARIO).pack(side="left")
        self.entry_repre = tk.Entry(f3, width=28, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_repre.pack(side="left", padx=(4, 15))
        self.entry_repre.bind("<KeyRelease>", self.convertir_mayus)

        tk.Label(f3, text="Teléfono Repr.:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA, fg=COLOR_PRIMARIO).pack(side="left")
        self.entry_telf = tk.Entry(f3, width=14, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_telf.pack(side="left", padx=(4, 0))

        # Fila 4: Datos de la Madre y Padre
        f4 = tk.Frame(f_datos, bg="#F0F7F4", pady=4, padx=6)
        f4.pack(fill="x", pady=(4, 0))

        tk.Label(f4, text="Madre:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_madre = tk.Entry(f4, width=22, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_madre.pack(side="left", padx=(4, 10))
        self.entry_madre.bind("<KeyRelease>", self.convertir_mayus)

        tk.Label(f4, text="Telf. Madre:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_telf_madre = tk.Entry(f4, width=12, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_telf_madre.pack(side="left", padx=(4, 15))

        tk.Label(f4, text="Padre:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_padre = tk.Entry(f4, width=22, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_padre.pack(side="left", padx=(4, 10))
        self.entry_padre.bind("<KeyRelease>", self.convertir_mayus)

        tk.Label(f4, text="Telf. Padre:", bg="#F0F7F4", font=FUENTE_ETIQUETA).pack(side="left")
        self.entry_telf_padre = tk.Entry(f4, width=12, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_telf_padre.pack(side="left", padx=(4, 0))

        # ──────────────────────────────────────────────────────────
        # SUB-BLOQUE 3: FOTOGRAFÍA DEL ESTUDIANTE
        # ──────────────────────────────────────────────────────────
        tk.Label(f_foto_est, text="Fotografía:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).pack(anchor="center", pady=(0, 4))
        
        self.f_foto_container = tk.Frame(f_foto_est, width=110, height=110, bg="#EAECEE", relief="solid", bd=1)
        self.f_foto_container.pack_propagate(False)
        self.f_foto_container.pack(anchor="center", pady=(0, 6))

        self.lbl_foto = tk.Label(
            self.f_foto_container, text="[ SIN FOTO ]", bg="#EAECEE", fg=COLOR_TEXTO_SECUNDARIO,
            font=FUENTE_PEQUEÑA
        )
        self.lbl_foto.pack(fill="both", expand=True)

        f_foto_btns = tk.Frame(f_foto_est, bg=COLOR_TARJETA)
        f_foto_btns.pack(fill="x")
        self.btn_cargar_foto = crear_boton(f_foto_btns, "📷 Cargar", self.cargar_foto_click, COLOR_PRIMARIO, COLOR_TEXTO_CLARO, ancho=8)
        self.btn_cargar_foto.pack(side="left", padx=2)
        AyudaVisual(self.btn_cargar_foto, "Cargar fotografía oficial del estudiante")

        self.btn_quitar_foto = crear_boton(f_foto_btns, "✖ Quitar", self.quitar_foto_click, "#7F8C8D", COLOR_TEXTO_CLARO, ancho=7)
        self.btn_quitar_foto.pack(side="left", padx=2)
        AyudaVisual(self.btn_quitar_foto, "Eliminar fotografía asignada")

        # ═══ BOTONERA PRINCIPAL ═══
        f_btns = tk.Frame(self.root, bg=COLOR_FONDO_APP)
        f_btns.pack(pady=6)

        crear_boton(f_btns, "💾  GUARDAR", self.guardar_nuevo, COLOR_ACENTO, COLOR_TEXTO_CLARO, COLOR_ACENTO_HOVER).pack(side="left", padx=5)
        crear_boton(f_btns, "📝  MODIFICAR", self.modificar_existente, COLOR_ADVERTENCIA, COLOR_TEXTO_CLARO, COLOR_ADVERTENCIA_HOVER).pack(side="left", padx=5)
        crear_boton(f_btns, "🗑️  ELIMINAR", self.eliminar_estudiante, COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER).pack(side="left", padx=5)
        crear_boton(f_btns, "🖨️  FICHA PDF", self.imprimir_ficha_click, "#2980B9", COLOR_TEXTO_CLARO, "#3498DB").pack(side="left", padx=5)
        crear_boton(f_btns, "🧹  LIMPIAR", self.limpiar_formulario, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="left", padx=5)

        # ═══ TABLA DE DATOS (ZEBRA) ═══
        cols = ("cedula", "nombre", "nac", "repre", "telf", "gen", "esc", "tur", "cond", "anio", "sec")
        encabezados = ["Cédula", "Nombre", "F. Nac", "Representante", "Telf", "Sexo",
                       "Escolaridad", "Turno", "Cond", "Año", "Sec"]
        anchos = [90, 200, 80, 150, 90, 40, 90, 60, 60, 40, 40]
        anclas = ["center", "w", "center", "w", "center", "center", "center", "center", "center", "center", "center"]

        self.tree, frame_tree = crear_treeview_zebra(
            self.root, cols, encabezados, anchos, anclas, alto=11,
        )
        frame_tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.cargar_formulario_desde_tabla)

    # ──────────────────────────────────────────────────────────
    # HERRAMIENTAS Y FOTOGRAFÍA
    # ──────────────────────────────────────────────────────────
    def convertir_mayus(self, event):
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.icursor(pos)

    def _obtener_cedula_actual(self) -> str:
        num = self.entry_cedula.get().strip()
        if not num:
            return ""
        return f"{self.combo_nac.get()}-{num}".upper()

    def cargar_foto_click(self):
        cedula = self._obtener_cedula_actual()
        if not cedula:
            messagebox.showwarning("Atención", "Ingrese primero la cédula del estudiante antes de cargar su fotografía.", parent=self.root)
            restaurar_foco(self.root)
            self.entry_cedula.focus()
            return

        ruta_origen = filedialog.askopenfilename(
            parent=self.root,
            title="Seleccionar fotografía del estudiante",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Todos los archivos", "*.*")]
        )
        restaurar_foco(self.root)
        if not ruta_origen:
            return

        if not self.gestor_fotos:
            messagebox.showwarning("Aviso", "El gestor de fotografías no está disponible.", parent=self.root)
            restaurar_foco(self.root)
            return

        try:
            ruta_rel = self.gestor_fotos.guardar_foto(ruta_origen, "estudiante", cedula)
            self.foto_path_actual = ruta_rel
            self._mostrar_preview_foto(ruta_rel)
            messagebox.showinfo("Fotografía Cargada", "La fotografía se optimizó y guardó correctamente (240x240 px).", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error de Imagen", f"No se pudo procesar la fotografía: {e}", parent=self.root)
        finally:
            restaurar_foco(self.root)

    def quitar_foto_click(self):
        self.foto_path_actual = ""
        self.lbl_foto.config(image="", text="[ SIN FOTO ]")
        self.lbl_foto.image = None
        self.preview_foto_tk = None
        self._foto_preview_ref = None

    def _mostrar_preview_foto(self, ruta_foto: str):
        if not ruta_foto:
            self.quitar_foto_click()
            return

        if self.gestor_fotos:
            img_tk = self.gestor_fotos.cargar_preview_tk(ruta_foto, (110, 110), master=self.root)
            if img_tk:
                self.preview_foto_tk = img_tk
                self._foto_preview_ref = img_tk
                self.lbl_foto.image = img_tk
                self.lbl_foto.config(image=img_tk, text="")
                return

        self.quitar_foto_click()

    def limpiar_formulario(self):
        self.cedula_seleccionada = None
        self.entry_cedula.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.entry_repre.delete(0, tk.END)
        self.entry_telf.delete(0, tk.END)
        self.entry_madre.delete(0, tk.END)
        self.entry_telf_madre.delete(0, tk.END)
        self.entry_padre.delete(0, tk.END)
        self.entry_telf_padre.delete(0, tk.END)
        self.entry_grado.delete(0, tk.END)
        self.combo_nac.current(0)
        self.combo_genero.current(0)
        self.combo_seccion.current(0)
        self.combo_escolaridad.current(0)
        self.combo_turno.current(0)
        self.combo_condicion.current(0)
        self.calendario.set_date(datetime.now())
        self.quitar_foto_click()
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
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
            nombre_madre=self.entry_madre.get().strip(),
            telefono_madre=self.entry_telf_madre.get().strip(),
            nombre_padre=self.entry_padre.get().strip(),
            telefono_padre=self.entry_telf_padre.get().strip(),
            foto_path=self.foto_path_actual,
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
        self.cedula_seleccionada = str(valores[0])

        est = self.repositorio.obtener_por_cedula(self.cedula_seleccionada)
        if not est:
            return

        self.limpiar_formulario()
        self.cedula_seleccionada = est.cedula

        if '-' in est.cedula:
            p = est.cedula.split('-', 1)
            if p[0] in ("V", "E", "P"):
                self.combo_nac.set(p[0])
            self.entry_cedula.insert(0, p[1])
        else:
            self.entry_cedula.insert(0, est.cedula)

        self.entry_nombre.insert(0, est.nombre)
        try:
            fecha_obj = datetime.strptime(est.fecha_nacimiento, '%d/%m/%Y').date()
            self.calendario.set_date(fecha_obj)
        except (ValueError, TypeError):
            pass

        self.entry_repre.insert(0, est.representante or "")
        self.entry_telf.insert(0, est.telefono or "")
        self.entry_madre.insert(0, getattr(est, "nombre_madre", "") or "")
        self.entry_telf_madre.insert(0, getattr(est, "telefono_madre", "") or "")
        self.entry_padre.insert(0, getattr(est, "nombre_padre", "") or "")
        self.entry_telf_padre.insert(0, getattr(est, "telefono_padre", "") or "")

        self.combo_genero.set(est.genero or "M")
        self.combo_escolaridad.set(est.escolaridad or "Regular")
        self.combo_turno.set(est.turno or "Mañana")
        self.combo_condicion.set(est.condicion or "Activo")
        self.entry_grado.insert(0, str(est.id_grado))

        letra_seccion = self.mapa_secciones_inverso.get(est.id_seccion, "A")
        self.combo_seccion.set(letra_seccion)

        self.foto_path_actual = getattr(est, "foto_path", "") or ""
        self._mostrar_preview_foto(self.foto_path_actual)

    # ──────────────────────────────────────────────────────────
    # FUNCIONES CRUD Y ACCIONES
    # ──────────────────────────────────────────────────────────
    def guardar_nuevo(self):
        try:
            nuevo = self._obtener_entidad_desde_formulario()
            nuevo.validar()
            if self.repositorio.guardar(nuevo):
                messagebox.showinfo("Éxito", "Estudiante registrado correctamente.", parent=self.root)
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo guardar. Verifica que la cédula no esté duplicada.", parent=self.root)
        except ValueError as e:
            messagebox.showwarning("Faltan Datos o Error", str(e), parent=self.root)
        finally:
            restaurar_foco(self.root)

    def modificar_existente(self):
        if not self.cedula_seleccionada:
            messagebox.showwarning("Atención", "Primero seleccione un estudiante de la tabla.", parent=self.root)
            restaurar_foco(self.root)
            return
        try:
            est = self._obtener_entidad_desde_formulario()
            est.cedula = self.cedula_seleccionada
            est.validar()
            if self.repositorio.actualizar(est):
                messagebox.showinfo("Éxito", "Datos actualizados correctamente.", parent=self.root)
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el registro.", parent=self.root)
        except ValueError as e:
            messagebox.showwarning("Error en los datos", str(e), parent=self.root)
        finally:
            restaurar_foco(self.root)

    def eliminar_estudiante(self):
        if not self.cedula_seleccionada:
            messagebox.showwarning("Atención", "Seleccione un estudiante para eliminar.", parent=self.root)
            restaurar_foco(self.root)
            return
        if not messagebox.askyesno("Confirmar", f"¿Seguro que desea eliminar a {self.cedula_seleccionada}?", parent=self.root):
            restaurar_foco(self.root)
            return
        try:
            if self.repositorio.eliminar(self.cedula_seleccionada):
                messagebox.showinfo("Listo", "Estudiante desactivado (borrado lógico).", parent=self.root)
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo eliminar al estudiante.", parent=self.root)
        finally:
            restaurar_foco(self.root)

    def imprimir_ficha_click(self):
        """Genera y ofrece abrir la Ficha Técnica Oficial del Estudiante en PDF."""
        cedula = self.cedula_seleccionada or self._obtener_cedula_actual()
        if not cedula:
            messagebox.showwarning("Atención", "Seleccione un estudiante de la tabla para imprimir su ficha.", parent=self.root)
            restaurar_foco(self.root)
            return

        est = self.repositorio.obtener_por_cedula(cedula)
        if not est:
            messagebox.showwarning("Atención", f"No se encontró el estudiante con cédula {cedula}.", parent=self.root)
            restaurar_foco(self.root)
            return

        if not self.exportador_pdf:
            messagebox.showerror("Error", "El servicio de exportación PDF no está disponible.", parent=self.root)
            restaurar_foco(self.root)
            return

        # Calcular resumen de asistencia si el repositorio de reportes está disponible
        resumen = None
        if self.repositorio_reportes:
            try:
                historial = self.repositorio_reportes.obtener_historial_estudiante(est.cedula)
                if historial:
                    total = len(historial)
                    presentes = sum(1 for h in historial if h.get("estado") == "P")
                    ausencias = sum(1 for h in historial if h.get("estado") == "A")
                    justificadas = sum(1 for h in historial if h.get("estado") == "J")
                    porc = (presentes / total * 100.0) if total > 0 else 100.0
                    resumen = {
                        "total_clases": total,
                        "presentes": presentes,
                        "ausencias": ausencias,
                        "justificadas": justificadas,
                        "porcentaje": porc,
                        "en_riesgo": porc < 75.0,
                    }
            except Exception:
                resumen = None

        ced_limpia = str(est.cedula).replace("-", "_").replace(".", "")
        nombre_sugerido = f"Ficha_Estudiante_{ced_limpia}.pdf"
        ruta_salida = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=nombre_sugerido,
            title="Guardar Ficha Técnica del Estudiante"
        )
        restaurar_foco(self.root)
        if not ruta_salida:
            return

        try:
            ruta_pdf = self.exportador_pdf.generar_ficha_estudiante(est, resumen, ruta_salida)
            if messagebox.askyesno(
                "Ficha Generada",
                f"Ficha oficial generada con éxito:\n{ruta_pdf}\n\n¿Desea abrir el archivo ahora?",
                parent=self.root
            ):
                abrir_archivo_sistema(ruta_pdf)
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo generar la ficha PDF: {e}", parent=self.root)
        finally:
            restaurar_foco(self.root)
