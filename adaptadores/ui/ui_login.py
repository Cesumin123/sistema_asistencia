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
from dominio.usuario import Usuario, ServicioRecuperacionUsuario
from dominio.promocion import ServicioPromocionDominio
from adaptadores.ui.utilidades_ui import (
    aplicar_tema_global, centrar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_PELIGRO, COLOR_SECUNDARIO, COLOR_TEXTO_PRINCIPAL,
    COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO, COLOR_SEPARADOR,
    COLOR_BORDE_TARJETA, FUENTE_TITULO, FUENTE_SUBTITULO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_BOTON, FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD,
    crear_boton, crear_tarjeta, crear_separador,
    configurar_ventana_hija, restaurar_foco, AyudaVisual,
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

        centrar_ventana(self.root, 420, 545)
        self._modal_recuperacion = None
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
        crear_separador(tarjeta).pack(fill="x", pady=(16, 10))

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
        btn_reg.pack(pady=(2, 6))
        btn_reg.bind("<Button-1>", lambda e: self.solicitar_registro())

        self.btn_recuperar = tk.Label(
            tarjeta,
            text="¿Olvidó su usuario o contraseña?",
            fg=COLOR_SECUNDARIO,
            bg=COLOR_TARJETA,
            font=FUENTE_PEQUEÑA_BOLD,
            cursor="hand2",
        )
        self.btn_recuperar.pack(pady=(2, 0))
        self.btn_recuperar.bind("<Button-1>", lambda e: self.abrir_modal_recuperacion())
        AyudaVisual(
            self.btn_recuperar,
            "Consultar usuarios activos o restablecer contraseña con clave maestra",
        )

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
                parent=self.root,
            )
            restaurar_foco(self.root)
            return

        usuario_autenticado = self.repo.autenticar(usuario, password)

        if usuario_autenticado:
            self.root.destroy()
            self.on_login_exitoso(usuario_autenticado)
        else:
            messagebox.showerror(
                "Acceso Denegado",
                "Usuario o contraseña incorrectos, o cuenta de usuario inactiva.",
                parent=self.root,
            )
            restaurar_foco(self.root)
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
        restaurar_foco(self.root)
        if clave is None:
            return

        try:
            ServicioPromocionDominio.validar_autorizacion(clave)
            self._abrir_modal_registro()
        except PermissionError as perm_err:
            messagebox.showerror("Acceso Denegado", str(perm_err), parent=self.root)
            restaurar_foco(self.root)

    def _abrir_modal_registro(self):
        """Ventana modal para dar de alta una nueva cuenta de usuario."""
        win = tk.Toplevel(self.root)
        win.title("Alta de Nuevo Usuario")
        win.resizable(False, False)
        win.config(bg=COLOR_FONDO_APP)
        centrar_ventana(win, 380, 460)
        configurar_ventana_hija(win, self.root, es_modal=True)
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
                messagebox.showinfo("Éxito", f"Usuario '{username}' registrado con rol '{rol}'.", parent=win)
                win.destroy()
            except ValueError as val_err:
                messagebox.showwarning("Dato Inválido", str(val_err), parent=win)
                restaurar_foco(win)
            except Exception as err:
                messagebox.showerror("Error al Guardar", str(err), parent=win)
                restaurar_foco(win)

        crear_boton(
            tarjeta, texto="💾  GUARDAR USUARIO", comando=guardar,
            color_bg=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER,
        ).pack(fill="x", pady=(20, 0), ipady=4)

    def abrir_modal_recuperacion(self):
        """
        Modal compacto de recuperación y restablecimiento offline en 2 pasos:
        1. Validación previa de Clave Maestra Institucional.
        2. Consulta de usuarios activos y restablecimiento de contraseña con auditoría.
        """
        win = tk.Toplevel(self.root)
        win.title("Recuperación Offline de Credenciales")
        win.resizable(False, False)
        win.config(bg=COLOR_FONDO_APP)
        centrar_ventana(win, 430, 480)
        configurar_ventana_hija(win, self.root, es_modal=True)
        win.grab_set()

        tarjeta = crear_tarjeta(win, padx=24, pady=20)
        tarjeta.pack(expand=True, fill="both", padx=18, pady=18)

        tk.Label(
            tarjeta, text="RECUPERACIÓN DE ACCESO",
            font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO,
        ).pack(pady=(0, 8))
        crear_separador(tarjeta).pack(fill="x", pady=(0, 12))

        # ── Paso 1: Validar Clave Maestra ──
        tk.Label(
            tarjeta, text="1. Clave Maestra Institucional:",
            bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x")

        e_maestra = tk.Entry(tarjeta, font=FUENTE_CUERPO, show="*", relief="solid", bd=1)
        e_maestra.pack(fill="x", pady=(4, 8), ipady=3)
        e_maestra.focus()

        lbl_estado = tk.Label(
            tarjeta, text="Valide la clave maestra para consultar usuarios activos.",
            bg=COLOR_TARJETA, fg=COLOR_TEXTO_SECUNDARIO, font=FUENTE_PEQUEÑA, anchor="w",
        )

        estado_modal = {"clave_validada": None}

        def validar_maestra():
            clave = e_maestra.get().strip()
            try:
                ServicioRecuperacionUsuario.validar_clave_maestra(clave)
            except PermissionError as err:
                messagebox.showerror("Acceso Denegado", str(err), parent=win)
                restaurar_foco(win)
                e_maestra.delete(0, tk.END)
                e_maestra.focus()
                return

            activos = self.repo.obtener_usernames_activos()
            if not activos:
                messagebox.showwarning(
                    "Sin Usuarios",
                    "No se encontraron usuarios activos en el sistema.",
                    parent=win,
                )
                restaurar_foco(win)
                return

            estado_modal["clave_validada"] = clave
            valores_combo = [f"{usr} - {rol}" for usr, rol in activos]
            c_usuarios["values"] = valores_combo
            c_usuarios.config(state="readonly")
            c_usuarios.current(0)

            e_nueva.config(state="normal")
            e_conf.config(state="normal")
            btn_restablecer.config(state="normal", bg=COLOR_ACENTO, cursor="hand2")
            e_maestra.config(state="disabled")
            btn_validar.config(state="disabled", bg="#BDC3C7", cursor="arrow")
            lbl_estado.config(
                text=f"✔ Clave validada ({len(activos)} usuario(s) activo(s)).",
                fg=COLOR_ACENTO,
            )
            e_nueva.focus()

        btn_validar = crear_boton(
            tarjeta, texto="🔑  Validar Clave Maestra", comando=validar_maestra,
            color_bg=COLOR_PRIMARIO, color_hover=COLOR_SECUNDARIO,
        )
        btn_validar.pack(fill="x", pady=(0, 6), ipady=2)
        AyudaVisual(btn_validar, "Autorizar consulta de usuarios activos y cambio de clave")
        lbl_estado.pack(fill="x", pady=(0, 10))

        crear_separador(tarjeta).pack(fill="x", pady=(0, 10))

        # ── Paso 2: Seleccionar usuario y restablecer contraseña ──
        tk.Label(
            tarjeta, text="2. Usuario Activo (consulta y restablecimiento):",
            bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x")
        c_usuarios = ttk.Combobox(tarjeta, state="disabled", font=FUENTE_CUERPO)
        c_usuarios.pack(fill="x", pady=(4, 8))

        tk.Label(
            tarjeta, text="Nueva Contraseña:",
            bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x")
        e_nueva = tk.Entry(tarjeta, font=FUENTE_CUERPO, show="*", relief="solid", bd=1, state="disabled")
        e_nueva.pack(fill="x", pady=(4, 8), ipady=3)

        tk.Label(
            tarjeta, text="Confirmar Contraseña:",
            bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL, font=FUENTE_ETIQUETA, anchor="w",
        ).pack(fill="x")
        e_conf = tk.Entry(tarjeta, font=FUENTE_CUERPO, show="*", relief="solid", bd=1, state="disabled")
        e_conf.pack(fill="x", pady=(4, 14), ipady=3)

        def restablecer():
            if not estado_modal["clave_validada"]:
                messagebox.showwarning(
                    "Autorización Requerida",
                    "Valide primero la Clave Maestra Institucional.",
                    parent=win,
                )
                restaurar_foco(win)
                return

            seleccion = c_usuarios.get().strip()
            if not seleccion:
                messagebox.showwarning("Usuario Requerido", "Seleccione un usuario activo.", parent=win)
                restaurar_foco(win)
                return

            username = seleccion.split(" - ", 1)[0].strip()
            pwd1 = e_nueva.get().strip()
            pwd2 = e_conf.get().strip()
            if pwd1 != pwd2:
                messagebox.showwarning(
                    "No Coinciden",
                    "La nueva contraseña y su confirmación no coinciden.",
                    parent=win,
                )
                restaurar_foco(win)
                e_conf.delete(0, tk.END)
                e_conf.focus()
                return

            try:
                self.repo.restablecer_contrasena_con_auditoria(
                    username=username,
                    nueva_password_plana=pwd1,
                    clave_maestra=estado_modal["clave_validada"],
                )
                messagebox.showinfo(
                    "Credenciales Restablecidas",
                    f"La contraseña de '{username}' fue actualizada correctamente.\n"
                    "Ya puede iniciar sesión con la nueva clave.",
                    parent=win,
                )
                win.destroy()
                restaurar_foco(self.root)
                self.entry_usuario.delete(0, tk.END)
                self.entry_usuario.insert(0, username)
                self.entry_password.delete(0, tk.END)
                self.entry_password.focus()
            except (PermissionError, ValueError) as err:
                messagebox.showwarning("Validación", str(err), parent=win)
                restaurar_foco(win)
            except Exception as err:
                messagebox.showerror("Error al Restablecer", str(err), parent=win)
                restaurar_foco(win)

        btn_restablecer = crear_boton(
            tarjeta, texto="💾  Restablecer Contraseña", comando=restablecer,
            color_bg=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER,
        )
        btn_restablecer.config(state="disabled", bg="#BDC3C7", cursor="arrow")
        btn_restablecer.pack(fill="x", ipady=4)
        AyudaVisual(btn_restablecer, "Guardar nueva contraseña y registrar auditoría")

        self._modal_recuperacion = {
            "win": win,
            "entry_maestra": e_maestra,
            "btn_validar": btn_validar,
            "combo_usuarios": c_usuarios,
            "entry_nueva": e_nueva,
            "entry_confirmar": e_conf,
            "btn_restablecer": btn_restablecer,
        }


# Alias para compatibilidad
LoginApp = VentanaLogin
