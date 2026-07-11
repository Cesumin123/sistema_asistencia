import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from db_conexion import ConexionBD

# Intentamos importar el Menú Principal.
# Usamos un truco (try/except) para que, si estás probando solo este archivo
# y no tienes el menú creado, no se cierre el programa de golpe.
try:
    from menu_principal import MenuPrincipal 
except ImportError:
    MenuPrincipal = None

class LoginApp:
    """
    Controlador de Acceso (Login).
    Es el portero del sistema: pide la contraseña para dejarte pasar.
    """
    
    # Esta es una clave secreta para que solo el Director pueda crear nuevos usuarios.
    CLAVE_MAESTRA = "DIRECTOR2025" 

    def __init__(self):
        # --- Configuración de la Ventana (El marco del cuadro) ---
        self.root = tk.Tk()
        self.root.title("Acceso al Sistema Escolar")
        self.root.geometry("350x450") 
        self.root.config(bg="#2c3e50") # Color de fondo (Azul oscuro elegante)
        self.root.resizable(False, False) # Prohibido cambiar el tamaño de la ventana
        
        self.crear_interfaz()
        
        # Mantiene la ventana abierta esperando clics
        self.root.mainloop()

    def crear_interfaz(self):
        """Dibuja los botones y cajas de texto en la pantalla."""
        
        # Título Grande
        tk.Label(self.root, text="SISTEMA ESCOLAR", fg="white", bg="#2c3e50", 
                 font=("Arial", 18, "bold")).pack(pady=30)

        # Un marco invisible para ordenar las cosas en el centro
        frame = tk.Frame(self.root, bg="#2c3e50")
        frame.pack()

        # --- Caja para escribir el Usuario ---
        tk.Label(frame, text="Usuario:", fg="#bdc3c7", bg="#2c3e50", font=("Arial", 10)).pack(anchor="w")
        self.entry_user = tk.Entry(frame, width=30, font=("Arial", 11))
        self.entry_user.pack(pady=(0, 15))
        self.entry_user.focus() # Pone el cursor aquí listo para escribir

        # --- Caja para escribir la Contraseña ---
        tk.Label(frame, text="Contraseña:", fg="#bdc3c7", bg="#2c3e50", font=("Arial", 10)).pack(anchor="w")
        self.entry_pass = tk.Entry(frame, width=30, font=("Arial", 11), show="*") # show="*" pone asteriscos
        self.entry_pass.pack(pady=(0, 20))
        
        # Truco: Si presionas la tecla ENTER, funciona igual que hacer clic en el botón
        self.entry_pass.bind("<Return>", lambda event: self.verificar_login())

        # --- Botón Rojo de Entrar ---
        tk.Button(self.root, text="INICIAR SESIÓN ▶", bg="#e74c3c", fg="white", 
                  width=20, font=("Arial", 10, "bold"), cursor="hand2", relief="flat",
                  command=self.verificar_login).pack(pady=10)

        # --- Enlace pequeño abajo para crear cuentas ---
        tk.Label(self.root, text="¿No tienes cuenta?", fg="#7f8c8d", bg="#2c3e50", font=("Arial", 9)).pack(pady=(30, 0))
        tk.Button(self.root, text="Registrar Nuevo Usuario", bg="#34495e", fg="white", 
                  font=("Arial", 8), cursor="hand2", relief="flat",
                  command=self.solicitar_registro).pack(pady=5)

    def verificar_login(self):
        """
        Revisa si el usuario y la contraseña son correctos.
        """
        # .strip() es como una goma de borrar: quita espacios accidentales al inicio o final
        # Ejemplo: " admin " se convierte en "admin"
        usuario = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not usuario or not password:
            messagebox.showwarning("Faltan Datos", "Por favor escribe tu usuario y contraseña.")
            return

        # Conectamos con el cerebro (Base de Datos)
        db = ConexionBD()
        conn = db.conectar()
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # --- CAMBIO IMPORTANTE PARA SQLITE ---
                # Usamos '?' en lugar de '%s'. Es el hueco donde pondremos los datos.
                sql = "SELECT ROL FROM TBL_USUARIOS WHERE USERNAME = ? AND PASSWORD = ?"
                
                cursor.execute(sql, (usuario, password))
                resultado = cursor.fetchone() # Buscamos si existe alguien con esos datos

                if resultado:
                    # ¡Encontramos al usuario!
                    rol_encontrado = resultado[0] # Guardamos si es ADMIN o COORDINADOR
                    self.root.destroy() # Cerramos la ventana de login
                    
                    # Abrimos el Menú Principal
                    if MenuPrincipal:
                        MenuPrincipal(rol_usuario=rol_encontrado)
                    else:
                        messagebox.showinfo("Éxito", f"Login correcto. Rol: {rol_encontrado}\n(Falta crear el archivo menu_principal.py)")
                else:
                    messagebox.showerror("Error", "Usuario o Contraseña incorrectos.")
            except Exception as e:
                messagebox.showerror("Error", f"Algo salió mal: {e}")
            finally:
                db.cerrar() # Siempre cerramos la conexión
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")

    def solicitar_registro(self):
        """Pide la clave secreta antes de dejarte crear un usuario nuevo."""
        clave = simpledialog.askstring("Seguridad", "Ingrese Clave de Director:", show="*")
        
        if clave == self.CLAVE_MAESTRA:
            self.abrir_ventana_registro()
        elif clave is not None:
            messagebox.showerror("Acceso Denegado", "Clave incorrecta.")

    def abrir_ventana_registro(self):
        """Abre una ventanita pequeña para crear un usuario."""
        win = tk.Toplevel(self.root)
        win.title("Nuevo Usuario")
        win.geometry("300x380")
        win.config(bg="#ecf0f1") # Fondo claro para contraste   
        
        # --- Formulario ---
        tk.Label(win, text="Nombre Real:").pack(pady=(10, 2))
        e_nom = tk.Entry(win); e_nom.pack()
        
        tk.Label(win, text="Usuario (Login):").pack(pady=2)
        e_usr = tk.Entry(win); e_usr.pack()
        
        tk.Label(win, text="Contraseña:").pack(pady=2)
        e_pwd = tk.Entry(win); e_pwd.pack()
        
        tk.Label(win, text="Permisos:").pack(pady=2)
        c_rol = ttk.Combobox(win, values=["COORDINADOR", "SUBDIRECTOR", "ADMIN"], state="readonly")
        c_rol.pack(); c_rol.current(0) # Selecciona el primero por defecto
        
        def guardar():
            # Revisamos que no dejen nada vacío
            if not e_nom.get() or not e_usr.get() or not e_pwd.get():
                messagebox.showwarning("Ojo", "Todos los campos son obligatorios.")
                return

            db = ConexionBD()
            conn = db.conectar()
            if conn:
                try:
                    cursor = conn.cursor()
                    # --- CAMBIO IMPORTANTE PARA SQLITE ---
                    # Usamos '?' 4 veces para los 4 datos
                    sql = "INSERT INTO TBL_USUARIOS (NOMBRE_COMPLETO, USERNAME, PASSWORD, ROL) VALUES (?, ?, ?, ?)"
                    
                    datos = (e_nom.get().strip().upper(), e_usr.get().strip(), e_pwd.get().strip(), c_rol.get())
                    cursor.execute(sql, datos)
                    
                    conn.commit() # Guardar cambios
                    messagebox.showinfo("Listo", "Usuario creado correctamente.")
                    win.destroy()
                    
                except sqlite3.IntegrityError: # <--- Error específico de SQLite
                    messagebox.showerror("Error", "Ese nombre de usuario YA EXISTE. Prueba otro.")
                except Exception as err:
                    messagebox.showerror("Error", str(err))
                finally: 
                    db.cerrar()

        tk.Button(win, text="GUARDAR USUARIO", bg="#27ae60", fg="white", font=("bold"), 
                  command=guardar).pack(pady=25)

if __name__ == "__main__":
    LoginApp()
