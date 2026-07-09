import json
import os
from typing import Optional

# Importamos el dominio y el puerto de emergencia
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from puertos.repositorio_asistencia import PuertoRespaldoEmergencia

class RespaldoAsistenciaJSON(PuertoRespaldoEmergencia):
    def __init__(self, ruta_archivo: str = "memoria_emergencia.json"):
        """
         Guardamos la ruta por defecto, pero permitimos cambiarla si es necesario.
        """
        self.ruta_archivo = ruta_archivo

    def guardar_respaldo(self, planilla: PlanillaAsistencia) -> None:
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
                datos = json.load(archivo)
            
            # --- BLINDAJE KISS ---
            # Verificamos que el archivo corresponda EXACTAMENTE a la clase y fecha actual
            if datos.get("id_clase") != id_clase or datos.get("fecha") != fecha:
                return None
            
            # Reconstruimos la planilla del dominio
            planilla = PlanillaAsistencia(id_clase=id_clase, fecha=fecha)
            
            for item in datos.get("registros", []):
                registro = RegistroAsistencia(
                    id_estudiante=item["id_estudiante"],
                    estado=EstadoAsistencia(item["estado"]),
                    motivo_justificacion=item.get("motivo")
                )
                planilla.registros.append(registro)
                
            return planilla
            
        except Exception as error:
            # KISS: Si el archivo se corrompió a la mitad de un apagón, 
            # simplemente lo ignoramos para no tumbar el programa.
            print(f"No se pudo recuperar el respaldo: {error}")
            return None

    def limpiar_respaldo(self) -> None:
        """Borra el archivo temporal una vez que se guardó en la BD oficial."""
        if os.path.exists(self.ruta_archivo):
            os.remove(self.ruta_archivo)