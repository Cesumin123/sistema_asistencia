# tests/test_dominio_asistencia.py
import pytest
from dominio.asistencia import EstadoAsistencia, RegistroAsistencia, PlanillaAsistencia

def test_estado_asistencia_valores():
    """Verifica que el enum tenga las opciones legales requeridas."""
    assert EstadoAsistencia.PRESENTE.value == "P"
    assert EstadoAsistencia.AUSENTE.value == "A"
    assert EstadoAsistencia.JUSTIFICADO.value == "J"

def test_registro_asistencia_estado_inicial():
    """Un registro nuevo debe iniciar por defecto como PRESENTE y sin justificación."""
    reg = RegistroAsistencia(id_estudiante="V-12345678")
    assert reg.id_estudiante == "V-12345678"
    assert reg.estado == EstadoAsistencia.PRESENTE
    assert reg.motivo_justificacion is None

def test_registro_asistencia_transiciones():
    """Prueba las transiciones de estado y la limpieza de motivo."""
    reg = RegistroAsistencia(id_estudiante="V-12345678")
    
    # Justificar
    reg.justificar("Cita médica comprobada")
    assert reg.estado == EstadoAsistencia.JUSTIFICADO
    assert reg.motivo_justificacion == "Cita médica comprobada"
    
    # Pasar a Ausente (debe limpiar motivo)
    reg.marcar_ausente()
    assert reg.estado == EstadoAsistencia.AUSENTE
    assert reg.motivo_justificacion is None
    
    # Pasar a Presente (debe limpiar motivo)
    reg.justificar("Permiso")
    reg.marcar_presente()
    assert reg.estado == EstadoAsistencia.PRESENTE
    assert reg.motivo_justificacion is None

def test_planilla_asistencia_actualizar_registro():
    """Verifica la lógica de negocio de actualización dentro de la raíz del agregado."""
    reg1 = RegistroAsistencia(id_estudiante="V-11111111")
    reg2 = RegistroAsistencia(id_estudiante="V-22222222")
    planilla = PlanillaAsistencia(id_clase=1, fecha="2026-11-21", registros=[reg1, reg2])
    
    # Modificar reg1 a Justificado
    planilla.actualizar_registro("V-11111111", EstadoAsistencia.JUSTIFICADO, "Gripe severa")
    assert reg1.estado == EstadoAsistencia.JUSTIFICADO
    assert reg1.motivo_justificacion == "Gripe severa"
    
    # Modificar reg2 a Ausente
    planilla.actualizar_registro("V-22222222", EstadoAsistencia.AUSENTE)
    assert reg2.estado == EstadoAsistencia.AUSENTE
    
    # Actualizar un estudiante que no está en la planilla (no debe fallar)
    planilla.actualizar_registro("V-99999999", EstadoAsistencia.AUSENTE)
