import tkinter as tk
from tkinter import messagebox
# Importamos la librería Pillow para manipulación avanzada de imágenes
from PIL import Image, ImageTk 
import sys
import os

# IMPORTACIONES DE LOS MÓDULOS DEL SISTEMA
from interfaz_registro import GestorEstudiantes
from interfaz_academica import GestorAcademico
from interfaz_asistencia import GestorAsistencia
from interfaz_reportes import GestorReportes
from interfaz_listados import VisorListados
from interfaz_promocion import GestorPromocion
from interfaz_coordinacion import GestorCoordinacion

def ruta_recurso(relativo):
    """Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relativo)

class MenuPrincipal:
    """
    PANEL DE CONTROL PRINCIPAL
    Esta clase gestiona la navegación central del sistema.
    """
    def __init__(self, rol_usuario="ADMIN"):
        self.rol = rol_usuario
        self.root = tk.Tk()
        self.root.title(f"Sistema de Control Escolar - Usuario: {self.rol}")
        
        # Aumentamos el ancho a 900px para que quepa el logo a la izquierda
        self.root.geometry("900x700")
        self.root.state('zoomed')  # Abrir en pantalla completa 
        self.root.config(bg="#ecf0f1") # Color de fondo gris claro (profesional)

        # Esta instrucción le dice a la ventana que se expanda al máximo al abrirse
        self.root.state('zoomed')
        
        # Iniciamos la construcción de la interfaz visual
        self.crear_interfaz()
        
        # Mantenemos la ventana en ejecución
        self.root.mainloop()

    def crear_interfaz(self):
        """
        Método encargado de distribuir los elementos visuales.
        Utilizamos un diseño de dos columnas (Frames).
        """
        
        # -----------------------------------------------------------
        # 1. PANEL IZQUIERDO (Área del Logo)
        # -----------------------------------------------------------
        # Creamos un contenedor (Frame) que ocupará el lado izquierdo
        frame_izq = tk.Frame(self.root, bg="#ecf0f1", width=350)
        frame_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        # Lógica para cargar la imagen de forma segura
        try:
            # Buscamos el archivo 'logo.png' en la misma carpeta del programa
            ruta_imagen = ruta_recurso("LOGOLICEO.png")
            
            # Abrimos la imagen original
            imagen_original = Image.open(ruta_imagen)
            
            # Redimensionamos la imagen para que no sea gigante (300x300 pixeles)
            # Usamos LANCZOS, un filtro que mantiene la calidad al reducir el tamaño
            imagen_redim = imagen_original.resize((300, 300), Image.Resampling.LANCZOS)
            
            # Convertimos la imagen a un formato que Tkinter entienda
            self.logo_tk = ImageTk.PhotoImage(imagen_redim)
            
            # Mostramos la imagen en una etiqueta (Label)
            lbl_img = tk.Label(frame_izq, image=self.logo_tk, bg="#ecf0f1")
            lbl_img.pack(expand=True) # expand=True la centra verticalmente
            
        except Exception as e:
            # Si no encuentra el logo o hay un error, mostramos un texto en su lugar.
            # Esto evita que el programa se cierre abruptamente.
            tk.Label(frame_izq, text="[LOGO INSTITUCIONAL]\n(Archivo 'logo.png' no encontrado)", 
                     bg="#ecf0f1", fg="gray").pack(expand=True)

        # -----------------------------------------------------------
        # 2. PANEL DERECHO (Área de Botones)
        # -----------------------------------------------------------
        # Creamos un contenedor para los botones a la derecha
        frame_der = tk.Frame(self.root, bg="#ecf0f1")
        frame_der.pack(side="right", fill="both", expand=True, padx=20)

        # Título del Sistema
        tk.Label(frame_der, text="PANEL DE CONTROL", font=("Arial", 22, "bold"), 
                 bg="#ecf0f1", fg="#2c3e50").pack(pady=(50, 30))
        
        # --- GENERACIÓN DE BOTONES ---
        # Pasamos 'frame_der' como argumento para que el botón se dibuje en el panel derecho
        
        # Botón Amarillo: Configuración Académica
        self.crear_boton(frame_der, "🎓 Gestión Académica", "#f1c40f", "black", 
                         lambda: GestorAcademico())
        
        # Botón Turquesa: Nueva oficina de Coordinación
        self.crear_boton(frame_der, "🏢 Coordinación y Salones", "#16a085", "white", 
                 lambda: GestorCoordinacion())

        # Botón Azul: Registro de Estudiantes
        self.crear_boton(frame_der, "👤 Gestión de Estudiantes", "#3498db", "white", 
                         lambda: GestorEstudiantes())
        
        # Botón Naranja: Asistencia
        self.crear_boton(frame_der, "📝 Tomar Asistencia", "#e67e22", "white", 
                         lambda: GestorAsistencia())
        
        # Botón Verde Agua: Listados
        self.crear_boton(frame_der, "👁️ Ver Listados Generales", "#1abc9c", "white", 
                         lambda: VisorListados())
        
        # Botón Morado: Reportes
        self.crear_boton(frame_der, "📊 Reportes y Estadísticas", "#9b59b6", "white", 
                         lambda: GestorReportes())

        # --- BOTONES DE ADMINISTRACIÓN ---
        if self.rol in ["ADMIN", "SUBDIRECTOR"]:
             self.crear_boton(frame_der, "⚠️ Promoción de Año", "#7f8c8d", "white", 
                              lambda: GestorPromocion())

        # Botón de Salir
        tk.Button(frame_der, text="Cerrar Sesión", font=("Arial", 10), bg="#95a5a6", fg="white",
                  command=self.root.destroy).pack(pady=40)

    def crear_boton(self, contenedor, texto, color_bg, color_fg, comando):
        """
        Método auxiliar 'Fábrica de Botones'.
        Ahora recibe un parámetro extra 'contenedor' para saber dónde ubicar el botón.
        """
        tk.Button(contenedor, text=texto, font=("Arial", 11), bg=color_bg, fg=color_fg, 
                  width=35, height=2, cursor="hand2", command=comando).pack(pady=8)

if __name__ == "__main__":
    MenuPrincipal()
