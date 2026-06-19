import tkinter as tk
from tkinter import ttk, messagebox
from db_conexion import ConexionBD  # Importa la clase de conexión a la base de datos creada anteriormente.
import sqlite3  # Importa la librería para manejar la base de datos SQLite.

class GestorAcademico:
    """
    Módulo para la gestión de profesores y la asignación de materias.
    Permite registrar docentes, aplicar borrado lógico y asignar cargas académicas.
    """

    def __init__(self):
        # --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ---
        self.root = tk.Toplevel()                           # Crea una ventana secundaria flotante.
        self.root.title("Gestión Académica Integral")       # Título de la ventana.
        self.root.geometry("650x600")                       # Dimensiones iniciales.
        self.root.state('zoomed')                           # Maximiza la ventana al abrirse.
        
        # --- CREACIÓN DEL SISTEMA DE PESTAÑAS ---
        self.notebook = ttk.Notebook(self.root)             # Contenedor para las múltiples pestañas.
        self.notebook.pack(pady=10, fill="both", expand=True) # Expande el contenedor en la ventana.
        
        # Construye la primera pestaña: Gestión de profesores.
        self.crear_tab_profesores()
        # Construye la segunda pestaña: Asignación de materias.
        self.crear_tab_materias()

    def convertir_mayus(self, event):
        """
        Evento que convierte el texto ingresado en un campo a mayúsculas en tiempo real.
        Evita inconsistencias en la base de datos.
        """
        widget = event.widget                               # Obtiene el campo de texto que activó el evento.
        texto = widget.get()                                # Obtiene el texto actual del campo.
        widget.delete(0, tk.END)                            # Borra el contenido actual.
        widget.insert(0, texto.upper())                     # Inserta el mismo texto convertido a mayúsculas.

    # ==========================================
    # MÓDULO DE PROFESORES
    # ==========================================

    def crear_tab_profesores(self):
        """Construye la interfaz visual para registrar y listar profesores."""
        self.tab_prof = ttk.Frame(self.notebook)            # Crea el contenedor de la pestaña.
        self.notebook.add(self.tab_prof, text="Profesores") # Añade el contenedor al notebook con un título.

        # --- FORMULARIO DE REGISTRO ---
        frame_form = tk.LabelFrame(self.tab_prof, text="Registrar Nuevo Profesor")
        frame_form.pack(padx=10, pady=10, fill="x")         # fill="x" hace que ocupe todo el ancho.

        tk.Label(frame_form, text="Cédula:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_cedula = tk.Entry(frame_form)
        self.entry_cedula.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame_form, text="Nombre Completo:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_nombre = tk.Entry(frame_form, width=40)
        self.entry_nombre.grid(row=0, column=3, padx=5, pady=5)
        
        # Vincula el evento de escritura (KeyRelease) a la función de mayúsculas.
        self.entry_nombre.bind("<KeyRelease>", self.convertir_mayus)

        btn_guardar = tk.Button(frame_form, text="Guardar", bg="green", fg="white", command=self.guardar_profesor)
        btn_guardar.grid(row=0, column=4, padx=10, pady=5)

        # --- TABLA DE DATOS (TREEVIEW) ---
        # Se definen las columnas que mostrará la tabla.
        columnas = ("ID", "Cédula", "Nombre", "Estado")
        self.tree_prof = ttk.Treeview(self.tab_prof, columns=columnas, show="headings")
        
        # Configura los encabezados y anchos de columna.
        self.tree_prof.heading("ID", text="ID")
        self.tree_prof.column("ID", width=30)
        self.tree_prof.heading("Cédula", text="Cédula")
        self.tree_prof.column("Cédula", width=100)
        self.tree_prof.heading("Nombre", text="Nombre")
        self.tree_prof.column("Nombre", width=300)
        self.tree_prof.heading("Estado", text="Estado")
        self.tree_prof.column("Estado", width=80)
        
        self.tree_prof.pack(padx=10, pady=10, fill="both", expand=True)

        # --- BOTÓN DE BORRADO LÓGICO ---
        btn_eliminar = tk.Button(self.tab_prof, text="Desactivar Profesor", bg="red", fg="white", command=self.eliminar_profesor)
        btn_eliminar.pack(pady=5)

        # Llama a la función para llenar la tabla al abrir la ventana.
        self.cargar_profesores()

    def cargar_profesores(self):
        """
        Consulta la base de datos y llena el Treeview de profesores.
        MODIFICACIÓN: Solo selecciona registros con ESTADO = 'ACTIVO'.
        """
        # Limpia las filas existentes en la tabla antes de cargar nuevas.
        for fila in self.tree_prof.get_children():
            self.tree_prof.delete(fila)

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # La cláusula WHERE ESTADO = 'ACTIVO' oculta a los profesores "eliminados".
                cursor.execute("SELECT ID_PROFESOR, CEDULA, NOMBRE_COMPLETO, ESTADO FROM TBL_PROFESORES WHERE ESTADO = 'ACTIVO'")
                profesores = cursor.fetchall()
                
                # Inserta cada registro obtenido en el Treeview visual.
                for prof in profesores:
                    self.tree_prof.insert("", "end", values=prof)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar datos: {e}")
            finally:
                db.cerrar()

    def guardar_profesor(self):
        """Inserta un nuevo profesor en la base de datos."""
        cedula = self.entry_cedula.get().strip()            # .strip() elimina espacios en blanco accidentales.
        nombre = self.entry_nombre.get().strip()

        # Validación básica para asegurar que no falten datos.
        if not cedula or not nombre:
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
            return

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Inserta el registro. La base de datos asignará 'ACTIVO' automáticamente por defecto.
                cursor.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO) VALUES (?, ?)", (cedula, nombre))
                conn.commit()                               # Confirma los cambios en SQLite.
                messagebox.showinfo("Éxito", "Profesor registrado correctamente.")
                
                # Limpia los campos de texto tras guardar.
                self.entry_cedula.delete(0, tk.END)
                self.entry_nombre.delete(0, tk.END)
                
                # Recarga la tabla para mostrar al nuevo profesor.
                self.cargar_profesores()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Ya existe un profesor con esa cédula.")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un problema: {e}")
            finally:
                db.cerrar()

    def eliminar_profesor(self):
        """
        Ejecuta el Borrado Lógico del profesor seleccionado.
        MODIFICACIÓN: Cambia UPDATE en lugar de DELETE.
        """
        seleccion = self.tree_prof.selection()              # Obtiene la fila seleccionada en el Treeview.
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un profesor de la lista.")
            return

        # Pide confirmación al usuario antes de proceder.
        confirmacion = messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este profesor del listado principal?")
        if not confirmacion:
            return

        # Extrae los datos de la fila seleccionada.
        item = self.tree_prof.item(seleccion[0])
        id_profesor = item['values'][0]                     # El ID_PROFESOR está en la primera columna (índice 0).

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # El borrado lógico: Actualiza el estado a INACTIVO en lugar de destruir el registro.
                cursor.execute("UPDATE TBL_PROFESORES SET ESTADO = 'INACTIVO' WHERE ID_PROFESOR = ?", (id_profesor,))
                conn.commit()
                messagebox.showinfo("Éxito", "Profesor eliminado lógicamente.")
                
                # Refresca la tabla. Como cargamos solo 'ACTIVO', este profesor ya no aparecerá.
                self.cargar_profesores()
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un problema al eliminar: {e}")
            finally:
                db.cerrar()

    # ==========================================
    # MÓDULO DE MATERIAS
    # ==========================================

    def crear_tab_materias(self):
        """Construye la interfaz para asignar materias a profesores."""
        self.tab_mat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mat, text="Asignar Materias")
        
        # Este frame contendrá los controles de asignación.
        frame_form = tk.LabelFrame(self.tab_mat, text="Formulario de Asignación")
        frame_form.pack(padx=10, pady=10, fill="both", expand=True)

        tk.Label(frame_form, text="Nombre de la Materia:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_materia = tk.Entry(frame_form, width=30)
        self.entry_materia.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.entry_materia.bind("<KeyRelease>", self.convertir_mayus)

        # Menú desplegable (Combobox) para seleccionar al profesor.
        tk.Label(frame_form, text="Profesor:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combo_profesores = ttk.Combobox(frame_form, state="readonly", width=40)
        self.combo_profesores.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Menú desplegable para seleccionar el grado escolar.
        tk.Label(frame_form, text="Grado / Año:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.combo_grados = ttk.Combobox(frame_form, state="readonly", width=20)
        self.combo_grados.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Lista múltiple (Listbox) para seleccionar varias secciones a la vez.
        tk.Label(frame_form, text="Secciones:").grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.listbox_secciones = tk.Listbox(frame_form, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.listbox_secciones.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        btn_guardar_mat = tk.Button(frame_form, text="Guardar Asignaciones", bg="blue", fg="white", command=self.guardar_materia)
        btn_guardar_mat.grid(row=4, column=0, columnspan=2, pady=15)

        # Llama a las funciones que traen los datos de la base de datos para rellenar los desplegables.
        self.cargar_listas_desplegables()

    def cargar_listas_desplegables(self):
        """Llena los Combobox de profesores y grados, y la Listbox de secciones."""
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Carga profesores activos.
                cursor.execute("SELECT ID_PROFESOR, NOMBRE_COMPLETO FROM TBL_PROFESORES WHERE ESTADO = 'ACTIVO'")
                profesores = cursor.fetchall()
                # Formatea los datos para mostrar "ID - Nombre" en el Combobox.
                self.combo_profesores['values'] = [f"{p[0]} - {p[1]}" for p in profesores]

                # Carga grados.
                cursor.execute("SELECT ID_GRADO, DESCRIPCION FROM TBL_GRADOS")
                grados = cursor.fetchall()
                self.combo_grados['values'] = [f"{g[0]} - {g[1]}" for g in grados]

                # Carga secciones.
                cursor.execute("SELECT DESCRIPCION FROM TBL_SECCIONES")
                secciones = cursor.fetchall()
                self.listbox_secciones.delete(0, tk.END)
                for s in secciones:
                    self.listbox_secciones.insert(tk.END, s[0])
                    
            except Exception as e:
                print(f"Error cargando listas: {e}")
            finally:
                db.cerrar()

    def guardar_materia(self):
        """Asigna una materia a un profesor para un grado y secciones específicas."""
        materia = self.entry_materia.get().strip()
        prof_seleccionado = self.combo_profesores.get()
        grado_seleccionado = self.combo_grados.get()
        indices_secciones = self.listbox_secciones.curselection()

        # Verifica que todos los campos y listas tengan una selección.
        if not materia or not prof_seleccionado or not grado_seleccionado or not indices_secciones:
            messagebox.showerror("Error", "Faltan datos. Complete el formulario y seleccione al menos una sección.")
            return

        # Extrae los IDs de las cadenas de texto (ej. "1 - Juan Pérez" -> "1").
        id_prof = int(prof_seleccionado.split(" - ")[0])
        id_grado = int(grado_seleccionado.split(" - ")[0])

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                contador = 0
                
                # Bucle para insertar un registro por cada sección seleccionada en la Listbox.
                for idx in indices_secciones:
                    letra = self.listbox_secciones.get(idx)
                    
                    # Consulta el ID_SECCION correspondiente a la letra (ej. 'A').
                    cursor.execute("SELECT ID_SECCION FROM TBL_SECCIONES WHERE DESCRIPCION = ?", (letra,))
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        id_sec = resultado[0]
                        # Inserta la nueva clase.
                        sql = "INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (?, ?, ?, ?)"
                        cursor.execute(sql, (materia, id_prof, id_grado, id_sec))
                        contador += 1
                
                conn.commit()
                messagebox.showinfo("Éxito", f"Se creó la materia '{materia}' para {contador} secciones.")
                
                # Cierra la ventana tras asignar con éxito.
                self.root.destroy()
            except Exception as err:
                messagebox.showerror("Error Base de Datos", str(err))
            finally: 
                db.cerrar()

# Bloque de ejecución principal para probar esta ventana de forma independiente.
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Oculta la ventana raíz base de Tkinter.
    app = GestorAcademico()
    root.mainloop()