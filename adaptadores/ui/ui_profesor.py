# adaptadores/ui/ui_profesor.py
import tkinter as tk
from tkinter import ttk, messagebox
from dominio.profesor import Profesor
from adaptadores.ui.utilidades_ui import AyudaVisual, enfocar_siguiente
from PIL import Image, ImageTk

class GestorProfesoresUI:
    """
    Adaptador de Interfaz. Solo se encarga de dibujar y capturar clics.
    """
    # Inyección de dependencias: Recibimos el repositorio (BD) ya configurado
    def __init__(self, parent_notebook, repositorio_profesor):
        self.notebook = parent_notebook
        self.repositorio = repositorio_profesor
        self.crear_tab()
        # ampliamos la ventana al maximo para que se vea el fondo completo
        self.notebook.master.state('zoomed')
    def convertir_mayus(self, event):
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.index(pos)

    def crear_tab(self):
        tab = tk.Frame(self.notebook, bg="#ffffff") 
        # agregamos imagen de fondo al tab
        # --- CÓDIGO DE FONDO ---
        try:
            # 1. Abrimos la imagen original
            imagen_original = Image.open("LOGOLICEO.png")
            
            # 2. La redimensionamos al tamaño aproximado de tu ventana
            imagen_redimensionada = imagen_original.resize((600, 400))
            
            # 3. La convertimos para que Tkinter la entienda
            self.img_fondo_tk = ImageTk.PhotoImage(imagen_redimensionada)
            
            # 4. La ponemos en un Label sin bordes
            lbl_fondo = tk.Label(tab, image=self.img_fondo_tk, bd=0)
            
            # 5. El truco maestro: .place() la pega al fondo y la estira
            lbl_fondo.place(x=0, y=80, relwidth=1, relheight=1)
        except Exception as e:
            print(f"No se pudo cargar el fondo: {e}")

        self.notebook.add(tab, text="  👨‍🏫  REGISTRAR PROFESOR  ")
        
        frame = tk.Frame(tab, bg="#ffffff"); frame.pack(pady=30)
        
        tk.Label(frame, text="Cédula de Identidad:", bg="#ffffff", font=("Arial", 10)).pack()
        f_ced = tk.Frame(frame, bg="#ffffff"); f_ced.pack()
        
        self.combo_nac_prof = ttk.Combobox(f_ced, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac_prof.pack(side="left"); self.combo_nac_prof.current(0)
        # implementamos un tooltip para el combo de nacionalidad
        AyudaVisual(self.combo_nac_prof, "Seleccione la nacionalidad del profesor.")

        # caja de texto de la cedula
        self.entry_ced_prof = tk.Entry(f_ced, width=15)
        # Solo permitimos números en la cédula
        self.entry_ced_prof.pack(side="left", padx=5)
        # Enfocamos el siguiente campo al presionar Enter
        self.entry_ced_prof.bind("<Return>", enfocar_siguiente)
        # implementamos un tooltip para la cédula
        AyudaVisual(self.entry_ced_prof, "Ingrese solo números. Ej: 12345678")
        
        tk.Label(frame, text="Nombre Completo:", bg="#ffffff", font=("Arial", 10)).pack(pady=(15, 0))
        
        # caja de texto del nombre completo
        self.entry_nom_prof = tk.Entry(frame, width=35)
        self.entry_nom_prof.pack()
        # Convertimos a mayúsculas automáticamente al escribir el nombre
        self.entry_nom_prof.bind("<KeyRelease>", self.convertir_mayus)
        # Enfocamos el siguiente campo al presionar Enter
        self.entry_nom_prof.bind("<Return>", enfocar_siguiente)

        # implementamos un tooltip para el nombre completo
        AyudaVisual(self.entry_nom_prof, "Ingrese el nombre completo del profesor.")
        
        # Botón para guardar el profesor
        btn_guardar = tk.Button(frame, text="GUARDAR PROFESOR", bg="#16a085", fg="white",
                   font=("Arial", 10, "bold"), command=self.guardar_click)
        btn_guardar.pack(pady=25)

        # implementamos un tooltip para el botón de guardar
        AyudaVisual(btn_guardar, "Haz clic para guardar el profesor en la base de datos.")

        # al dar Enter en el botón, también se guarda el profesor
        btn_guardar.bind("<Return>", self.guardar_click)

    def guardar_click(self, event=None):
        """Captura los datos visuales y delega la lógica."""
        nombre = self.entry_nom_prof.get().strip().upper()
        ced_num = self.entry_ced_prof.get().strip()
        cedula = f"{self.combo_nac_prof.get()}-{ced_num}"

        try:
            # 1. Creamos la entidad pura
            nuevo_profesor = Profesor(cedula=cedula, nombre_completo=nombre)
            nuevo_profesor.validar() # Verificamos reglas de negocio
            
            # 2. Guardamos usando el puerto (no nos importa si es SQLite o MySQL)
            self.repositorio.guardar(nuevo_profesor)
            
            messagebox.showinfo("Listo", f"Profesor {nombre} registrado exitosamente.")
            # Limpiamos las cajas de texto tras guardar
            self.entry_ced_prof.delete(0, tk.END)
            self.entry_nom_prof.delete(0, tk.END)

        except ValueError as e:
            messagebox.showwarning("Atención", str(e))
        except Exception as e:
            messagebox.showerror("Error del sistema", str(e))