# tests/test_respaldo_json.py
import os
import json
import pytest
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON

def test_guardar_y_recuperar_respaldo_concordante(tmp_path):
    """Verifica que el respaldo síncrono guarde y recupere fielmente los datos."""
    archivo_json = str(tmp_path / "test_emergencia.json")
    respaldo = RespaldoAsistenciaJSON(ruta_archivo=archivo_json)
    
    reg1 = RegistroAsistencia(id_estudiante="V-100", estado=EstadoAsistencia.PRESENTE)
    reg2 = RegistroAsistencia(id_estudiante="V-200", estado=EstadoAsistencia.JUSTIFICADO, motivo_justificacion="Consulta odontológica")
    reg3 = RegistroAsistencia(id_estudiante="V-300", estado=EstadoAsistencia.AUSENTE)
    planilla_original = PlanillaAsistencia(id_clase=10, fecha="2026-11-21", registros=[reg1, reg2, reg3])
    
    # 1. Guardar respaldo
    respaldo.guardar_respaldo(planilla_original)
    assert os.path.exists(archivo_json)
    
    # Verificar formato JSON interno
    with open(archivo_json, "r", encoding="utf-8") as f:
        datos = json.load(f)
    assert datos["id_clase"] == 10
    assert datos["fecha"] == "2026-11-21"
    assert len(datos["registros"]) == 3
    
    # 2. Recuperar respaldo concordante
    recuperada = respaldo.recuperar_respaldo(id_clase=10, fecha="2026-11-21")
    assert recuperada is not None
    assert recuperada.id_clase == 10
    assert recuperada.fecha == "2026-11-21"
    assert len(recuperada.registros) == 3
    
    r1, r2, r3 = recuperada.registros
    assert r1.id_estudiante == "V-100" and r1.estado == EstadoAsistencia.PRESENTE
    assert r2.id_estudiante == "V-200" and r2.estado == EstadoAsistencia.JUSTIFICADO and r2.motivo_justificacion == "Consulta odontológica"
    assert r3.id_estudiante == "V-300" and r3.estado == EstadoAsistencia.AUSENTE

def test_recuperar_respaldo_inconcordante(tmp_path):
    """Un respaldo de otra clase u otra fecha debe ser descartado (retornar None)."""
    archivo_json = str(tmp_path / "test_emergencia.json")
    respaldo = RespaldoAsistenciaJSON(ruta_archivo=archivo_json)
    
    planilla = PlanillaAsistencia(id_clase=5, fecha="2026-11-21", registros=[RegistroAsistencia("V-100")])
    respaldo.guardar_respaldo(planilla)
    
    # Intento con distinta clase
    assert respaldo.recuperar_respaldo(id_clase=99, fecha="2026-11-21") is None
    
    # Intento con distinta fecha
    assert respaldo.recuperar_respaldo(id_clase=5, fecha="2026-11-22") is None

def test_recuperar_sin_archivo_existente(tmp_path):
    """Si no hay archivo de emergencia, debe retornar None sin lanzar excepciones."""
    archivo_json = str(tmp_path / "inexistente.json")
    respaldo = RespaldoAsistenciaJSON(ruta_archivo=archivo_json)
    assert respaldo.recuperar_respaldo(id_clase=1, fecha="2026-11-21") is None

def test_limpiar_respaldo(tmp_path):
    """Verifica que limpiar_respaldo elimine el archivo físico y sea idempotente."""
    archivo_json = str(tmp_path / "test_emergencia.json")
    respaldo = RespaldoAsistenciaJSON(ruta_archivo=archivo_json)
    
    planilla = PlanillaAsistencia(id_clase=1, fecha="2026-11-21", registros=[])
    respaldo.guardar_respaldo(planilla)
    assert os.path.exists(archivo_json)
    
    respaldo.limpiar_respaldo()
    assert not os.path.exists(archivo_json)
    
    # Llamar de nuevo no debe fallar
    respaldo.limpiar_respaldo()
