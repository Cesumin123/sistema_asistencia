# adaptadores/ui/ui_login.py
"""
Adaptador de Interfaz Gráfica para Autenticación de Usuarios (CU-01, RF-02).
Desacoplado de SQL: interactúa exclusivamente con el RepositorioUsuario
y el Dominio de Usuario para validación y hashing PBKDF2.

Diseño: tarjeta centrada sobre fondo neutro, feedback visual claro,
soporte Enter para iniciar sesión.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Optional

from puertos.repositorio_usuario import RepositorioUsuario
from dominio.usuario import Usuario
from dominio.promocion import ServicioPromocionDominio
from adaptadores.ui.utilidades_ui import (
    aplicar_tema_global, centrar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_PELIGRO, COLOR_TEXTO_PRINCIPAL,
    COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO, COLOR_SEPARADOR,
    COLOR_BORDE_TARJETA, FUENTE_TITULO, FUENTE_SUBTITULO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_BOTON, FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD,
    crear_boton, crear_tarjeta, crear_separador,
)


class VentanaLogin:
    """Ventana de inicio de sesión con autenticación criptográfica segura."""

    def __init__(
        self,
        repositorio_usuario: RepositorioUsuario,
        on_login_exitoso: Callable[[Usuario], None],
        root: Optional[tk.Tk] = None,
    ):
        self.repo = repositorio_usuario
        self.on_login_exitoso = on_login_exitoso

        if root is None:
            self.root = tk.Tk()
            self._root_propio = True
        else:
            self.root = root
            self._root_propio = False

        aplicar_tema_global(self.root)
        self.root.title("Acceso al Sistema — Colinas del Llano")
        self.root.resizable(False, False)
        self.root.config(bg=COLOR_FONDO_APP)

        centrar_ventana(self.root, 420, 520)
        self._crear_interfaz()

    # ──────────────────────────────────────────────────────────
    # INTERFAZ
    # ──────────────────────────────────────────────────────────
    def _crear_interfaz(self):
        """Construye el formulario de login tipo tarjeta centrada."""
        # Contenedor central
        contenedor = tk.Frame(self.root, bg=COLOR_FONDO_APP)
        contenedor.pack(expand=True, fill="both", padx=40, pady=30)

        # Tarjeta blanca centrada
        tarjeta = crear_tarjeta(contenedor, padx=30, pady=30)
        tarjeta.pack(expand=True, fill="both")

        # Encabezado institucional
        tk.Label(
            tarjeta, text="SISTEMA ESCOLAR", fg=COLOR_PRIMARIO,
            bg=COLOR_TARJETA, font=FUENTE_TITULO,
        ).pack(pady=(5, 2))

        tk.Label(
            tarjeta, text="Complejo Educativo 'Colinas del Llano'",
            fg=COLOR_TEXTO_SECUNDARIO, bg=COLOR_TARJETA,
            font=FUENTE_PEQUEÑA,
        ).pack(pady=(0, 20))

        crear_separador(tarjeta).pack(fill="x", pady=(0, 20))

        # Campo: Usuario
        tk.Label(
            tarjeta, text="Nombre de Usuario:", fg=COLOR_TEXTO_PRINCIPAL,
            bg=COLOR_TARJETA, font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x")

        self.entry_usuario = tk.Entry(
            tarjeta, font=FUENTE_CUERPO, relief="solid", bd=1,
            highlightthickness=1, highlightcolor=COLOR_SEPARADOR,
        )
        self.entry_usuario.pack(fill="x", pady=(4, 14), ipady=4)
        self.entry_usuario.focus()
        self.entry_usuario.bind("<Return>", lambda e: self.entry_password.focus())

        # Campo: Contraseña
        tk.Label(
            tarjeta, text="Contraseña:", fg=COLOR_TEXTO_PRINCIPAL,
            bg=COLOR_TARJETA, font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x")

        self.entry_password = tk.Entry(
            tarjeta, font=FUENTE_CUERPO, show="●", relief="solid", bd=1,
            highlightthickness=1, highlightcolor=COLOR_SEPARADOR,
        )
        self.entry_password.pack(fill="x", pady=(4, 24), ipady=4)
        self.entry_password.bind("<Return>", lambda e: self.iniciar_sesion())

        # Botón principal
        crear_boton(
            tarjeta, texto="INICIAR SESIÓN", comando=self.iniciar_sesion,
            color_bg=COLOR_PRIMARIO, color_hover=COLOR_ACENTO,
        ).pack(fill="x", ipady=4)

        # Separador inferior
        crear_separador(tarjeta).pack(fill="x", pady=(24, 12))

        # Enlace de registro
        tk.Label(
            tarjeta, text="¿Requiere una nueva cuenta de acceso?",
            fg=COLOR_TEXTO_SECUNDARIO, bg=COLOR_TARJETA, font=FUENTE_PEQUEÑA,
        ).pack()

        btn_reg = tk.Label(
            tarjeta, text="Registrar Nuevo Usuario",
            fg=COLOR_ACENTO, bg=COLOR_TARJETA,
            font=FUENTE_PEQUEÑA_BOLD, cursor="hand2",
        )
        btn_reg.pack(pady=(2, 0))
        btn_reg.bind("<Button-1>", lambda e: self.solicitar_registro())

    # ──────────────────────────────────────────────────────────
    # LÓGICA DE AUTENTICACIÓN
    # ──────────────────────────────────────────────────────────
    def iniciar_sesion(self):
        """Valida credenciales ingresadas contra el repositorio mediante PBKDF2."""
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        if not usuario or not password:
            messagebox.showwarning(
                "Faltan Datos",
                "Por favor ingrese su nombre de usuario y contraseña.",
            )
            return

        usuario_autenticado = self.repo.autenticar(usuario, password)

        if usuario_autenticado:
            self.root.destroy()
            self.on_login_exitoso(usuario_autenticado)
        else:
            messagebox.showerror(
                "Acceso Denegado",
                "Usuario o contraseña incorrectos, o cuenta de usuario inactiva.",
            )
            self.entry_password.delete(0, tk.END)
            self.entry_password.focus()

    def solicitar_registro(self):
        """Solicita la clave maestra administrativa para autorizar el registro."""
        clave = simpledialog.askstring(
            "Autorización Administrativa",
            "Ingrese la Clave Maestra Institucional:",
            show="*",
            parent=self.root,
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
        win.resizable(False, False)
        win.config(bg=COLOR_FONDO_APP)
        centrar_ventana(win, 380, 460)
        win.grab_set()

        tarjeta = crear_tarjeta(win, padx=28, pady=24)
        tarjeta.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(
            tarjeta, text="REGISTRO DE USUARIO",
            font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO,
        ).pack(pady=(0, 15))

        crear_separador(tarjeta).pack(fill="x", pady=(0, 15))

        # Campos
        def _campo(label_text):
            tk.Label(
                tarjeta, text=label_text, bg=COLOR_TARJETA,
                font=FUENTE_ETIQUETA, anchor="w",
            ).pack(fill="x", pady=(4, 2))
            e = tk.Entry(tarjeta, font=FUENTE_CUERPO, relief="solid", bd=1)
            e.pack(fill="x", ipady=3)
            return e

        e_nom = _campo("Nombre Completo:")
        e_usr = _campo("Nombre de Usuario (Login):")
        e_pwd = _campo("Contraseña:")
        e_pwd.config(show="●")

        tk.Label(
            tarjeta, text="Rol de Acceso (RBAC):", bg=COLOR_TARJETA,
            font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x", pady=(8, 2))
        c_rol = ttk.Combobox(
            tarjeta, values=["DOCENTE", "ASISTENTE", "ADMIN"],
            state="readonly", font=FUENTE_CUERPO,
        )
        c_rol.pack(fill="x")
        c_rol.current(0)

        def guardar():
            nombre = e_nom.get().strip()
            username = e_usr.get().strip()
            password = e_pwd.get().strip()
            rol = c_rol.get().strip()
            try:
                nuevo = Usuario(nombre_completo=nombre, username=username, password=password, rol=rol)
                nuevo.validar()
                self.repo.guardar(nuevo)
                messagebox.showinfo("Éxito", f"Usuario '{username}' registrado con rol '{rol}'.")
                win.destroy()
            except ValueError as val_err:
                messagebox.showwarning("Dato Inválido", str(val_err))
            except Exception as err:
                messagebox.showerror("Error al Guardar", str(err))

        crear_boton(
            tarjeta, texto="💾  GUARDAR USUARIO", comando=guardar,
            color_bg=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER,
        ).pack(fill="x", pady=(20, 0), ipady=4)


# Alias para compatibilidad
LoginApp = VentanaLogin
