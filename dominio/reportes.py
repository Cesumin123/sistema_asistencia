# dominio/reportes.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class AsistenciaEnriquecida:
    """Data Transfer Object que combina la asistencia con datos básicos del estudiante para análisis."""
    id_estudiante: str
    nombre: str
    genero: str
    fecha: str
    estado: str  # 'P', 'A', 'J'

@dataclass
class AlertaRiesgo:
    """Entidad que representa a un alumno en peligro de perder el año por inasistencia."""
    id_estudiante: str
    nombre: str
    faltas_injustificadas: int

    @property
    def es_critico(self) -> bool:
        """Regla de negocio: Más de 3 faltas es crítico."""
        return self.faltas_injustificadas > 3


class AnalizadorEstadistico:
    """
    Servicio de Dominio. 
    Contiene la inteligencia del módulo sin tocar bases de datos ni UI.
    """
    
    @staticmethod
    def detectar_riesgo(registros: List[AsistenciaEnriquecida]) -> List[AlertaRiesgo]:
        conteo_faltas = {}
        nombres = {}
        
        for reg in registros:
            if reg.estado == 'A':
                conteo_faltas[reg.id_estudiante] = conteo_faltas.get(reg.id_estudiante, 0) + 1
                nombres[reg.id_estudiante] = reg.nombre
                
        alertas = []
        for id_est, faltas in conteo_faltas.items():
            alerta = AlertaRiesgo(id_estudiante=id_est, nombre=nombres[id_est], faltas_injustificadas=faltas)
            if alerta.es_critico:
                alertas.append(alerta)
                
        # Ordenamos de mayor a menor riesgo
        return sorted(alertas, key=lambda x: x.faltas_injustificadas, reverse=True)

    @staticmethod
    def calcular_demografia(registros: List[AsistenciaEnriquecida]) -> Dict[str, int]:
        """Calcula estadísticas descriptivas (Varones vs Hembras presentes/ausentes)."""
        stats = {
            "masculino_presente": 0, "masculino_ausente": 0,
            "femenino_presente": 0, "femenino_ausente": 0
        }
        
        for reg in registros:
            clave_genero = "masculino" if reg.genero.upper() == "M" else "femenino"
            clave_estado = "presente" if reg.estado in ('P', 'J') else "ausente"
            stats[f"{clave_genero}_{clave_estado}"] += 1
            
        return stats