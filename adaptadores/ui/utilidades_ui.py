# adaptadores/ui/utilidades_ui.py
import tkinter as tk

class AyudaVisual:
    """
    Implementación de Tooltips (mensajes emergentes) para componentes de Tkinter.
    
    Esta clase gestiona la aparición y desaparición de pequeñas ventanas flotantes
    con información contextual cuando el usuario posiciona el puntero del ratón
    sobre un widget específico.
    """

    def __init__(self, widget, texto):
        """
        Inicializa la ayuda visual para un widget determinado.

        Args:
            widget (tk.Widget): El componente de la interfaz al que se asociará la ayuda.
            texto (str): El mensaje informativo que se mostrará al usuario.
        """
        self.widget = widget
        self.texto = texto
        self.ventana_ayuda = None
        
        # Vinculación de eventos del ratón para controlar el ciclo de vida del tooltip
        self.widget.bind("<Enter>", self.mostrar_cartel)
        self.widget.bind("<Leave>", self.ocultar_cartel)

    def mostrar_cartel(self, event=None):
        """
        Calcula la posición y crea la ventana flotante con el texto de ayuda.

        Utiliza las coordenadas globales del widget para posicionar la ventana
        emergente ligeramente desplazada del cursor.

        Args:
            event (tk.Event, opcional): Evento de entrada del ratón disparado por el widget.
        """
        # Intenta obtener coordenadas del cursor; no todos los widgets soportan 'insert'
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            # Si no existe, posicionamos cerca del widget
            x, y = 0, 0
        
        # Calcula la posición absoluta en la pantalla
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        
        # Creación de una ventana de nivel superior (TopLevel) sin decoraciones de SO
        self.ventana_ayuda = tk.Toplevel(self.widget)
        self.ventana_ayuda.wm_overrideredirect(True) 
        self.ventana_ayuda.wm_geometry(f"+{x}+{y}")
        
        # Configuración visual del contenedor del texto
        label = tk.Label(self.ventana_ayuda, text=self.texto, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def ocultar_cartel(self, event=None):
        """
        Destruye la ventana de ayuda actual y libera el recurso.

        Args:
            event (tk.Event, opcional): Evento de salida del ratón disparado por el widget.
        """
        if self.ventana_ayuda:
            self.ventana_ayuda.destroy()
            self.ventana_ayuda = None


def enfocar_siguiente(event):
    """
    Gestiona el cambio de foco entre componentes mediante el teclado.

    Esta función permite que el usuario navegue a través de los campos de entrada
    presionando la tecla 'Enter' en lugar de la tecla 'Tab'.

    Args:
        event (tk.Event): Evento de teclado originado en el widget actual.

    Returns:
        str: "break", indicando a Tkinter que detenga la propagación del evento
             y evite comportamientos por defecto (como saltos de línea en Text widgets).
    """
    # Localiza el siguiente widget en el orden de tabulación y le otorga el foco
    event.widget.tk_focusNext().focus()
    return "break"
