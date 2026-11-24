# adaptadores/ui/ui_promocion.py
"""
Adaptador de Interfaz de Usuario para Promoción Anual en Cascada (RF-16).
Desacoplado de SQL. Confirmación visual destacada de alto riesgo,
alertas claras y verificación de clave maestra a través del dominio.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from puertos.repositorio_promocion import PuertoRepositorioPromocion
from dominio.promocion import ServicioPromocionDominio
from adaptadores.ui.utilidades_ui import (
    centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER, COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_CLARO, COLOR_SEPARADOR,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD,
    crear_boton, crear_tarjeta, crear_separador,
    crear_treeview_zebra, insertar_fila_zebra,
)


class UIPromocion:
    """Interfaz gráfica para el cierre del año escolar y promoción en cascada."""

    def __init__(self, repo_promocion: PuertoRepositorioPromocion,
                 parent: Optional[tk.Widget] = None,
                 usuario_actual: str = "ADMIN"):
        self.repo = repo_promocion
        self.usuario_actual = usuario_actual

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Cierre y Promoción de Año Escolar")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 800, 650)
        maximizar_ventana(self.root)

        self._crear_interfaz()
        self.cargar_vista_previa()

    def _crear_interfaz(self):
        # ═══ BANNER DE ADVERTENCIA ROJO ═══
        f_alerta = tk.Frame(self.root, bg=COLOR_PELIGRO, pady=15)
        f_alerta.pack(fill="x")

        tk.Label(f_alerta, text="⚠️  ZONA DE ALTO RIESGO — CIERRE DE AÑO ESCOLAR", font=FUENTE_SUBTITULO, fg=COLOR_TEXTO_CLARO, bg=COLOR_PELIGRO).pack()

        texto_adv = (
            "Esta operación promueve a todos los alumnos ACTIVOS al grado superior:\n"
            "• 5to → GRADUADO  |  4to → 5to  |  3ro → 4to  |  2do → 3ro  |  1ro → 2do\n"
            "• Los estudiantes inactivos no son alterados.\n"
            "¡Esta acción es IRREVERSIBLE y requiere la Clave Maestra!"
        )
        tk.Label(f_alerta, text=texto_adv, font=FUENTE_PEQUEÑA, fg="#FDFEFE", bg=COLOR_PELIGRO, justify="center").pack(pady=8)

        # ═══ VISTA PREVIA ═══
        f_central = tk.Frame(self.root, bg=COLOR_FONDO_APP, padx=25, pady=15)
        f_central.pack(fill="both", expand=True)

        tk.Label(f_central, text="Vista Previa de Alumnos Activos por Grado:", font=FUENTE_ETIQUETA, fg=COLOR_TEXTO_PRINCIPAL, bg=COLOR_FONDO_APP).pack(anchor="w", pady=5)

        cols = ("id_grado", "grado", "alumnos_activos", "destino")
        enc = ["ID", "Grado / Año Actual", "Alumnos Activos", "Destino tras Promoción"]
        anch = [40, 220, 120, 220]
        anclas = ["center", "w", "center", "w"]

        self.tree, frame_tree = crear_treeview_zebra(f_central, cols, enc, anch, anclas, alto=8)
        frame_tree.pack(fill="both", expand=True)

        # Refrescar
        f_refresh = tk.Frame(f_central, bg=COLOR_FONDO_APP, pady=5)
        f_refresh.pack(fill="x")
        crear_boton(f_refresh, "🔄 Refrescar Censo", self.cargar_vista_previa, "#95A5A6", COLOR_TEXTO_CLARO).pack(side="right")

        # ═══ BOTÓN DE EJECUCIÓN ═══
        f_accion = tk.Frame(self.root, bg=COLOR_FONDO_APP, pady=15)
        f_accion.pack()

        crear_boton(
            f_accion, "🔒  EJECUTAR PROMOCIÓN EN CASCADA",
            self.solicitar_promocion, COLOR_PELIGRO, COLOR_TEXTO_CLARO,
            COLOR_PELIGRO_HOVER,
            fuente=FUENTE_ENCABEZADO,
        ).pack(ipady=6, ipadx=20)

    def cargar_vista_previa(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        mapa_destinos = {
            1: "2do AÑO", 2: "3er AÑO", 3: "4to AÑO",
            4: "5to AÑO", 5: "GRADUADO / EGRESADO", 6: "Ya Graduado (Sin Cambio)",
        }

        try:
            resumen = self.repo.obtener_resumen_grados()
            for r in resumen:
                destino = mapa_destinos.get(r.id_grado, "Sin Cambio")
                insertar_fila_zebra(self.tree, (r.id_grado, r.descripcion, r.total_estudiantes, destino))
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar la vista previa: {error}")

    def solicitar_promocion(self):
        confirmado = messagebox.askyesno(
            "Confirmación Crítica",
            "¿Está completamente seguro de promover a todos los estudiantes activos?\n\n"
            "Esta operación modifica los registros y NO se puede deshacer.",
            icon="warning",
        )
        if not confirmado:
            return

        clave = simpledialog.askstring(
            "Autorización Administrativa",
            "Ingrese la CLAVE MAESTRA para autorizar la promoción:",
            show="*", parent=self.root,
        )
        if not clave:
            messagebox.showinfo("Cancelado", "Operación cancelada.")
            return

        try:
            ServicioPromocionDominio.validar_autorizacion(clave)
        except PermissionError as perm_err:
            messagebox.showerror("Acceso Denegado", str(perm_err))
            return

        try:
            resultado = self.repo.ejecutar_promocion_cascada(usuario_responsable=self.usuario_actual)
            messagebox.showinfo("¡Proceso Exitoso!", f"{resultado.mensaje}\n\n¡Feliz Nuevo Año Escolar!")
            self.cargar_vista_previa()
        except Exception as error:
            messagebox.showerror("Fallo Crítico", f"Error al ejecutar: {error}")


# Alias
GestorPromocionUI = UIPromocion
