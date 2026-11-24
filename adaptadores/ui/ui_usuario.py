# adaptadores/ui/ui_usuario.py
"""
Adaptador de Interfaz de Usuario para Gestión de Usuarios.
Panel de Administración con CRUD, borrado lógico y verificación
de clave maestra a través del Servicio de Dominio (desacoplado).
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from dominio.usuario import Usuario
from dominio.promocion import ServicioPromocionDominio
from adaptadores.ui.utilidades_ui import (
    centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_PELIGRO, COLOR_PELIGRO_HOVER,
    COLOR_ADVERTENCIA, COLOR_ADVERTENCIA_HOVER,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO,
    COLOR_SEPARADOR, COLOR_BORDE_TARJETA,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_BOTON,
    crear_boton, crear_tarjeta, crear_separador,
    crear_treeview_zebra, insertar_fila_zebra,
    AyudaVisual, enfocar_siguiente,
)


class GestorUsuariosUI:
    """Panel de Administración de Usuarios (CRUD con Borrado Lógico)."""

    def __init__(self, parent_root, repositorio_usuario):
        self.repositorio = repositorio_usuario
        self.usuario_seleccionado_id = None

        # Validación de clave maestra a través del DOMINIO (no hardcodeada)
        clave_ingresada = simpledialog.askstring(
            "Seguridad", "Ingrese la Clave Maestra del Director:",
            show='*', parent=parent_root,
        )

        try:
            ServicioPromocionDominio.validar_autorizacion(clave_ingresada or "")
        except PermissionError:
            messagebox.showerror("Acceso Denegado", "Clave incorrecta. Acceso denegado.")
            return

        # Crear la ventana
        self.root = tk.Toplevel(parent_root)
        self.root.title("🔐 Panel de Seguridad y Usuarios")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 900, 600)
        maximizar_ventana(self.root)

        self.crear_interfaz()
        self.cargar_tabla()

    def crear_interfaz(self):
        # ═══ ENCABEZADO ═══
        f_header = tk.Frame(self.root, bg=COLOR_PRIMARIO, pady=12)
        f_header.pack(fill="x")
        tk.Label(f_header, text="⚙️  GESTIÓN DE USUARIOS DEL SISTEMA", font=FUENTE_SUBTITULO, bg=COLOR_PRIMARIO, fg=COLOR_TEXTO_CLARO).pack(side="left", padx=20)

        # ═══ FORMULARIO ═══
        tarjeta = crear_tarjeta(self.root, padx=20, pady=15)
        tarjeta.pack(fill="x", padx=15, pady=(10, 5))

        f_grid = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_grid.pack(fill="x")

        # Fila 1
        tk.Label(f_grid, text="Nombre Completo:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).grid(row=0, column=0, sticky="e", pady=6, padx=4)
        self.entry_nom = tk.Entry(f_grid, width=30, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_nom.grid(row=0, column=1, padx=5, pady=6)
        self.entry_nom.bind("<Return>", enfocar_siguiente)

        tk.Label(f_grid, text="Username (Login):", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).grid(row=0, column=2, sticky="e", pady=6, padx=4)
        self.entry_usr = tk.Entry(f_grid, width=20, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_usr.grid(row=0, column=3, padx=5, pady=6)
        self.entry_usr.bind("<Return>", enfocar_siguiente)
        AyudaVisual(self.entry_usr, "Ej: admin, jperez, director")

        # Fila 2
        tk.Label(f_grid, text="Contraseña:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).grid(row=1, column=0, sticky="e", pady=6, padx=4)
        self.entry_pwd = tk.Entry(f_grid, width=30, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_pwd.grid(row=1, column=1, padx=5, pady=6)
        self.entry_pwd.bind("<Return>", enfocar_siguiente)

        tk.Label(f_grid, text="Rol en el sistema:", bg=COLOR_TARJETA, font=FUENTE_ETIQUETA).grid(row=1, column=2, sticky="e", pady=6, padx=4)
        self.combo_rol = ttk.Combobox(f_grid, values=["ADMIN", "ASISTENTE", "DOCENTE"], state="readonly", width=17, font=FUENTE_CUERPO)
        self.combo_rol.grid(row=1, column=3, padx=5, pady=6)
        self.combo_rol.current(0)

        # Botones
        f_btn = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        f_btn.pack(fill="x", pady=(12, 0))

        crear_boton(f_btn, "💾  Guardar Nuevo", self.guardar, COLOR_ACENTO, COLOR_TEXTO_CLARO, COLOR_ACENTO_HOVER).pack(side="left", padx=4)
        crear_boton(f_btn, "✏️  Actualizar", self.actualizar, COLOR_ADVERTENCIA, COLOR_TEXTO_CLARO, COLOR_ADVERTENCIA_HOVER).pack(side="left", padx=4)
        crear_boton(f_btn, "🧹  Limpiar", self.limpiar, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="left", padx=4)
        btn_borrar = crear_boton(f_btn, "🗑️  Desactivar", self.desactivar, COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER)
        btn_borrar.pack(side="left", padx=4)
        AyudaVisual(btn_borrar, "Borrado lógico: el usuario pierde acceso pero se conserva el historial.")

        # ═══ TABLA DE USUARIOS (ZEBRA) ═══
        cols = ("ID", "Nombre", "Username", "Rol")
        encabezados = ["ID", "Nombre Completo", "Username", "Nivel de Acceso"]
        anchos = [50, 300, 150, 150]
        anclas = ["center", "w", "center", "center"]

        self.tree, frame_tree = crear_treeview_zebra(self.root, cols, encabezados, anchos, anclas, alto=10)
        frame_tree.pack(fill="both", expand=True, padx=15, pady=(5, 15))
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
            insertar_fila_zebra(self.tree, (u.id_usuario, u.nombre_completo, u.username, u.rol))

    def seleccionar_fila(self, event):
        item = self.tree.focus()
        if not item:
            return
        valores = self.tree.item(item)['values']
        self.limpiar()
        self.usuario_seleccionado_id = valores[0]
        self.entry_nom.insert(0, valores[1])
        self.entry_usr.insert(0, valores[2])
        self.entry_pwd.insert(0, "********")
        self.combo_rol.set(valores[3])

    def extraer_datos_ui(self):
        u = Usuario(
            nombre_completo=self.entry_nom.get().strip(),
            username=self.entry_usr.get().strip(),
            password=self.entry_pwd.get().strip(),
            rol=self.combo_rol.get(),
            id_usuario=self.usuario_seleccionado_id,
        )
        u.validar()
        return u

    def guardar(self):
        if self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Está intentando guardar un usuario que ya existe. Use 'Actualizar' o limpie las cajas.")
            return
        try:
            nuevo = self.extraer_datos_ui()
            self.repositorio.guardar(nuevo)
            messagebox.showinfo("Éxito", "Usuario creado correctamente.")
            self.limpiar()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar(self):
        if not self.usuario_seleccionado_id:
            return
        try:
            editado = self.extraer_datos_ui()
            if editado.password == "********":
                messagebox.showwarning("Clave", "Escriba una nueva contraseña para actualizar.")
                return
            self.repositorio.actualizar(editado)
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
            self.limpiar()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def desactivar(self):
        if not self.usuario_seleccionado_id:
            return
        try:
            if messagebox.askyesno("Confirmar", "¿Seguro que desea desactivar a este usuario?"):
                self.repositorio.desactivar(self.usuario_seleccionado_id)
                messagebox.showinfo("Desactivado", "Usuario revocado del sistema exitosamente.")
                self.limpiar()
                self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))
