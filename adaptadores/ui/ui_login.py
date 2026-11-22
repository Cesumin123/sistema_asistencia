# adaptadores/ui/ui_login.py
"""
Adaptador de Interfaz Gráfica para Autenticación de Usuarios (CU-01, RF-02).
Desacoplado de SQL: interactúa exclusivamente con el RepositorioUsuario
y el Dominio de Usuario para validación y hashing PBKDF2.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional

from puertos.repositorio_usuario import RepositorioUsuario
from dominio.usuario import Usuario
from dominio.promocion import ServicioPromocionDominio


class VentanaLogin:
    """
    Ventana de inicio de sesión con autenticación criptográfica segura.
    """

    def __init__(
        self,
        repositorio_usuario: RepositorioUsuario,
        on_login_exitoso: Callable[[Usuario], None],
        root: Optional[tk.Tk] = None
    ):
        self.repo = repositorio_usuario
        self.on_login_exitoso = on_login_exitoso

        if root is None:
            self.root = tk.Tk()
            self._root_propio = True
        else:
            self.root = root
            self._root_propio = False

        self.root.title("Acceso al Sistema Escolar - Colinas del Llano")
        self.root.geometry("380x480")
        self.root.resizable(False, False)
        self.root.config(bg="#2c3e50")

        # Centrar ventana
        self._centrar_ventana(380, 480)
        self._crear_interfaz()

    def _centrar_ventana(self, ancho: int, alto: int):
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = max(0, int((sw - ancho) / 2))
            y = max(0, int((sh - alto) / 2))
            self.root.geometry(f"{ancho}x{alto}+{x}+{y}")
        except Exception:
            pass

    def _crear_interfaz(self):
        """Construye el formulario de login y registro de usuarios."""
        # Encabezado institucional
        tk.Label(
            self.root,
            text="SISTEMA ESCOLAR",
            fg="white",
            bg="#2c3e50",
            font=("Arial", 18, "bold")
        ).pack(pady=(35, 5))

        tk.Label(
            self.root,
            text="Complejo Educativo 'Colinas del Llano'",
            fg="#bdc3c7",
            bg="#2c3e50",
            font=("Arial", 9, "italic")
        ).pack(pady=(0, 25))

        # Marco central de credenciales
        frame_form = tk.Frame(self.root, bg="#2c3e50")
        frame_form.pack(padx=30)

        tk.Label(
            frame_form,
            text="Nombre de Usuario:",
            fg="#ecf0f1",
            bg="#2c3e50",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self.entry_usuario = tk.Entry(frame_form, width=28, font=("Arial", 11))
        self.entry_usuario.pack(pady=(4, 15))
        self.entry_usuario.focus()

        tk.Label(
            frame_form,
            text="Contraseña:",
            fg="#ecf0f1",
            bg="#2c3e50",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self.entry_password = tk.Entry(frame_form, width=28, font=("Arial", 11), show="*")
        self.entry_password.pack(pady=(4, 20))
        self.entry_password.bind("<Return>", lambda e: self.iniciar_sesion())

        # Botón de entrada
        self.btn_login = tk.Button(
            self.root,
            text="INICIAR SESIÓN ▶",
            bg="#e74c3c",
            fg="white",
            width=22,
            font=("Arial", 10, "bold"),
            cursor="hand2",
            relief="flat",
            command=self.iniciar_sesion
        )
        self.btn_login.pack(pady=10)

        # Sección para registro de nuevas cuentas protegidas
        tk.Label(
            self.root,
            text="¿Requiere una nueva cuenta de acceso?",
            fg="#95a5a6",
            bg="#2c3e50",
            font=("Arial", 8)
        ).pack(pady=(25, 2))

        tk.Button(
            self.root,
            text="Registrar Nuevo Usuario",
            bg="#34495e",
            fg="white",
            font=("Arial", 8),
            cursor="hand2",
            relief="flat",
            command=self.solicitar_registro
        ).pack()

    def iniciar_sesion(self):
        """Valida credenciales ingresadas contra el repositorio mediante PBKDF2."""
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        if not usuario or not password:
            messagebox.showwarning(
                "Faltan Datos",
                "Por favor ingrese su nombre de usuario y contraseña."
            )
            return

        usuario_autenticado = self.repo.autenticar(usuario, password)

        if usuario_autenticado:
            # Login exitoso (CP-01)
            self.root.destroy()
            self.on_login_exitoso(usuario_autenticado)
        else:
            # Credenciales inválidas o cuenta inactiva (CP-02)
            messagebox.showerror(
                "Acceso Denegado",
                "Usuario o contraseña incorrectos, o cuenta de usuario inactiva."
            )

    def solicitar_registro(self):
        """Solicita la clave maestra administrativa para autorizar el registro de un nuevo usuario."""
        clave = simpledialog.askstring(
            "Autorización Administrativa",
            "Ingrese la Clave Maestra Institucional:",
            show="*",
            parent=self.root
        )

        if clave is None:
            return

        try:
            ServicioPromocionDominio.validar_autorizacion(clave)
            self._abrir_modal_registro()
        except PermissionError as perm_err:
            messagebox.showerror("Acceso Denegado", str(perm_err))

    def _abrir_modal_registro(self):
        """Ventana modal para dar de alta una nueva cuenta de usuario."""
        win = tk.Toplevel(self.root)
        win.title("Alta de Nuevo Usuario")
        win.geometry("340x430")
        win.resizable(False, False)
        win.config(bg="#ecf0f1")
        win.grab_set()

        tk.Label(
            win,
            text="REGISTRO DE USUARIO",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack(pady=15)

        f = tk.Frame(win, bg="#ecf0f1", padx=20)
        f.pack(fill="both")

        tk.Label(f, text="Nombre Completo:", bg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(5, 2))
        e_nom = tk.Entry(f, width=30)
        e_nom.pack()

        tk.Label(f, text="Nombre de Usuario (Login):", bg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 2))
        e_usr = tk.Entry(f, width=30)
        e_usr.pack()

        tk.Label(f, text="Contraseña:", bg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 2))
        e_pwd = tk.Entry(f, width=30, show="*")
        e_pwd.pack()

        tk.Label(f, text="Rol de Acceso (RBAC):", bg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 2))
        c_rol = ttk.Combobox(f, values=["DOCENTE", "ASISTENTE", "ADMIN"], state="readonly", width=28)
        c_rol.pack()
        c_rol.current(0)

        def guardar():
            nombre = e_nom.get().strip()
            username = e_usr.get().strip()
            password = e_pwd.get().strip()
            rol = c_rol.get().strip()

            try:
                nuevo_usuario = Usuario(
                    nombre_completo=nombre,
                    username=username,
                    password=password,
                    rol=rol
                )
                nuevo_usuario.validar()
                self.repo.guardar(nuevo_usuario)
                messagebox.showinfo(
                    "Éxito",
                    f"Usuario '{username}' registrado exitosamente con rol '{rol}'."
                )
                win.destroy()
            except ValueError as val_err:
                messagebox.showwarning("Dato Inválido", str(val_err))
            except Exception as err:
                messagebox.showerror("Error al Guardar", str(err))

        tk.Button(
            win,
            text="💾 GUARDAR USUARIO",
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            command=guardar
        ).pack(pady=25)


# Alias para compatibilidad
LoginApp = VentanaLogin
