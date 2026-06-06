# adaptadores/ui/ui_profesor.py
import tkinter as tk
from tkinter import ttk, messagebox
from dominio.profesor import Profesor
from adaptadores.ui.utilidades_ui import AyudaVisual, enfocar_siguiente
from PIL import Image, ImageTk

class GestorProfesoresUI:
    """
    Adaptador de Interfaz de Usuario (UI) para la entidad Profesor.
    
    Esta clase actúa como un puente entre el usuario y la lógica de negocio,
    implementando la capa de presentación mediante la librería Tkinter.
    Se encarga de la captura de datos, validación visual y la interacción
    con el repositorio de persistencia.
    """

    def __init__(self, parent_notebook, repositorio_profesor):
        """
        Inicializa la interfaz del gestor de profesores.

        Args:
            parent_notebook (ttk.Notebook): El contenedor de pestañas principal de la aplicación.
            repositorio_profesor (RepositorioProfesor): Adaptador de persistencia inyectado 
                para realizar operaciones sobre la base de datos.
        """
        self.notebook = parent_notebook
        self.repositorio = repositorio_profesor
        
        # Construcción de los elementos visuales
        self.crear_tab()
        
        # Maximiza la ventana principal para asegurar la correcta visualización del fondo
        self.notebook.master.state('zoomed')

    def convertir_mayus(self, event):
        """
        Transforma dinámicamente el contenido de un widget de entrada a letras mayúsculas.

        Args:
            event (tk.Event): Evento de teclado que dispara la función.
        """
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            # Guarda la posición actual del cursor para evitar que salte al inicio
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            # Restaura la posición del cursor después de la modificación
            widget.icursor(pos)

    def crear_tab(self):
        """
        Configura y ensambla todos los componentes visuales de la pestaña de registro.
        
        Incluye la carga de recursos gráficos, definición de campos de entrada,
        configuración de eventos (binds) y herramientas de ayuda visual (tooltips).
        """
        # Creación del marco contenedor de la pestaña
        tab = tk.Frame(self.notebook, bg="#e8f8f5") 

        # --- GESTIÓN DEL FONDO GRÁFICO ---
        try:
            # Carga y redimensionamiento de la imagen corporativa
            imagen_original = Image.open("LOGOLICEO.png")
            imagen_redimensionada = imagen_original.resize((600, 400))
            self.img_fondo_tk = ImageTk.PhotoImage(imagen_redimensionada)
            
            # Label posicionado de forma absoluta para actuar como fondo
            lbl_fondo = tk.Label(tab, image=self.img_fondo_tk, bd=0)
            lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            # En caso de error de carga, se registra en consola pero no interrumpe el flujo
            print(f"Error al cargar recurso gráfico: {e}")

        # Agrega la pestaña al cuaderno principal
        self.notebook.add(tab, text="  👨‍🏫  REGISTRAR PROFESOR  ")
        
        # Marco central para organizar los controles de entrada
        frame = tk.Frame(tab, bg="#e8f8f5")
        frame.pack(pady=30)
        
        # --- SECCIÓN: CÉDULA DE IDENTIDAD ---
        tk.Label(frame, text="Cédula de Identidad:", bg="#ffffff", font=("Arial", 10)).pack()
        f_ced = tk.Frame(frame, bg="#fff3f3")
        f_ced.pack()
        
        # Selector de nacionalidad (Prefijo de cédula)
        self.combo_nac_prof = ttk.Combobox(f_ced, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac_prof.pack(side="left")
        self.combo_nac_prof.current(0)
        AyudaVisual(self.combo_nac_prof, "Seleccione la nacionalidad del profesor.")

        # Campo numérico para la cédula
        self.entry_ced_prof = tk.Entry(f_ced, width=15)
        self.entry_ced_prof.pack(side="left", padx=5)
        self.entry_ced_prof.bind("<Return>", enfocar_siguiente)
        AyudaVisual(self.entry_ced_prof, "Ingrese solo números. Ej: 12345678")
        
        # --- SECCIÓN: NOMBRE DEL PROFESOR ---
        tk.Label(frame, text="Nombre Completo:", bg="#e8f8f5", font=("Arial", 10)).pack(pady=(15, 0))
        
        self.entry_nom_prof = tk.Entry(frame, width=35)
        self.entry_nom_prof.pack()
        # Vinculación de eventos para normalización automática a mayúsculas
        self.entry_nom_prof.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_prof.bind("<Return>", enfocar_siguiente)
        AyudaVisual(self.entry_nom_prof, "Ingrese el nombre completo del profesor.")
        
        # --- SECCIÓN: ACCIÓN DE GUARDADO ---
        btn_guardar = tk.Button(frame, text="GUARDAR PROFESOR", bg="#16a085", fg="white",
                   font=("Arial", 10, "bold"), command=self.guardar_click)
        btn_guardar.pack(pady=25)
        btn_guardar.bind("<Return>", self.guardar_click)
        AyudaVisual(btn_guardar, "Haz clic para guardar el profesor en la base de datos.")

    def guardar_click(self, event=None):
        """
        Procesa la recolección de datos, instanciación del dominio y persistencia.

        Captura la información de los widgets, formatea los datos, solicita la 
        validación de reglas de negocio al dominio y finalmente delega el 
        almacenamiento al repositorio.

        Args:
            event (tk.Event, opcional): Captura el evento de teclado si se presiona 'Enter'.
        """
        # Extracción y limpieza básica de entradas
        nombre = self.entry_nom_prof.get().strip().upper()
        ced_num = self.entry_ced_prof.get().strip()
        cedula = f"{self.combo_nac_prof.get()}-{ced_num}"

        try:
            # Instanciación del objeto de Dominio (Entidad Pura)
            nuevo_profesor = Profesor(cedula=cedula, nombre_completo=nombre)
            
            # Validación de reglas de negocio (Lógica interna del dominio)
            nuevo_profesor.validar()
            
            # Persistencia a través del adaptador de infraestructura (Inyectado)
            self.repositorio.guardar(nuevo_profesor)
            
            # Retroalimentación al usuario
            messagebox.showinfo("Éxito", f"Profesor {nombre} registrado correctamente.")
            
            # Limpieza de los campos del formulario
            self.entry_ced_prof.delete(0, tk.END)
            self.entry_nom_prof.delete(0, tk.END)
            self.entry_ced_prof.focus()

        except ValueError as e:
            # Captura errores de validación de reglas de negocio
            messagebox.showwarning("Dato Inválido", str(e))
        except Exception as e:
            # Captura errores técnicos (ej. pérdida de conexión a BD)
            messagebox.showerror("Error de Sistema", f"No se pudo completar la operación: {e}")
