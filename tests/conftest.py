# tests/conftest.py
"""
Fixtures compartidos para pruebas UI con Tkinter y Pillow.

Mantiene una única instancia raíz `tk.Tk()` viva durante toda la sesión de pytest
(`_session_tk`), evitando la creación y destrucción repetida de intérpretes Tcl que
provoca errores use-after-free en `PIL._imagingtk` bajo Xvfb headless.
"""

import gc
import tkinter as tk
import pytest


def _soltar_referencias_imagenes(widget):
    """Limpia recursivamente referencias PhotoImage en widgets antes de destruirlos."""
    try:
        hijos = list(widget.winfo_children())
    except Exception:
        hijos = []

    for child in hijos:
        _soltar_referencias_imagenes(child)

    for attr in ("image", "_foto_preview_ref", "preview_foto_tk", "img_logo_tk", "logo_tk"):
        if hasattr(widget, attr):
            try:
                setattr(widget, attr, None)
            except Exception:
                pass

    try:
        widget.configure(image="")
    except Exception:
        pass


@pytest.fixture(scope="session")
def _session_tk():
    """Única instancia raíz tk.Tk() oculta para toda la sesión de pruebas."""
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Entorno gráfico Tkinter no disponible.")
        return

    yield root

    try:
        for child in list(root.winfo_children()):
            _soltar_referencias_imagenes(child)
            try:
                child.destroy()
            except Exception:
                pass
        _soltar_referencias_imagenes(root)
        root.update_idletasks()
    except Exception:
        pass

    gc.collect()
    try:
        if root.winfo_exists():
            root.destroy()
    except Exception:
        pass
    gc.collect()


@pytest.fixture(scope="function")
def tk_root(_session_tk):
    """
    Provee un Toplevel aislado y oculto por test sobre el único intérprete Tcl activo.
    Destruye ventanas hijas y recolecta PhotoImage mientras `_session_tk` sigue vivo.
    """
    win = tk.Toplevel(_session_tk)
    win.withdraw()
    yield win

    try:
        hijos_sesion = [c for c in list(_session_tk.winfo_children()) if c is not win]
    except Exception:
        hijos_sesion = []

    for ventana in [win] + hijos_sesion:
        try:
            if ventana.winfo_exists():
                _soltar_referencias_imagenes(ventana)
                ventana.update_idletasks()
                ventana.destroy()
        except Exception:
            pass

    gc.collect()


@pytest.fixture(scope="function")
def tk_app(tk_root):
    """Alias compatible de `tk_root` para pruebas de integración UI."""
    return tk_root
