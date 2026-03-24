import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
import sqlite3
import json # Herramienta para guardar archivos de texto rápido
import os   # Herramienta para borrar archivos del sistema
from db_conexion import ConexionBD
from tkcalendar import DateEntry 

class GestorAsistencia:
    """
    Módulo para Pasar la Lista.
    Si se va la luz, guarda lo que llevas en un archivo temporal.
    Al volver, te pregunta si quieres recuperarlo.
    """
    
    def __init__(self):
        # Nombre del archivo de seguridad (La libreta de borrador)
        self.archivo_seguridad = "memoria_emergencia.json"
        
        # 1. Ventana para elegir materia
        self.root_selector = tk.Toplevel()
        self.root_selector.title("Paso 1: Seleccionar Clase")
        self.root_selector.geometry("500x350")
        # Esta instrucción le dice a la ventana que se expanda al máximo al abrirse
        self.root.state('zoomed')
        
        # Memoria para las excusas médicas
        self.justificaciones_temp = {} 
        
        self.crear_interfaz_selector()

    def crear_interfaz_selector(self):
        """Dibuja los botones para elegir materia y fecha."""
        
        # Elegir Clase
        tk.Label(self.root_selector, text="Seleccione la Clase:", font=("Arial", 11)).pack(pady=10)
        self.combo_clases = ttk.Combobox(self.root_selector, width=60, state="readonly")
        self.combo_clases.pack()
        
        # Listas ocultas
        self.ids_clases = [] 
        self.cargar_clases_bd()
        
        # Elegir Fecha
        tk.Label(self.root_selector, text="Fecha de Asistencia:", font=("Arial", 11)).pack(pady=10)
        self.cal_fecha = DateEntry(self.root_selector, width=12, background='darkblue', 
                                   foreground='white', borderwidth=2, 
                                   date_pattern='dd/mm/y', locale='es_ES')
        self.cal_fecha.pack()
        
        # Botón Iniciar
        tk.Button(self.root_selector, text="COMENZAR CLASE ▶", bg="#2980b9", fg="white", 
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=self.abrir_planilla).pack(pady=20)

    def cargar_clases_bd(self):
        """Busca las materias en la base de datos."""
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Unimos texto: "MATEMÁTICA - 1er AÑO (PROFESOR)"
                sql = """SELECT C.ID_CLASE, 
                                C.NOMBRE_MATERIA || ' - ' || G.DESCRIPCION || ' ' || S.DESCRIPCION || ' (' || P.NOMBRE_COMPLETO || ')' 
                         FROM TBL_CLASES C 
                         JOIN TBL_GRADOS G ON C.ID_GRADO=G.ID_GRADO 
                         JOIN TBL_SECCIONES S ON C.ID_SECCION=S.ID_SECCION 
                         JOIN TBL_PROFESORES P ON C.ID_PROFESOR=P.ID_PROFESOR"""
                cursor.execute(sql)
                
                nombres = []
                for row in cursor.fetchall():
                    self.ids_clases.append(row[0])
                    nombres.append(row[1])
                
                self.combo_clases['values'] = nombres
                if nombres: self.combo_clases.current(0)
            finally: 
                db.cerrar()

    def abrir_planilla(self):
        """Prepara todo para pasar la lista."""
        idx = self.combo_clases.current()
        if idx == -1: return
        
        id_clase = self.ids_clases[idx]
        nombre_clase = self.combo_clases.get()
        fecha_obj = self.cal_fecha.get_date()
        
        self.root_selector.destroy() # Cerramos el selector
        self.crear_ventana_planilla(id_clase, nombre_clase, fecha_obj)

    def crear_ventana_planilla(self, id_clase, nombre_clase, fecha_obj):
        """Crea la tabla grande para marcar Presente/Ausente."""
        self.win_planilla = tk.Toplevel()
        self.win_planilla.title(f"Planilla de Asistencia")
        self.win_planilla.geometry("850x600")
        self.win_planilla.state('zoomed')
        
        # Guardamos estos datos para usarlos en el autoguardado
        self.id_clase_actual = id_clase
        self.fecha_actual_str = fecha_obj.strftime("%Y-%m-%d")
        
        # Encabezado
        frame_head = tk.Frame(self.win_planilla, bg="#ecf0f1", pady=10)
        frame_head.pack(fill="x")
        tk.Label(frame_head, text=nombre_clase, font=("Arial", 12, "bold"), bg="#ecf0f1").pack()
        tk.Label(frame_head, text=f"Fecha: {fecha_obj.strftime('%d/%m/%Y')}", font=("Arial", 10), bg="#ecf0f1").pack()
        
        # Tabla
        self.tree = ttk.Treeview(self.win_planilla, columns=("id", "nom", "st"), show="headings", height=15)
        self.tree.heading("id", text="Cédula"); self.tree.column("id", width=100)
        self.tree.heading("nom", text="Estudiante"); self.tree.column("nom", width=400)
        self.tree.heading("st", text="Estado"); self.tree.column("st", width=80, anchor="center")
        
        self.tree.tag_configure("presente", foreground="green")
        self.tree.tag_configure("ausente", foreground="red")
        self.tree.tag_configure("justificado", foreground="#d35400")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 1. Cargamos la lista original de alumnos
        self.cargar_alumnos(id_clase)
        
        # 2. ¡MAGIA! Verificamos si se fue la luz antes y hay algo guardado
        self.verificar_recuperacion_emergencia()
        
        # Botones
        fb = tk.Frame(self.win_planilla, pady=10); fb.pack()
        
        tk.Button(fb, text="✅ PRESENTE", bg="#2ecc71", fg="white", 
                  command=lambda: self.cambiar_estado("P")).pack(side="left", padx=5)
        
        tk.Button(fb, text="❌ AUSENTE", bg="#e74c3c", fg="white", 
                  command=lambda: self.cambiar_estado("A")).pack(side="left", padx=5)
        
        tk.Button(fb, text="⚠️ JUSTIFICADA", bg="#f39c12", fg="white", 
                  command=lambda: self.cambiar_estado("J")).pack(side="left", padx=5)
        
        tk.Button(self.win_planilla, text="💾 GUARDAR EN BASE DE DATOS", bg="#34495e", fg="white", font=("bold"), width=30,
                  command=lambda: self.guardar_final_bd(id_clase, fecha_obj)).pack(pady=15)

    def cargar_alumnos(self, id_clase):
        """Trae a los alumnos de la base de datos."""
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cur = conn.cursor()
                # Buscamos grado y sección de la materia
                cur.execute("SELECT ID_GRADO, ID_SECCION FROM TBL_CLASES WHERE ID_CLASE=?", (id_clase,))
                datos = cur.fetchone()
                if datos:
                    # Buscamos alumnos
                    sql = "SELECT ID_ESTUDIANTE, NOMBRE FROM TBL_ESTUDIANTES WHERE ID_GRADO=? AND ID_SECCION=? ORDER BY NOMBRE"
                    cur.execute(sql, (datos[0], datos[1]))
                    for alum in cur.fetchall():
                        # Por defecto todos están Presentes (P)
                        self.tree.insert("", "end", values=(alum[0], alum[1], "P"), tags=("presente",))
            finally: db.cerrar()

    def cambiar_estado(self, nuevo_estado):
        """
        Cambia P, A o J cuando tocas los botones.
        Y ADEMÁS: Guarda una copia de seguridad inmediatamente.
        """
        seleccion = self.tree.selection()
        if not seleccion: return

        for item in seleccion:
            vals = self.tree.item(item, "values")
            cedula = vals[0]
            nombre = vals[1]
            
            # Lógica de justificación
            if nuevo_estado == "J":
                motivo = simpledialog.askstring("Motivo", f"¿Por qué faltó {nombre}?")
                if motivo: self.justificaciones_temp[cedula] = motivo
                else: continue
            else:
                if cedula in self.justificaciones_temp: 
                    del self.justificaciones_temp[cedula]

            # Cambiar color
            tag = "presente"
            if nuevo_estado == "A": tag = "ausente"
            elif nuevo_estado == "J": tag = "justificado"
            
            self.tree.item(item, values=(cedula, nombre, nuevo_estado), tags=(tag,))
        
        # --- AQUÍ OCURRE EL GUARDADO AUTOMÁTICO ---
        self.guardar_copia_seguridad()

    # -----------------------------------------------------------
    #  SISTEMA ANTI-APAGONES (Funciones de Emergencia)
    # -----------------------------------------------------------

    def guardar_copia_seguridad(self):
        """Guarda el estado actual en un archivo de texto secreto."""
        datos_recuperacion = {
            "id_clase": self.id_clase_actual,
            "fecha": self.fecha_actual_str,
            "alumnos": [],
            "justificaciones": self.justificaciones_temp
        }
        
        # Recorremos la tabla visual para guardar cómo va la lista
        for item in self.tree.get_children():
            v = self.tree.item(item)['values']
            # v[0]=cedula, v[1]=nombre, v[2]=estado
            datos_recuperacion["alumnos"].append({
                "cedula": v[0],
                "nombre": v[1],
                "estado": v[2]
            })
            
        # Escribimos en el disco duro
        with open(self.archivo_seguridad, "w") as f:
            json.dump(datos_recuperacion, f)

    def verificar_recuperacion_emergencia(self):
        """Al abrir, revisa si hay un archivo guardado de emergencia."""
        if not os.path.exists(self.archivo_seguridad):
            return # No hay nada guardado, seguimos normal

        try:
            with open(self.archivo_seguridad, "r") as f:
                datos = json.load(f)
            
            # Verificamos si el archivo guardado es de ESTA clase y ESTA fecha
            if datos["id_clase"] == self.id_clase_actual and datos["fecha"] == self.fecha_actual_str:
                
                resp = messagebox.askyesno("Recuperación", 
                    "¡ATENCIÓN! Se encontró una lista sin guardar (quizás se fue la luz).\n"
                    "¿Deseas recuperar lo que llevabas?")
                
                if resp:
                    # Recuperamos las justificaciones
                    self.justificaciones_temp = datos["justificaciones"]
                    
                    # Limpiamos la tabla
                    for i in self.tree.get_children(): self.tree.delete(i)
                    
                    # Llenamos con los datos recuperados
                    for alum in datos["alumnos"]:
                        tag = "presente"
                        if alum["estado"] == "A": tag = "ausente"
                        elif alum["estado"] == "J": tag = "justificado"
                        
                        self.tree.insert("", "end", values=(alum["cedula"], alum["nombre"], alum["estado"]), tags=(tag,))
                    
                    messagebox.showinfo("Listo", "Datos recuperados exitosamente.")
        
        except Exception as e:
            print(f"Error recuperando: {e}")

    # -----------------------------------------------------------
    #  GUARDADO FINAL
    # -----------------------------------------------------------

    def guardar_final_bd(self, id_clase, fecha_obj):
        """Guarda en la Base de Datos y BORRA el archivo de emergencia."""
        if not self.tree.get_children(): return

        db = ConexionBD()
        conn = db.conectar()
        if not conn: return

        try:
            cursor = conn.cursor()
            fecha_sql = fecha_obj.strftime('%Y-%m-%d')

            # 1. Borramos registros viejos de ese día (para no duplicar)
            cursor.execute("DELETE FROM TBL_ASISTENCIA WHERE ID_CLASE=? AND FECHA=?", (id_clase, fecha_sql))

            # 2. Insertamos lo nuevo
            count = 0
            for item in self.tree.get_children():
                vals = self.tree.item(item)['values']
                ced, est = vals[0], vals[2]

                sql = "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (id_clase, ced, fecha_sql, est))
                
                # Si hay justificación, la guardamos
                id_asis = cursor.lastrowid 
                if est == 'J' and ced in self.justificaciones_temp:
                    cursor.execute("INSERT INTO TBL_JUSTIFICACIONES (ID_ASISTENCIA, MOTIVO) VALUES (?, ?)", 
                                   (id_asis, self.justificaciones_temp[ced]))
                count += 1

            conn.commit()
            
            # --- LIMPIEZA ---
            # Como ya guardamos en la BD, borramos el papelito de emergencia
            if os.path.exists(self.archivo_seguridad):
                os.remove(self.archivo_seguridad)
                
            messagebox.showinfo("Éxito", f"Se guardó la asistencia de {count} alumnos.")
            self.win_planilla.destroy()

        except Exception as err:
            conn.rollback()
            messagebox.showerror("Error", str(err))
        finally:
            db.cerrar()

if __name__ == "__main__":
    GestorAsistencia()
