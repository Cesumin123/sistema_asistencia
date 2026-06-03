# adaptadores/ui/utilidades_ui.py
import tkinter as tk

class AyudaVisual:
    """
    Caja de herramientas de Tkinter.
    Crea carteles amarillos (Tooltips) al pasar el mouse sobre un elemento.
    """
    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self.ventana_ayuda = None
        self.widget.bind("<Enter>", self.mostrar_cartel)
        self.widget.bind("<Leave>", self.ocultar_cartel)

    def mostrar_cartel(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.ventana_ayuda = tk.Toplevel(self.widget)
        self.ventana_ayuda.wm_overrideredirect(True) 
        self.ventana_ayuda.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.ventana_ayuda, text=self.texto, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def ocultar_cartel(self, event=None):
        if self.ventana_ayuda:
            self.ventana_ayuda.destroy()
            self.ventana_ayuda = None


def enfocar_siguiente(event):
    """
    Herramienta que cambia el foco al siguiente elemento al presionar Enter.
    El 'break' evita que Tkinter intente escribir un salto de línea.
    """
    event.widget.tk_focusNext().focus()
    return "break"