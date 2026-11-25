# adaptadores/ui/ui_profesor.py
"""
Adaptador de Interfaz de Usuario (UI) para la entidad Profesor.
Incluye formulario con profesión, fotografía (240x240 px),
tabla de profesores registrados y exportación de Ficha Técnica Docente en PDF.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from PIL import Image, ImageTk

from dominio.profesor import Profesor
from adaptadores.ui.utilidades_ui import (
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_ADVERTENCIA, COLOR_ADVERTENCIA_HOVER,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO,
    COLOR_SEPARADOR, COLOR_BORDE_TARJETA,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_BOTON,
    crear_boton, crear_tarjeta, crear_separador, maximizar_ventana,
    crear_treeview_zebra, insertar_fila_zebra,
    AyudaVisual, enfocar_siguiente, abrir_archivo_sistema, restaurar_foco,
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


PROFESIONES_SUGERIDAS = [
    "Lcdo. en Educación",
    "Lcdo. en Matemáticas",
    "Lcdo. en Física",
    "Lcdo. en Química",
    "Lcdo. en Biología",
    "Lcdo. en Castellano y Literatura",
    "Lcdo. en Idiomas Modernos",
    "Lcdo. en Ciencias Sociales",
    "Lcdo. en Educación Física",
    "Ingeniero",
    "TSU",
    "Profesor",
    "MSc.",
    "Especialista",
]


class GestorProfesoresUI:
    """Adaptador de Interfaz de Usuario para el registro y gestión de Profesores."""

    def __init__(
        self,
        parent_notebook: ttk.Notebook,
        repositorio_profesor,
        exportador_pdf=None,
        gestor_fotos=None,
        repositorio_clase=None
    ):
        self.notebook = parent_notebook
        self.repositorio = repositorio_profesor
        self.exportador_pdf = exportador_pdf
        self.gestor_fotos = gestor_fotos
        self.repositorio_clase = repositorio_clase

        self.img_logo_tk = None
        self.preview_foto_tk = None
        self._foto_preview_ref = None
        self.foto_path_actual = ""
        self.profesor_seleccionado: Profesor | None = None

        self.crear_tab()
        self.cargar_profesores_en_tabla()
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
        """Construye la pestaña con layout de 2 columnas: formulario/foto a la izq, lista a la der."""
        tab = tk.Frame(self.notebook, bg=COLOR_FONDO_APP)
        self.notebook.add(tab, text="  👨‍🏫  GESTIÓN DE PROFESORES  ")

        # Contenedor principal con grid de 2 columnas
        contenedor = tk.Frame(tab, bg=COLOR_FONDO_APP)
        contenedor.pack(fill="both", expand=True, padx=14, pady=10)
        contenedor.columnconfigure(0, weight=5)
        contenedor.columnconfigure(1, weight=5)
        contenedor.rowconfigure(0, weight=1)

        # ══════════════════════════════════════════════════════════════════
        # COLUMNA IZQUIERDA: TARJETA DE FORMULARIO Y FOTO
        # ══════════════════════════════════════════════════════════════════
        tarjeta_form = crear_tarjeta(contenedor, padx=18, pady=12)
        tarjeta_form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Encabezado con Logo y Título
        f_header = tk.Frame(tarjeta_form, bg=COLOR_TARJETA)
        f_header.pack(fill="x", pady=(0, 8))

        ruta_logo = resolver_ruta_logo()
        if ruta_logo:
            try:
                img_orig = Image.open(ruta_logo)
                ratio = min(64 / img_orig.width, 64 / img_orig.height)
                nuevo_w = int(img_orig.width * ratio)
                nuevo_h = int(img_orig.height * ratio)
                img_redim = img_orig.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
                self.img_logo_tk = ImageTk.PhotoImage(img_redim)
                tk.Label(f_header, image=self.img_logo_tk, bg=COLOR_TARJETA).pack(side="left", padx=(0, 12))
            except Exception:
                pass

        f_titulos = tk.Frame(f_header, bg=COLOR_TARJETA)
        f_titulos.pack(side="left", fill="y", expand=True)
        tk.Label(f_titulos, text="EXPEDIENTE DOCENTE", font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(anchor="w")
        tk.Label(f_titulos, text="Complejo Educativo 'Colinas del Llano'", font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SECUNDARIO).pack(anchor="w", pady=(2, 0))

        crear_separador(tarjeta_form).pack(fill="x", pady=(0, 10))

        # Cuerpo del Formulario + Marco de Foto
        f_cuerpo = tk.Frame(tarjeta_form, bg=COLOR_TARJETA)
        f_cuerpo.pack(fill="both", expand=True)
        f_cuerpo.columnconfigure(0, weight=1)
        f_cuerpo.columnconfigure(1, minsize=160)

        # Sub-panel de campos de texto (lado izquierdo de la tarjeta)
        f_campos = tk.Frame(f_cuerpo, bg=COLOR_TARJETA)
        f_campos.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(f_campos, text="Cédula de Identidad:", bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA).pack(anchor="w", pady=(0, 2))
        f_ced = tk.Frame(f_campos, bg=COLOR_TARJETA)
        f_ced.pack(anchor="w", pady=(0, 6))

        self.combo_nac_prof = ttk.Combobox(f_ced, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac_prof.pack(side="left")
        self.combo_nac_prof.current(0)
        self.combo_nac_prof.bind("<Return>", enfocar_siguiente)

        self.entry_ced_prof = tk.Entry(f_ced, width=15, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_ced_prof.pack(side="left", padx=(6, 0))
        self.entry_ced_prof.bind("<Return>", enfocar_siguiente)
        self.entry_ced_prof.focus()
        AyudaVisual(self.entry_ced_prof, "Solo números sin puntos. Ej: 12345678")

        tk.Label(f_campos, text="Nombre Completo del Profesor:", bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA).pack(anchor="w", pady=(0, 2))
        self.entry_nom_prof = tk.Entry(f_campos, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_nom_prof.pack(fill="x", pady=(0, 6))
        self.entry_nom_prof.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_prof.bind("<Return>", enfocar_siguiente)

        tk.Label(f_campos, text="Profesión / Título Académico:", bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA).pack(anchor="w", pady=(0, 2))
        self.combo_profesion = ttk.Combobox(f_campos, values=PROFESIONES_SUGERIDAS, font=FUENTE_CUERPO)
        self.combo_profesion.pack(fill="x", pady=(0, 6))
        self.combo_profesion.set("Lcdo. en Educación")

        # Sub-panel de Foto (lado derecho de la tarjeta de form)
        f_foto_box = tk.Frame(f_cuerpo, bg=COLOR_TARJETA, width=160)
        f_foto_box.grid(row=0, column=1, sticky="ns")

        tk.Label(f_foto_box, text="Fotografía:", bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA).pack(anchor="center", pady=(0, 3))
        
        self.f_foto_container = tk.Frame(f_foto_box, width=110, height=110, bg="#EAECEE", relief="solid", bd=1)
        self.f_foto_container.pack_propagate(False)
        self.f_foto_container.pack(anchor="center", pady=(0, 6))

        self.lbl_foto = tk.Label(
            self.f_foto_container, text="[ SIN FOTO ]", bg="#EAECEE", fg=COLOR_TEXTO_SECUNDARIO,
            font=FUENTE_PEQUEÑA
        )
        self.lbl_foto.pack(fill="both", expand=True)

        f_foto_btns = tk.Frame(f_foto_box, bg=COLOR_TARJETA)
        f_foto_btns.pack(fill="x")
        f_foto_btns.columnconfigure(0, weight=1, uniform="btn_foto_prof")
        f_foto_btns.columnconfigure(1, weight=1, uniform="btn_foto_prof")

        self.btn_cargar_foto = crear_boton(
            f_foto_btns, "📷 Cargar", self.cargar_foto_click,
            COLOR_PRIMARIO, COLOR_TEXTO_CLARO, padx=6, pady=5,
        )
        self.btn_cargar_foto.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        AyudaVisual(self.btn_cargar_foto, "Cargar fotografía oficial del docente")

        self.btn_quitar_foto = crear_boton(
            f_foto_btns, "✖ Quitar", self.quitar_foto_click,
            "#7F8C8D", COLOR_TEXTO_CLARO, padx=6, pady=5,
        )
        self.btn_quitar_foto.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        AyudaVisual(self.btn_quitar_foto, "Remover la fotografía asignada")

        crear_separador(tarjeta_form).pack(fill="x", pady=(8, 8))

        # Botonera de Acciones en cuadrícula 2x2
        f_acciones = tk.Frame(tarjeta_form, bg=COLOR_TARJETA)
        f_acciones.pack(fill="x")
        f_acciones.columnconfigure(0, weight=1, uniform="btn_prof")
        f_acciones.columnconfigure(1, weight=1, uniform="btn_prof")

        self.btn_guardar = crear_boton(f_acciones, "💾  GUARDAR", self.guardar_click, COLOR_ACENTO, COLOR_TEXTO_CLARO, COLOR_ACENTO_HOVER, pady=6)
        self.btn_guardar.grid(row=0, column=0, sticky="ew", padx=4, pady=3)
        AyudaVisual(self.btn_guardar, "Registrar nuevo profesor con los datos ingresados")

        self.btn_actualizar = crear_boton(f_acciones, "📝  ACTUALIZAR", self.actualizar_click, COLOR_ADVERTENCIA, COLOR_TEXTO_CLARO, COLOR_ADVERTENCIA_HOVER, pady=6)
        self.btn_actualizar.grid(row=0, column=1, sticky="ew", padx=4, pady=3)
        AyudaVisual(self.btn_actualizar, "Actualizar los datos del docente seleccionado")

        self.btn_ficha = crear_boton(f_acciones, "🖨️  FICHA PDF", self.imprimir_ficha_click, "#2980B9", COLOR_TEXTO_CLARO, "#3498DB", pady=6)
        self.btn_ficha.grid(row=1, column=0, sticky="ew", padx=4, pady=3)
        AyudaVisual(self.btn_ficha, "Exportar Ficha Técnica Oficial del Docente en PDF")

        self.btn_limpiar = crear_boton(f_acciones, "🧹  LIMPIAR", self.limpiar_formulario, "#95A5A6", COLOR_TEXTO_CLARO, pady=6)
        self.btn_limpiar.grid(row=1, column=1, sticky="ew", padx=4, pady=3)
        AyudaVisual(self.btn_limpiar, "Limpiar formulario y deseleccionar registro")

        # ══════════════════════════════════════════════════════════════════
        # COLUMNA DERECHA: LISTADO DE PROFESORES REGISTRADOS
        # ══════════════════════════════════════════════════════════════════
        tarjeta_lista = crear_tarjeta(contenedor, padx=20, pady=20)
        tarjeta_lista.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(
            tarjeta_lista, text="DOCENTES REGISTRADOS",
            font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO
        ).pack(anchor="w", pady=(0, 5))
        self.lbl_subtitulo_lista = tk.Label(
            tarjeta_lista, text="Seleccione un docente para editarlo o imprimir su ficha oficial.",
            font=FUENTE_PEQUEÑA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SECUNDARIO,
            wraplength=380, justify="left"
        )
        self.lbl_subtitulo_lista.pack(anchor="w", pady=(0, 10))

        cols = ("id", "cedula", "nombre", "profesion")
        encabezados = ["ID", "Cédula", "Nombre del Profesor", "Profesión"]
        anchos = [40, 95, 180, 140]
        anclas = ["center", "center", "w", "w"]

        self.tree_prof, frame_tree = crear_treeview_zebra(
            tarjeta_lista, cols, encabezados, anchos, anclas, alto=14
        )
        frame_tree.pack(fill="both", expand=True)
        self.tree_prof.bind("<<TreeviewSelect>>", self.seleccionar_profesor_desde_tabla)

    # ──────────────────────────────────────────────────────────────
    # GESTIÓN DE FOTOGRAFÍA
    # ──────────────────────────────────────────────────────────────
    def _obtener_cedula_actual(self) -> str:
        ced_num = self.entry_ced_prof.get().strip()
        if not ced_num:
            return ""
        return f"{self.combo_nac_prof.get()}-{ced_num}".upper()

    def cargar_foto_click(self):
        parent = self.notebook.winfo_toplevel()
        cedula = self._obtener_cedula_actual()
        if not cedula:
            messagebox.showwarning("Atención", "Ingrese primero la cédula del profesor antes de cargar la foto.", parent=parent)
            restaurar_foco(self.notebook)
            self.entry_ced_prof.focus()
            return

        ruta_origen = filedialog.askopenfilename(
            parent=parent,
            title="Seleccionar fotografía del profesor",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Todos los archivos", "*.*")]
        )
        restaurar_foco(self.notebook)
        if not ruta_origen:
            return

        if not self.gestor_fotos:
            messagebox.showwarning("Aviso", "El gestor de fotografías no está disponible.", parent=parent)
            restaurar_foco(self.notebook)
            return

        try:
            ruta_rel = self.gestor_fotos.guardar_foto(ruta_origen, "profesor", cedula)
            self.foto_path_actual = ruta_rel
            self._mostrar_preview_foto(ruta_rel)
            messagebox.showinfo("Fotografía Cargada", "La fotografía se optimizó y guardó correctamente (240x240 px).", parent=parent)
        except Exception as e:
            messagebox.showerror("Error de Imagen", f"No se pudo procesar la fotografía: {e}", parent=parent)
        finally:
            restaurar_foco(self.notebook)

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
            top = self.notebook.winfo_toplevel()
            img_tk = self.gestor_fotos.cargar_preview_tk(ruta_foto, (110, 110), master=top)
            if img_tk:
                self.preview_foto_tk = img_tk
                self._foto_preview_ref = img_tk
                self.lbl_foto.image = img_tk
                self.lbl_foto.config(image=img_tk, text="")
                return

        self.quitar_foto_click()

    # ──────────────────────────────────────────────────────────────
    # CARGA Y SELECCIÓN EN TABLA
    # ──────────────────────────────────────────────────────────────
    def cargar_profesores_en_tabla(self):
        for item in self.tree_prof.get_children():
            self.tree_prof.delete(item)

        profesores = self.repositorio.obtener_activos()
        for p in profesores:
            insertar_fila_zebra(
                self.tree_prof,
                (p.id_profesor, p.cedula, p.nombre_completo, p.profesion or "Docente")
            )

    def seleccionar_profesor_desde_tabla(self, event=None):
        seleccion = self.tree_prof.selection()
        if not seleccion:
            return
        item = self.tree_prof.item(seleccion[0])
        valores = item["values"]
        id_prof = int(valores[0])

        prof = self.repositorio.obtener_por_id(id_prof)
        if not prof:
            return

        self.profesor_seleccionado = prof
        self.limpiar_campos_sin_seleccion()

        # Cédula
        if "-" in prof.cedula:
            partes = prof.cedula.split("-", 1)
            if partes[0] in ("V", "E", "P"):
                self.combo_nac_prof.set(partes[0])
            self.entry_ced_prof.insert(0, partes[1])
        else:
            self.entry_ced_prof.insert(0, prof.cedula)

        # Nombre y Profesión
        self.entry_nom_prof.insert(0, prof.nombre_completo)
        self.combo_profesion.set(prof.profesion or "Lcdo. en Educación")

        # Foto
        self.foto_path_actual = prof.foto_path or ""
        self._mostrar_preview_foto(self.foto_path_actual)

    # ──────────────────────────────────────────────────────────────
    # OPERACIONES CRUD Y ACCIONES
    # ──────────────────────────────────────────────────────────────
    def limpiar_campos_sin_seleccion(self):
        self.entry_ced_prof.delete(0, tk.END)
        self.entry_nom_prof.delete(0, tk.END)
        self.combo_profesion.set("Lcdo. en Educación")
        self.combo_nac_prof.current(0)
        self.quitar_foto_click()

    def limpiar_formulario(self):
        self.profesor_seleccionado = None
        self.limpiar_campos_sin_seleccion()
        if self.tree_prof.selection():
            self.tree_prof.selection_remove(self.tree_prof.selection())
        self.entry_ced_prof.focus()

    def guardar_click(self, event=None):
        parent = self.notebook.winfo_toplevel()
        cedula = self._obtener_cedula_actual()
        nombre = self.entry_nom_prof.get().strip().upper()
        profesion = self.combo_profesion.get().strip().upper()

        try:
            nuevo = Profesor(
                cedula=cedula,
                nombre_completo=nombre,
                profesion=profesion,
                foto_path=self.foto_path_actual
            )
            nuevo.validar()
            self.repositorio.guardar(nuevo)
            messagebox.showinfo("Éxito", f"Profesor '{nombre}' registrado correctamente.", parent=parent)
            self.limpiar_formulario()
            self.cargar_profesores_en_tabla()
        except ValueError as e:
            messagebox.showwarning("Dato Inválido", str(e), parent=parent)
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo completar la operación: {e}", parent=parent)
        finally:
            restaurar_foco(self.notebook)

    def actualizar_click(self, event=None):
        parent = self.notebook.winfo_toplevel()
        if not self.profesor_seleccionado:
            messagebox.showwarning("Atención", "Seleccione primero un profesor de la tabla para actualizar.", parent=parent)
            restaurar_foco(self.notebook)
            return

        cedula = self._obtener_cedula_actual()
        nombre = self.entry_nom_prof.get().strip().upper()
        profesion = self.combo_profesion.get().strip().upper()

        try:
            prof_actualizado = Profesor(
                cedula=cedula,
                nombre_completo=nombre,
                id_profesor=self.profesor_seleccionado.id_profesor,
                profesion=profesion,
                foto_path=self.foto_path_actual
            )
            prof_actualizado.validar()
            if self.repositorio.actualizar(prof_actualizado):
                messagebox.showinfo("Éxito", f"Expediente del profesor '{nombre}' actualizado.", parent=parent)
                self.limpiar_formulario()
                self.cargar_profesores_en_tabla()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el registro del profesor.", parent=parent)
        except ValueError as e:
            messagebox.showwarning("Dato Inválido", str(e), parent=parent)
        except Exception as e:
            messagebox.showerror("Error de Sistema", f"No se pudo completar la actualización: {e}", parent=parent)
        finally:
            restaurar_foco(self.notebook)

    def imprimir_ficha_click(self):
        """Genera y ofrece abrir la Ficha Técnica Oficial del Docente en PDF."""
        parent = self.notebook.winfo_toplevel()
        profesor = self.profesor_seleccionado

        if not profesor:
            cedula = self._obtener_cedula_actual()
            if cedula:
                profesor = self.repositorio.obtener_por_cedula(cedula)

        if not profesor:
            messagebox.showwarning("Atención", "Seleccione un docente de la lista para imprimir su ficha.", parent=parent)
            restaurar_foco(self.notebook)
            return

        if not self.exportador_pdf:
            messagebox.showerror("Error", "El servicio de exportación PDF no está disponible.", parent=parent)
            restaurar_foco(self.notebook)
            return

        # Consultar materias asignadas si el repositorio de clases está presente
        materias = []
        if self.repositorio_clase and profesor.id_profesor:
            try:
                materias = self.repositorio_clase.obtener_clases_por_profesor(profesor.id_profesor)
            except Exception:
                materias = []

        ced_limpia = str(profesor.cedula).replace("-", "_").replace(".", "")
        nombre_sugerido = f"Ficha_Docente_{ced_limpia}.pdf"
        ruta_salida = filedialog.asksaveasfilename(
            parent=parent,
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=nombre_sugerido,
            title="Guardar Ficha Técnica Docente"
        )
        restaurar_foco(self.notebook)
        if not ruta_salida:
            return

        try:
            ruta_pdf = self.exportador_pdf.generar_ficha_docente(profesor, materias, ruta_salida)
            if messagebox.askyesno(
                "Ficha Generada",
                f"Ficha oficial generada con éxito:\n{ruta_pdf}\n\n¿Desea abrir el archivo ahora?",
                parent=parent
            ):
                abrir_archivo_sistema(ruta_pdf)
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo generar la ficha PDF: {e}", parent=parent)
        finally:
            restaurar_foco(self.notebook)
