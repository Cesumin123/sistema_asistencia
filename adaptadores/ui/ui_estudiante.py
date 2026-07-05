import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry 
from datetime import datetime
import string

# Importamos tu clase de ayuda visual (si la moviste a utilidades, impórtala desde ahí)
#from utilidades_ui import AyudaVisual 

# --- Importaciones de la Arquitectura Hexagonal ---
from dominio.estudiante import Estudiante
from puertos.repositorio_estudiante import PuertoRepositorioEstudiante

# --- CLASE DE AYUDA VISUAL --- (La mantengo aquí por si no la tienes en otro archivo)
class AyudaVisual:
    """
    Esta clase crea pequeños carteles amarillos (Tooltips)
    que aparecen cuando pasas el mouse por encima de una caja.
    Sirven para guiar al usuario.
    """
    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self.ventana_ayuda = None
        self.widget.bind("<Enter>", self.mostrar_cartel)
        self.widget.bind("<Leave>", self.ocultar_cartel)

    def mostrar_cartel(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.ventana_ayuda = tk.Toplevel(self.widget)
        self.ventana_ayuda.wm_overrideredirect(True) 
        self.ventana_ayuda.wm_geometry(f"+{x}+{y}")
        
        etiqueta = tk.Label(self.ventana_ayuda, text=self.texto, background="#ffffe0", 
                         relief="solid", borderwidth=1, font=("Arial", 8))
        etiqueta.pack()

    def ocultar_cartel(self, event=None):
        if self.ventana_ayuda:
            self.ventana_ayuda.destroy()
            self.ventana_ayuda = None

# --- CLASE PRINCIPAL DEL GESTOR (ADAPTADOR UI) ---
class UIEstudiante:
    """
    Adaptador de Interfaz de Usuario para el módulo de Estudiantes.
    Solo interactúa con el Dominio a través del Puerto (Repositorio).
    """
    def __init__(self, repositorio: PuertoRepositorioEstudiante):
        # Inyección de dependencias
        self.repositorio = repositorio
        
        self.root = tk.Toplevel()
        self.root.title("Gestión Profesional de Estudiantes")
        self.root.geometry("1150x780")
        self.root.state('zoomed') 
        
        self.cedula_seleccionada = None 
        
        # 1. Diccionario de Traducción (Letra de Sección a ID numérico)
        self.mapa_secciones = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9, "J": 10, "K": 11, "L": 12, "M": 13, "N": 14, "O": 15, "P": 16, "Q": 17, "R": 18, "S": 19, "T": 20, "U": 21, "V": 22, "W": 23, "X": 24, "Y": 25, "Z": 26}
        # Mapa inverso (ID a Letra) para cuando cargamos datos a la tabla
        self.mapa_secciones_inverso = {v: k for k, v in self.mapa_secciones.items()}

        # 2. Dibujamos los campos y botones
        self.crear_interfaz()
        # 3. Llenamos la tabla pidiendo datos al repositorio
        self.cargar_datos()

    def crear_interfaz(self):
        """Dibuja la interfaz visual (IDÉNTICA A LA TUYA)"""
        frame_form = tk.Frame(self.root, pady=10, padx=10, bg="#f0f0f0", relief="groove", bd=2)
        frame_form.pack(fill="x", padx=10, pady=10)
        
        tk.Label(frame_form, text="FICHA TÉCNICA DEL ESTUDIANTE", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        # Variables Tkinter
        self.var_nac = tk.StringVar(value="V")
        self.var_genero = tk.StringVar(value="M")
        self.var_seccion = tk.StringVar(value="A")
        self.var_escolaridad = tk.StringVar(value="Regular")
        self.var_turno = tk.StringVar(value="Mañana")
        self.var_condicion = tk.StringVar(value="Activo")
        
        # --- FILA 1 ---
        f1 = tk.Frame(frame_form, bg="#f0f0f0"); f1.pack(pady=5)
        tk.Label(f1, text="Cédula:", bg="#f0f0f0").pack(side="left")
        self.combo_nac = ttk.Combobox(f1, textvariable=self.var_nac, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac.pack(side="left")
        self.entry_cedula = tk.Entry(f1, width=15)
        self.entry_cedula.pack(side="left", padx=(5, 20))
        AyudaVisual(self.entry_cedula, "Escribe el número de cédula sin puntos.")

        tk.Label(f1, text="Nombre Completo:", bg="#f0f0f0").pack(side="left")
        self.entry_nombre = tk.Entry(f1, width=35)
        self.entry_nombre.pack(side="left", padx=(5, 20))
        self.entry_nombre.bind("<KeyRelease>", self.convertir_mayus) 
        AyudaVisual(self.entry_nombre, "Nombre y Apellido del estudiante.")
        
        tk.Label(f1, text="Género:", bg="#f0f0f0").pack(side="left")
        self.combo_genero = ttk.Combobox(f1, textvariable=self.var_genero, values=["M", "F"], width=4, state="readonly")
        self.combo_genero.pack(side="left")
        AyudaVisual(self.combo_genero, "Selecciona M (Masculino) o F (Femenino).")

        # --- FILA 2 ---
        f2 = tk.Frame(frame_form, bg="#f0f0f0"); f2.pack(pady=5)
        tk.Label(f2, text="Fecha Nacimiento:", bg="#f0f0f0").pack(side="left")
        self.calendario = DateEntry(f2, width=12, date_pattern='dd/mm/y', locale='es_ES', background='darkblue')
        self.calendario.pack(side="left", padx=(5, 20))
        AyudaVisual(self.calendario, "Haz clic para elegir el cumpleaños.")
        
        tk.Label(f2, text="Año Escolar (1-5):", bg="#f0f0f0").pack(side="left")
        self.entry_grado = tk.Entry(f2, width=5)
        self.entry_grado.pack(side="left", padx=(5, 20))
        AyudaVisual(self.entry_grado, "Escribe solo el número del año (Ej: 1).")
        
        tk.Label(f2, text="Sección:", bg="#f0f0f0").pack(side="left")
        self.combo_seccion = ttk.Combobox(f2, textvariable=self.var_seccion, values=list(string.ascii_uppercase), width=4, state="readonly")
        self.combo_seccion.pack(side="left")
        AyudaVisual(self.combo_seccion, "La letra de la sección.")

        # --- FILA 3 ---
        f3 = tk.Frame(frame_form, bg="#f0f0f0"); f3.pack(pady=5)
        tk.Label(f3, text="Representante:", bg="#f0f0f0", fg="#2980b9").pack(side="left")
        self.entry_repre = tk.Entry(f3, width=35)
        self.entry_repre.pack(side="left", padx=(5, 20))
        self.entry_repre.bind("<KeyRelease>", self.convertir_mayus)
        AyudaVisual(self.entry_repre, "Nombre de mamá, papá o tutor.")
        
        tk.Label(f3, text="Teléfono:", bg="#f0f0f0", fg="#2980b9").pack(side="left")
        self.entry_telf = tk.Entry(f3, width=15)
        self.entry_telf.pack(side="left")
        AyudaVisual(self.entry_telf, "Número para llamar en emergencias.")

        # --- FILA 4 ---
        f4 = tk.Frame(frame_form, bg="#e8f8f5", pady=5, padx=5, relief="flat") 
        f4.pack(pady=10)
        
        tk.Label(f4, text="Escolaridad:", bg="#e8f8f5").pack(side="left")
        self.combo_escolaridad = ttk.Combobox(f4, textvariable=self.var_escolaridad, 
                                            values=["Regular", "Materia Pendiente", "Repite"], 
                                            width=15, state="readonly")
        self.combo_escolaridad.pack(side="left", padx=(2, 20))
        AyudaVisual(self.combo_escolaridad, "¿Pasó todo, debe materias o repite año?")

        tk.Label(f4, text="Turno:", bg="#e8f8f5").pack(side="left")
        self.combo_turno = ttk.Combobox(f4, textvariable=self.var_turno, 
                                      values=["Mañana", "Tarde"], 
                                      width=10, state="readonly")
        self.combo_turno.pack(side="left", padx=(2, 20))
        AyudaVisual(self.combo_turno, "¿En qué horario estudia?")

        tk.Label(f4, text="Condición:", bg="#e8f8f5").pack(side="left")
        self.combo_condicion = ttk.Combobox(f4, textvariable=self.var_condicion, 
                                          values=["Activo", "Preinscrito"], 
                                          width=12, state="readonly")
        self.combo_condicion.pack(side="left", padx=(2, 20))
        AyudaVisual(self.combo_condicion, "¿Ya es alumno oficial o está en proceso?")

        # --- BOTONERA ---
        f_btns = tk.Frame(self.root); f_btns.pack(pady=10)
        
        tk.Button(f_btns, text="💾 GUARDAR", bg="#27ae60", fg="white", font=("bold"), 
                  command=self.guardar_nuevo).pack(side="left", padx=10)
        tk.Button(f_btns, text="📝 MODIFICAR", bg="#f39c12", fg="white", font=("bold"), 
                  command=self.modificar_existente).pack(side="left", padx=10)
        tk.Button(f_btns, text="🗑️ ELIMINAR", bg="#c0392b", fg="white", font=("bold"), 
                  command=self.eliminar_estudiante).pack(side="left", padx=10)
        tk.Button(f_btns, text="🧹 Limpiar", command=self.limpiar_formulario).pack(side="left", padx=10)

        # --- TABLA DE DATOS ---
        cols = ("cedula", "nombre", "nac", "repre", "telf", "gen", "esc", "tur", "cond", "anio", "sec")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        
        headers = ["Cédula", "Nombre", "F. Nac", "Representante", "Telf", "Sx", "Escolaridad", "Turno", "Cond", "Año", "Sec"]
        widths = [90, 200, 80, 150, 90, 30, 90, 60, 60, 40, 40]
        
        for i, col in enumerate(cols):
            self.tree.heading(col, text=headers[i])
            self.tree.column(col, width=widths[i])
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.cargar_formulario_desde_tabla)

    # ---------------- HERRAMIENTAS ÚTILES ----------------
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

    # ---------------- LÓGICA DE CONEXIÓN CON EL DOMINIO ----------------

    def _obtener_entidad_desde_formulario(self) -> Estudiante:
        """Extrae los datos, hace la traducción y devuelve un objeto Estudiante."""
        nac = self.combo_nac.get()
        num = self.entry_cedula.get().strip()
        nombre = self.entry_nombre.get().strip()
        grado_str = self.entry_grado.get().strip()
        seccion_letra = self.combo_seccion.get()
        
        # Validaciones muy básicas de UI (para que no falle la creación del objeto)
        if not num or not nombre or not grado_str:
            raise ValueError("La Cédula, Nombre y Año Escolar son campos obligatorios.")
        
        try:
            grado = int(grado_str)
        except ValueError:
            raise ValueError("El Año Escolar debe ser un número (Ej: 1, 2, 3).")

        # --- TRADUCCIÓN: De letra a ID ---
        # Si la letra no está en el diccionario, por defecto ponemos 1
        id_seccion_traducido = self.mapa_secciones.get(seccion_letra, 1)

        estudiante = Estudiante(
            cedula=f"{nac}-{num}",
            nombre=nombre,
            fecha_nacimiento=self.calendario.get_date().strftime('%d/%m/%Y'), # Formato de fecha
            representante=self.entry_repre.get().strip(),
            telefono=self.entry_telf.get().strip(),
            genero=self.combo_genero.get(),
            escolaridad=self.combo_escolaridad.get(),
            turno=self.combo_turno.get(),
            condicion=self.combo_condicion.get(),
            id_grado=grado,
            id_seccion=id_seccion_traducido 
        )
        return estudiante

    def cargar_datos(self):
        """Pide los datos al repositorio (Dominio) y los dibuja."""
        for item in self.tree.get_children(): 
            self.tree.delete(item)
            
        estudiantes = self.repositorio.obtener_todos_activos()
        
        for est in estudiantes:
            # --- TRADUCCIÓN INVERSA: De ID a letra para mostrar en la tabla ---
            letra_seccion = self.mapa_secciones_inverso.get(est.id_seccion, "A")

            valores = (est.cedula, est.nombre, est.fecha_nacimiento, est.representante, 
                       est.telefono, est.genero, est.escolaridad, est.turno, 
                       est.condicion, est.id_grado, letra_seccion)
            self.tree.insert("", "end", values=valores)

    def cargar_formulario_desde_tabla(self, event):
        """Rellena las cajas de texto cuando se selecciona un alumno de la tabla."""
        seleccion = self.tree.selection()
        if not seleccion: return
        
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
        
        # Ajuste para tkcalendar: Manejar la fecha (depende del formato que guardes)
        try:
             # Asumimos que guardamos en formato 'dd/mm/yyyy'
             fecha_obj = datetime.strptime(valores[2], '%d/%m/%Y').date()
             self.calendario.set_date(fecha_obj)
        except (ValueError, TypeError):
             pass # Si hay un error con el formato de fecha, simplemente no la llenamos
            
        self.entry_repre.insert(0, valores[3] or "")
        self.entry_telf.insert(0, str(valores[4]) if valores[4] else "") # Aseguramos que sea string
        self.combo_genero.set(valores[5])
        
        self.combo_escolaridad.set(valores[6] or "Regular")
        self.combo_turno.set(valores[7] or "Mañana")
        self.combo_condicion.set(valores[8] or "Activo")
        
        self.entry_grado.insert(0, str(valores[9]))
        self.combo_seccion.set(str(valores[10]))

    # ---------------- FUNCIONES DE GUARDADO (Ahora usando el Repositorio) ----------------

    def guardar_nuevo(self):
        try:
            nuevo_estudiante = self._obtener_entidad_desde_formulario()
            nuevo_estudiante.validar()
            
            if self.repositorio.guardar(nuevo_estudiante):
                messagebox.showinfo("Éxito", "Estudiante registrado correctamente.")
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo guardar. Verifica que la cédula no esté duplicada.")
                
        except ValueError as e:
            messagebox.showwarning("Faltan Datos o Error", str(e))

    def modificar_existente(self):
        if not self.cedula_seleccionada:
            messagebox.showwarning("Ojo", "Primero toca un estudiante en la lista de abajo.")
            return

        try:
            estudiante_modificado = self._obtener_entidad_desde_formulario()
            # IMPORTANTE: Forzamos la cédula seleccionada por seguridad
            estudiante_modificado.cedula = self.cedula_seleccionada
            estudiante_modificado.validar()
            
            if self.repositorio.actualizar(estudiante_modificado):
                messagebox.showinfo("Éxito", "Datos actualizados correctamente.")
                self.limpiar_formulario()
                self.cargar_datos()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el registro en la base de datos.")
                
        except ValueError as e:
            messagebox.showwarning("Error en los datos", str(e))

    def eliminar_estudiante(self):
        if not self.cedula_seleccionada:
            messagebox.showwarning("Ojo", "Selecciona un estudiante para borrar.")
            return
        
        confirm = messagebox.askyesno("Confirmar", f"¿Seguro que quieres borrar a {self.cedula_seleccionada}?")
        if not confirm: return

        if self.repositorio.eliminar(self.cedula_seleccionada):
            messagebox.showinfo("Listo", "Estudiante borrado (borrado lógico).")
            self.limpiar_formulario()
            self.cargar_datos()
        else:
            messagebox.showerror("Error", "Hubo un problema al intentar eliminar al estudiante.")