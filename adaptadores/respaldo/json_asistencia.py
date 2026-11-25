import json
import os
from typing import Optional

# Importamos el dominio y el puerto de emergencia
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from puertos.repositorio_asistencia import PuertoRespaldoEmergencia
from rutas_app import obtener_ruta_dato

class RespaldoAsistenciaJSON(PuertoRespaldoEmergencia):
    def __init__(self, ruta_archivo: Optional[str] = None):
        """
        Guardamos la ruta por defecto de forma portable junto al ejecutable,
        permitiendo pasar una ruta personalizada en pruebas.
        """
        self.ruta_archivo = ruta_archivo if ruta_archivo is not None else obtener_ruta_dato("memoria_emergencia.json")

    def guardar_respaldo(self, planilla: PlanillaAsistencia) -> None:
        # Asegurar directorio si es ruta personalizada
        directorio = os.path.dirname(self.ruta_archivo)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        # 1. Convertimos la planilla a un diccionario simple
        datos = {
            "id_clase": planilla.id_clase,
            "fecha": planilla.fecha,
            "registros": [
                {
                    "id_estudiante": reg.id_estudiante,
                    "estado": reg.estado.value,  # Guardamos "P", "A" o "J"
                    "motivo": reg.motivo_justificacion
                } for reg in planilla.registros
            ]
        }
        
        # 2. Escribimos en el archivo sobrescribiendo el anterior (modo "w")
        with open(self.ruta_archivo, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo)

    def recuperar_respaldo(self, id_clase: int, fecha: str) -> Optional[PlanillaAsistencia]:
        # Si no hay archivo de emergencia, no hacemos nada
        if not os.path.exists(self.ruta_archivo):
            return None
            
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as archivo:
                contenido = archivo.read().strip()
                if not contenido:
                    return None
                datos = json.loads(contenido)
            
            # --- BLINDAJE DEFENSIVO ANTE CORRUPCIÓN ---
            if not isinstance(datos, dict):
                return None
            
            # Verificamos que el archivo corresponda EXACTAMENTE a la clase y fecha actual
            if datos.get("id_clase") != id_clase or datos.get("fecha") != fecha:
                return None
            
            # Reconstruimos la planilla del dominio
            planilla = PlanillaAsistencia(id_clase=id_clase, fecha=fecha)
            registros_raw = datos.get("registros")
            if not isinstance(registros_raw, list):
                return None
            
            for item in registros_raw:
                if not isinstance(item, dict):
                    continue
                id_est = item.get("id_estudiante")
                estado_val = item.get("estado")
                if not id_est or not estado_val:
                    continue
                try:
                    estado_enum = EstadoAsistencia(estado_val)
                except ValueError:
                    continue

                registro = RegistroAsistencia(
                    id_estudiante=str(id_est),
                    estado=estado_enum,
                    motivo_justificacion=item.get("motivo")
                )
                planilla.registros.append(registro)
                
            return planilla
            
        except Exception:
            # Resiliencia: si el archivo se corrompió o truncó por apagón repentino,
            # lo ignoramos defensivamente sin tumbar el programa.
            return None

    def limpiar_respaldo(self) -> None:
        """Borra el archivo temporal una vez que se guardó en la BD oficial."""
        if os.path.exists(self.ruta_archivo):
            try:
                os.remove(self.ruta_archivo)
            except OSError:
                pass