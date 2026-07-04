# adaptadores/ui/ui_clase.py
import tkinter as tk
from tkinter import ttk, messagebox
from dominio.clase import Clase
from adaptadores.ui.utilidades_ui import AyudaVisual, enfocar_siguiente

class GestorClasesUI:
    """
    Adaptador de Interfaz para las Materias (Clases).
    Solo dibuja la ventana y recolecta los clics del usuario.
    """
    def __init__(self, parent_notebook, repositorio_clase):
        self.notebook = parent_notebook
        self.repositorio = repositorio_clase
        self.crear_tab()
        self.mapa_secciones = {}  # Mapa para almacenar la relación entre el índice de la Listbox y el ID de la sección
        self.cargar_datos_en_listas() # Llenamos los menús desplegables

    def convertir_mayus(self, event):
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.index(pos)

    def crear_tab(self):
        tab = tk.Frame(self.notebook, bg="#f9ebea")
        self.notebook.add(tab, text="  📚  ASIGNAR MATERIAS  ")
        
        frame = tk.Frame(tab, bg="#f9ebea")
        frame.pack(pady=20)
        
        # --- 1. NOMBRE DE LA MATERIA ---

        tk.Label(frame, text="Nombre de la Materia:", bg="#f9ebea").grid(row=0, column=0, pady=10, sticky="e")
        self.entry_nom_mat = tk.Entry(frame, width=30)
        self.entry_nom_mat.grid(row=0, column=1, padx=10)
        self.entry_nom_mat.bind("<KeyRelease>", self.convertir_mayus)
        self.entry_nom_mat.bind("<Return>", enfocar_siguiente)
        #tooltip de ayuda para el nombre de la materia.
        AyudaVisual(self.entry_nom_mat, "Ej: MATEMÁTICAS, CASTELLANO...")
        
        # --- 2. PROFESOR ---

        tk.Label(frame, text="Asignar al Profesor:", bg="#f9ebea").grid(row=1, column=0, pady=10, sticky="e")
        self.combo_prof = ttk.Combobox(frame, width=27, state="readonly")
        self.combo_prof.grid(row=1, column=1, padx=10)
        self.combo_prof.bind("<Return>", enfocar_siguiente)
        #tooltip de ayuda para el combo de profesores.
        AyudaVisual(self.combo_prof, "Seleccione el profesor que dictará la clase")


        # --- 3. AÑO/GRADO ---

        tk.Label(frame, text="Año / Grado:", bg="#f9ebea").grid(row=2, column=0, pady=10, sticky="e")
        self.combo_grado = ttk.Combobox(frame, width=27, state="readonly")
        self.combo_grado['values'] = ["1 - 1er AÑO", "2 - 2do AÑO", "3 - 3er AÑO", "4 - 4to AÑO", "5 - 5to AÑO"] # El grado 6 es GRADUADO, a ellos no se les asignan materias
        self.combo_grado.grid(row=2, column=1, padx=10)
        
        #tooltip de ayuda para el combo de grados
        AyudaVisual(self.combo_grado, "Seleccione a qué año pertenece")


        # --- 4. SECCIONES (Selección Múltiple) ---

        tk.Label(frame, text="Secciones (Puede elegir varias):", bg="#f9ebea").grid(row=3, column=0, pady=10, sticky="ne")
        
        # selectmode=tk.MULTIPLE permite hacer clic en varias opciones a la vez
        self.listbox_secciones = tk.Listbox(frame, height=5, selectmode=tk.MULTIPLE, exportselection=False)
        self.listbox_secciones.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        #  Agregar elementos SIN números para que el usuario no se confunda, pero guardamos el ID internamente
        secciones_disponibles = ["Sección A", "Sección B", "Sección C", "Sección D", "Sección E", "Sección F", "Sección G", "Sección H", "Sección I", "Sección J"]
        for seccion in secciones_disponibles:
            self.listbox_secciones.insert(tk.END, seccion)  # ← Esto elimina los números
        

        # Agregamos una Ayuda Visual para explicar cómo funciona la selección múltiple
        AyudaVisual(self.listbox_secciones, "Haga clic en todas las secciones donde este profesor dará esta materia")
        
        # --- BOTÓN ---
        btn_guardar = tk.Button(frame, text="INSCRIBIR MATERIA", bg="#c0392b", fg="white", 
                                font=("Arial", 10, "bold"), command=self.guardar_click)
        btn_guardar.grid(row=4, column=0, columnspan=2, pady=25)
        AyudaVisual(btn_guardar, "Guarda la configuración para todas las secciones elegidas")

    def cargar_datos_en_listas(self):
        """Usa el Repositorio para buscar en la BD y llena los Combobox."""
        
        profesores = self.repositorio.obtener_profesores_activos()
        self.combo_prof['values'] = [f"{p[0]} - {p[1]}" for p in profesores]
        
        grados = self.repositorio.obtener_grados()
        self.combo_grado['values'] = [f"{g[0]} - {g[1]}" for g in grados]
        
        # Carga de secciones con mapa secreto
        secciones = self.repositorio.obtener_secciones()
        self.listbox_secciones.delete(0, tk.END) # Limpiamos por si acaso
        self.mapa_secciones.clear()
        
        for sec in secciones:
            id_sec = sec[0]
            texto_pantalla = f"Sección {sec[1]}"
            
            # Lo mostramos bonito en la pantalla
            self.listbox_secciones.insert(tk.END, texto_pantalla)
            # Lo guardamos en el diccionario (Ej: {"Sección A": 1})
            self.mapa_secciones[texto_pantalla] = id_sec

    def guardar_click(self):
        """Captura visual, crea Entidades y delega el guardado."""
        materia = self.entry_nom_mat.get().strip().upper()
        prof_seleccionado = self.combo_prof.get()
        grado_seleccionado = self.combo_grado.get()
        indices_secciones = self.listbox_secciones.curselection()

        # 1. Validaciones básicas de UI
        if not materia or not prof_seleccionado or not grado_seleccionado or not indices_secciones:
            messagebox.showwarning("Faltan datos", "Complete todos los campos y elija al menos una sección.")
            return

        try:
            # Extraemos los IDs (el número antes del guion "-")
            id_prof = int(prof_seleccionado.split(" - ")[0])
            id_grado = int(grado_seleccionado.split(" - ")[0])
            
            lista_materias_nuevas = []
            
            # Por cada sección seleccionada, creamos una entidad "Clase"
            for idx in indices_secciones:
                # Obtenemos el texto de la sección seleccionada
                texto_seccion = self.listbox_secciones.get(idx)
                # buscamos el ID real de la sección usando el mapa secreto
                id_seccion = self.mapa_secciones[texto_seccion]

                # Creamos la entidad Clase y la agregamos a la lista
                nueva_clase = Clase(materia, id_prof, id_grado, id_seccion)
                nueva_clase.validar()
                # Agregamos a la lista de materias nuevas
                lista_materias_nuevas.append(nueva_clase)
            
            # 2. Le pasamos toda la lista a la Base de Datos para que la guarde de un solo golpe
            self.repositorio.guardar_lote(lista_materias_nuevas)
            
            messagebox.showinfo("Éxito", f"Materia '{materia}' registrada para {len(lista_materias_nuevas)} sección(es).")
            
            # Limpiamos la pantalla
            self.entry_nom_mat.delete(0, tk.END)
            self.combo_prof.set('')
            self.combo_grado.set('')
            self.listbox_secciones.selection_clear(0, tk.END)

        except ValueError as e:
            messagebox.showwarning("Regla de Negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")