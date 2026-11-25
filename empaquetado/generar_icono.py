# empaquetado/generar_icono.py
"""
Genera `empaquetado/icono_colegio.ico` multi-resolución a partir del escudo
institucional `LOGOLICEO.png` usando Pillow.
"""

import os
import sys
from PIL import Image

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from rutas_app import obtener_ruta_recurso  # noqa: E402

TAMANOS_ICO = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def generar_icono(ruta_salida: str | None = None) -> str:
    """Convierte LOGOLICEO.png en un archivo .ico multi-resolución para Windows."""
    ruta_logo = obtener_ruta_recurso("LOGOLICEO.png")
    if not os.path.exists(ruta_logo):
        raise FileNotFoundError(f"No se encontró el logo institucional en: {ruta_logo}")

    if ruta_salida is None:
        ruta_salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono_colegio.ico")

    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)

    with Image.open(ruta_logo) as img:
        img_rgba = img.convert("RGBA")
        # Centrar en lienzo cuadrado manteniendo proporción antes de exportar tamaños .ico
        lado = max(img_rgba.size)
        lienzo = Image.new("RGBA", (lado, lado), (255, 255, 255, 0))
        offset_x = (lado - img_rgba.width) // 2
        offset_y = (lado - img_rgba.height) // 2
        lienzo.paste(img_rgba, (offset_x, offset_y), img_rgba)
        lienzo.save(ruta_salida, format="ICO", sizes=TAMANOS_ICO)

    return ruta_salida


if __name__ == "__main__":
    destino = generar_icono()
    print(f"Icono generado correctamente en: {destino}")
