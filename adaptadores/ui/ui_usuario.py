# adaptadores/ui/ui_usuario.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from dominio.usuario import Usuario
from adaptadores.ui.utilidades_ui import AyudaVisual, enfocar_siguiente

class GestorUsuariosUI:
    """
    Panel de Administración de Usuarios. (CRUD con Borrado Lógico)
    """
    CLAVE_MAESTRA = "DIRECTOR2025" # Solo quien sepa esto puede entrar aquí

    def __init__(self, parent_root, repositorio_usuario):
        self.repositorio = repositorio_usuario
        self.usuario_seleccionado_id = None
        
        # 1. EL MURO DE SEGURIDAD
        clave_ingresada = simpledialog.askstring("Seguridad", "Ingrese la Clave Maestra del Director:", show='*', parent=parent_root)
        
        if clave_ingresada != self.CLAVE_MAESTRA:
            messagebox.showerror("Acceso Denegado", "Clave incorrecta. Incidente registrado.")
            return # Abortamos la creación de la ventana

        # 2. SI LA CLAVE ES CORRECTA, CREAMOS LA VENTANA
        self.root = tk.Toplevel(parent_root)
        self.root.title("🔐 Panel de Seguridad y Usuarios")
        self.root.geometry("850x550")
        self.root.config(bg="#2c3e50")
        
        self.crear_interfaz()
        self.cargar_tabla()

    def crear_interfaz(self):
        tk.Label(self.root, text="GESTIÓN DE USUARIOS DEL SISTEMA", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack(pady=10)

        # --- PANEL DE FORMULARIO ---
        frame_form = tk.Frame(self.root, bg="#34495e", padx=20, pady=20)
        frame_form.pack(fill="x", padx=20)

        # Fila 1
        tk.Label(frame_form, text="Nombre Completo:", bg="#34495e", fg="white").grid(row=0, column=0, sticky="e", pady=5)
        self.entry_nom = tk.Entry(frame_form, width=30); self.entry_nom.grid(row=0, column=1, padx=5)
        self.entry_nom.bind("<Return>", enfocar_siguiente)
        
        tk.Label(frame_form, text="Username (Login):", bg="#34495e", fg="white").grid(row=0, column=2, sticky="e", pady=5)
        self.entry_usr = tk.Entry(frame_form, width=20); self.entry_usr.grid(row=0, column=3, padx=5)
        self.entry_usr.bind("<Return>", enfocar_siguiente)
        AyudaVisual(self.entry_usr, "Ej: admin, jperez, director")

        # Fila 2
        tk.Label(frame_form, text="Contraseña:", bg="#34495e", fg="white").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_pwd = tk.Entry(frame_form, width=30); self.entry_pwd.grid(row=1, column=1, padx=5)
        self.entry_pwd.bind("<Return>", enfocar_siguiente)

        tk.Label(frame_form, text="Rol en el sistema:", bg="#34495e", fg="white").grid(row=1, column=2, sticky="e", pady=5)
        self.combo_rol = ttk.Combobox(frame_form, values=["ADMIN", "SUBDIRECTOR", "PROFESOR", "SECRETARIA"], state="readonly", width=17)
        self.combo_rol.grid(row=1, column=3, padx=5); self.combo_rol.current(0)

        # Botones
        frame_btn = tk.Frame(frame_form, bg="#34495e")
        frame_btn.grid(row=2, column=0, columnspan=4, pady=15)
        
        tk.Button(frame_btn, text="💾 Guardar Nuevo", bg="#27ae60", fg="white", command=self.guardar).pack(side="left", padx=10)
        tk.Button(frame_btn, text="✏️ Actualizar Seleccionado", bg="#f39c12", fg="white", command=self.actualizar).pack(side="left", padx=10)
        tk.Button(frame_btn, text="🧹 Limpiar Cajas", bg="#95a5a6", fg="white", command=self.limpiar).pack(side="left", padx=10)
        btn_borrar = tk.Button(frame_btn, text="🗑️ Desactivar Usuario", bg="#c0392b", fg="white", command=self.desactivar)
        btn_borrar.pack(side="left", padx=10)
        AyudaVisual(btn_borrar, "No borra los datos históricos, solo le prohíbe entrar al sistema.")

        # --- TABLA DE USUARIOS ---
        self.tree = ttk.Treeview(self.root, columns=("ID", "Nombre", "Username", "Rol"), show="headings", height=10)
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=50, anchor="center")
        self.tree.heading("Nombre", text="Nombre Completo"); self.tree.column("Nombre", width=300)
        self.tree.heading("Username", text="Username"); self.tree.column("Username", width=150, anchor="center")
        self.tree.heading("Rol", text="Nivel de Acceso"); self.tree.column("Rol", width=150, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tree.bind("<Double-1>", self.seleccionar_fila)
        AyudaVisual(self.tree, "Doble clic en un usuario para editar sus datos")

    def limpiar(self):
        self.usuario_seleccionado_id = None
        self.entry_nom.delete(0, tk.END)
        self.entry_usr.delete(0, tk.END)
        self.entry_pwd.delete(0, tk.END)
        self.combo_rol.current(0)

    def cargar_tabla(self):
        for fila in self.tree.get_children():
            self.tree.delete(fila)
        
        usuarios = self.repositorio.obtener_activos()
        for u in usuarios:
            self.tree.insert("", tk.END, values=(u.id_usuario, u.nombre_completo, u.username, u.rol))

    def seleccionar_fila(self, event):
        item = self.tree.focus()
        if not item: return
        valores = self.tree.item(item)['values']
        
        self.limpiar()
        self.usuario_seleccionado_id = valores[0]
        self.entry_nom.insert(0, valores[1])
        self.entry_usr.insert(0, valores[2])
        self.entry_pwd.insert(0, "********") # Por seguridad no traemos el password real a la vista
        self.combo_rol.set(valores[3])

    def extraer_datos_ui(self):
        """Función auxiliar para no repetir código"""
        u = Usuario(
            nombre_completo=self.entry_nom.get().strip(),
            username=self.entry_usr.get().strip(),
            password=self.entry_pwd.get().strip(),
            rol=self.combo_rol.get(),
            id_usuario=self.usuario_seleccionado_id
        )
        u.validar()
        return u

    def guardar(self):
        if self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Está intentando guardar un usuario que ya existe. Use 'Actualizar' o limpie las cajas.")
            return
        try:
            nuevo_user = self.extraer_datos_ui()
            self.repositorio.guardar(nuevo_user)
            messagebox.showinfo("Éxito", "Usuario creado correctamente.")
            self.limpiar()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar(self):
        if not self.usuario_seleccionado_id: return
        try:
            user_editado = self.extraer_datos_ui()
            # Si dejaron los asteriscos, significa que no quisieron cambiar la clave. (En un sistema real aquí se maneja distinto)
            if user_editado.password == "********":
                messagebox.showwarning("Clave", "Escriba una nueva contraseña para actualizar, o vuelva a escribir la anterior.")
                return
                
            self.repositorio.actualizar(user_editado)
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
            self.limpiar()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def desactivar(self):
        if not self.usuario_seleccionado_id: return
        if messagebox.askyesno("Confirmar", "¿Seguro que desea desactivar a este usuario? Perderá el acceso al sistema."):
            self.repositorio.desactivar(self.usuario_seleccionado_id)
            messagebox.showinfo("Desactivado", "Usuario revocado del sistema exitosamente.")
            self.limpiar()
            self.cargar_tabla()