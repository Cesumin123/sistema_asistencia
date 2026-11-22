# adaptadores/ui/ui_promocion.py
"""
Adaptador de Interfaz de Usuario para Promoción Anual en Cascada (RF-16).
Completamente desacoplado de SQL: interactúa únicamente con el puerto
PuertoRepositorioPromocion y el servicio de dominio ServicioPromocionDominio.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from puertos.repositorio_promocion import PuertoRepositorioPromocion
from dominio.promocion import ServicioPromocionDominio


class UIPromocion:
    """
    Interfaz gráfica para el cierre del año escolar y promoción en cascada descendente.
    """

    def __init__(
        self,
        repo_promocion: PuertoRepositorioPromocion,
        parent: Optional[tk.Widget] = None,
        usuario_actual: str = "ADMIN"
    ):
        self.repo = repo_promocion
        self.usuario_actual = usuario_actual

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Cierre y Promoción de Año Escolar (Hexagonal)")
        self.root.geometry("750x600")
        try:
            self.root.state('zoomed')
        except Exception:
            pass

        self._crear_interfaz()
        self.cargar_vista_previa()

    def _crear_interfaz(self):
        """Construye los widgets de advertencia, vista previa y botones de acción."""
        # Panel superior de advertencia en color rojo/peligro
        frame_alerta = tk.Frame(self.root, bg="#c0392b", pady=15)
        frame_alerta.pack(fill="x")

        tk.Label(
            frame_alerta,
            text="⚠️ ZONA DE ALTO RIESGO — CIERRE DE AÑO ESCOLAR",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#c0392b"
        ).pack()

        texto_advertencia = (
            "Esta operación promueve a todos los alumnos ACTIVOS al grado inmediato superior:\n"
            "• 5to Año pasa a 6to Año (GRADUADO).\n"
            "• 4to Año pasa a 5to Año | 3ro a 4to | 2do a 3ro | 1ro a 2do.\n"
            "• Los estudiantes inactivos no son alterados.\n"
            "¡Esta acción es irreversible y requiere la Clave Maestra Administrativa!"
        )
        tk.Label(
            frame_alerta,
            text=texto_advertencia,
            font=("Arial", 10),
            fg="#fdfefe",
            bg="#c0392b",
            justify="center"
        ).pack(pady=8)

        # Contenedor central para la vista previa por grado
        frame_central = tk.Frame(self.root, padx=25, pady=15)
        frame_central.pack(fill="both", expand=True)

        tk.Label(
            frame_central,
            text="Vista Previa de Alumnos Activos por Grado Actual:",
            font=("Arial", 11, "bold"),
            fg="#2c3e50"
        ).pack(anchor="w", pady=5)

        columnas = ("id_grado", "grado", "alumnos_activos", "destino")
        self.tree = ttk.Treeview(frame_central, columns=columnas, show="headings", height=8)

        self.tree.heading("id_grado", text="ID")
        self.tree.column("id_grado", width=40, anchor="center")
        self.tree.heading("grado", text="Grado / Año Actual")
        self.tree.column("grado", width=220, anchor="w")
        self.tree.heading("alumnos_activos", text="Alumnos Activos")
        self.tree.column("alumnos_activos", width=120, anchor="center")
        self.tree.heading("destino", text="Destino tras Promoción")
        self.tree.column("destino", width=220, anchor="w")

        self.tree.pack(fill="both", expand=True)

        # Botón para refrescar vista previa
        f_refresh = tk.Frame(frame_central, pady=5)
        f_refresh.pack(fill="x")
        tk.Button(
            f_refresh,
            text="🔄 Refrescar Censo",
            command=self.cargar_vista_previa,
            cursor="hand2"
        ).pack(side="right")

        # Botonera de Ejecución protegida
        frame_accion = tk.Frame(self.root, pady=20)
        frame_accion.pack()

        self.btn_ejecutar = tk.Button(
            frame_accion,
            text="🔒 EJECUTAR PROMOCIÓN EN CASCADA",
            font=("Arial", 12, "bold"),
            bg="#c0392b",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.solicitar_promocion
        )
        self.btn_ejecutar.pack()

    def cargar_vista_previa(self):
        """Carga en el Treeview la cantidad de alumnos por grado actual."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        mapa_destinos = {
            1: "2do AÑO",
            2: "3er AÑO",
            3: "4to AÑO",
            4: "5to AÑO",
            5: "GRADUADO / EGRESADO",
            6: "Ya Graduado (Sin Cambio)"
        }

        try:
            resumen = self.repo.obtener_resumen_grados()
            for r in resumen:
                destino = mapa_destinos.get(r.id_grado, "Sin Cambio")
                self.tree.insert(
                    "", "end",
                    values=(r.id_grado, r.descripcion, r.total_estudiantes, destino)
                )
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar la vista previa: {error}")

    def solicitar_promocion(self):
        """
        Flujo de doble verificación de seguridad:
        1. Confirmación de intención.
        2. Solicitud y validación de la Clave Maestra.
        3. Ejecución atómica en base de datos.
        """
        # Paso 1: Confirmación de advertencia
        confirmado = messagebox.askyesno(
            "Confirmación Crítica",
            "¿Está completamente seguro de promover a todos los estudiantes activos al siguiente año escolar?\n\n"
            "Esta operación modificará los registros de la institución y no se puede deshacer.",
            icon="warning"
        )
        if not confirmado:
            return

        # Paso 2: Solicitud de Clave Maestra
        clave = simpledialog.askstring(
            "Autorización Administrativa",
            "Ingrese la CLAVE MAESTRA para autorizar la promoción:",
            show="*",
            parent=self.root
        )

        if not clave:
            messagebox.showinfo("Cancelado", "Operación cancelada. No se ingresó clave de seguridad.")
            return

        # Paso 3: Validación a través del Servicio de Dominio
        try:
            ServicioPromocionDominio.validar_autorizacion(clave)
        except PermissionError as perm_err:
            messagebox.showerror("Acceso Denegado", str(perm_err))
            return

        # Paso 4: Ejecución a través del Adaptador de Persistencia
        try:
            resultado = self.repo.ejecutar_promocion_cascada(usuario_responsable=self.usuario_actual)
            messagebox.showinfo(
                "¡Proceso Exitoso!",
                f"{resultado.mensaje}\n\n¡Feliz Nuevo Año Escolar!"
            )
            self.cargar_vista_previa()
        except Exception as error:
            messagebox.showerror("Fallo Crítico", f"Error al ejecutar la promoción: {error}")


# Alias para compatibilidad
GestorPromocionUI = UIPromocion
