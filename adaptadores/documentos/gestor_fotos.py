# adaptadores/documentos/gestor_fotos.py
"""
Adaptador de Gestión de Fotografías de Profesores y Estudiantes.
Almacena imágenes en formato JPEG optimizado (240x240 px) en rutas relativas POSIX
para garantizar portabilidad USB (RNF-07), sin usar BLOBs en SQLite ni rutas absolutas fijas.
"""

import os
import re
from typing import Optional, Tuple, Any
from PIL import Image, ImageOps, ImageTk

from rutas_app import obtener_directorio_datos


class GestorFotos:
    """
    Gestiona el almacenamiento, resolución y vistas previas de fotografías
    institucionales (Profesores y Estudiantes).
    """

    def __init__(self, directorio_base: Optional[str] = None):
        if directorio_base is not None:
            self.directorio_base = os.path.abspath(directorio_base)
        else:
            self.directorio_base = obtener_directorio_datos()

    @staticmethod
    def sanitizar_cedula(cedula: str) -> str:
        """Sanitiza una cédula para que sea un nombre de archivo seguro en Windows y Linux."""
        if not cedula:
            return "sin_identificacion"
        # Reemplazar caracteres no alfanuméricos por guion bajo
        limpio = re.sub(r"[^A-Za-z0-9]", "_", str(cedula).strip())
        # Colapsar guiones bajos repetidos
        limpio = re.sub(r"_+", "_", limpio).strip("_")
        return limpio or "foto"

    def guardar_foto(self, ruta_origen: str, tipo_entidad: str, cedula: str) -> str:
        """
        Procesa y almacena la fotografía seleccionada:
        - Ajusta proporcionalmente con ImageOps.fit a 240x240 px (LANCZOS).
        - Convierte a RGB.
        - Guarda como JPEG optimizado (calidad 85).
        - Retorna únicamente la ruta relativa POSIX (ej. 'fotos/estudiantes/V_31201101.jpg').
        """
        if not os.path.exists(ruta_origen):
            raise FileNotFoundError(f"El archivo de imagen no existe: {ruta_origen}")

        tipo_norm = "profesores" if "prof" in tipo_entidad.lower() else "estudiantes"
        carpeta_destino = os.path.join(self.directorio_base, "fotos", tipo_norm)
        os.makedirs(carpeta_destino, exist_ok=True)

        nombre_archivo = f"{self.sanitizar_cedula(cedula)}.jpg"
        ruta_absoluta_destino = os.path.join(carpeta_destino, nombre_archivo)

        with Image.open(ruta_origen) as img:
            # Convertir a RGB (manejando RGBA o modos con transparencia con fondo blanco)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img_rgb = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                img_rgb.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            else:
                img_rgb = img.convert("RGB")

            # Recorte centrado a 240x240 con alta calidad
            img_redim = ImageOps.fit(img_rgb, (240, 240), method=Image.Resampling.LANCZOS)
            img_redim.save(ruta_absoluta_destino, "JPEG", quality=85, optimize=True)

        # Retornar ruta relativa normalizada con barras POSIX para portabilidad SQLite
        return f"fotos/{tipo_norm}/{nombre_archivo}"

    def resolver_ruta_absoluta(self, ruta_relativa: Optional[str]) -> Optional[str]:
        """
        Resuelve la ruta absoluta en tiempo de ejecución.
        Retorna la ruta normalizada si existe el archivo, o None si no existe o ruta está vacía.
        """
        if not ruta_relativa or not str(ruta_relativa).strip():
            return None

        ruta_limpia = str(ruta_relativa).strip()

        # Si ya es absoluta y existe físicamente
        if os.path.isabs(ruta_limpia) and os.path.exists(ruta_limpia):
            return os.path.normpath(ruta_limpia)

        # Resolver relativa al directorio base
        ruta_abs = os.path.normpath(os.path.join(self.directorio_base, ruta_limpia.replace("/", os.sep)))
        if os.path.exists(ruta_abs):
            return ruta_abs

        return None

    def cargar_preview_tk(
        self,
        ruta_relativa_o_abs: Optional[str],
        tamano: Tuple[int, int] = (110, 110),
        master: Optional[Any] = None
    ) -> Optional[ImageTk.PhotoImage]:
        """
        Carga de forma segura una imagen Tkinter PhotoImage redimensionada.
        Retorna None sin lanzar excepciones si la imagen no existe o está corrupta.
        """
        ruta_real = self.resolver_ruta_absoluta(ruta_relativa_o_abs)
        if not ruta_real:
            return None

        try:
            with Image.open(ruta_real) as img:
                img_redim = ImageOps.fit(img.convert("RGB"), tamano, method=Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img_redim, master=master)
        except Exception:
            return None

    def eliminar_foto(self, ruta_relativa: Optional[str]) -> bool:
        """Elimina el archivo físico de la fotografía si existe."""
        ruta_real = self.resolver_ruta_absoluta(ruta_relativa)
        if ruta_real and os.path.exists(ruta_real):
            try:
                os.remove(ruta_real)
                return True
            except OSError:
                return False
        return False
