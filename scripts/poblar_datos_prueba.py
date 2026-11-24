#!/usr/bin/env python3
# scripts/poblar_datos_prueba.py
"""
Script de Carga de Datos de Prueba (Seed) — Sistema de Asistencia Estudiantil.
Complejo Educativo 'Colinas del Llano' (Barinas, Venezuela).

Puebla sistema_escolar.db con un conjunto de datos ficticio pero realista:
- 4 Profesores activos con materias asignadas.
- 14 Estudiantes de 4to Año distribuidos en Secciones A y B.
- Clases de Matemáticas, Física, Química, Castellano e Inglés.
- 10 jornadas de asistencia con distribución realista:
  * Alumnos regulares (asistencia >= 80% a 100%).
  * Faltas justificadas (J) con motivos realistas (médicos, personales).
  * Casos intencionales de ALERTA DE RIESGO (< 75.0% según Art. 109 RGLOE)
    para validación visual inmediata en las interfaces de Reportes.

Uso:
    python scripts/poblar_datos_prueba.py [--reset]
"""

import sys
import os
import argparse
from datetime import datetime

# Asegurar que el directorio raíz del proyecto esté en sys.path
dir_script = os.path.dirname(os.path.abspath(__file__))
dir_raiz = os.path.abspath(os.path.join(dir_script, ".."))
if dir_raiz not in sys.path:
    sys.path.insert(0, dir_raiz)

from db_conexion import ConexionBD
from dominio.profesor import Profesor
from dominio.estudiante import Estudiante
from dominio.clase import Clase
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
from adaptadores.db.sqlite_asistencia import RepositorioAsistenciaSQLite


# =============================================================================
# DATOS MAESTROS DE PRUEBA
# =============================================================================

DOCENTES_SEED = [
    ("V-12456789", "PROF. CARLOS ALBERTO MENDOZA"),
    ("V-14890123", "PROF. MARIA ELENA CONTRERAS"),
    ("V-16234567", "PROF. JOSE RAMON GUERRERO"),
    ("V-18567890", "PROF. ANA BEATRIZ SILVA"),
]

# (cedula, nombre, fecha_nac, repre, telf, gen, escolaridad, turno, condicion, grado, seccion)
ESTUDIANTES_SEED = [
    # ── 4to Año Sección A (ID_GRADO=4, ID_SECCION=1) ──
    (
        "V-31201101", "GABRIEL ALEJANDRO MORALES RIVAS", "14/03/2009",
        "ELENA RIVAS DE MORALES", "0414-5551101", "M", "Regular", "Mañana", "Activo", 4, 1
    ),
    (
        "V-31201102", "MARIANA VALENTINA SALAZAR PEÑA", "28/05/2009",
        "ROBERTO SALAZAR", "0424-5551102", "F", "Regular", "Mañana", "Activo", 4, 1
    ),
    (
        "V-31201103", "DIEGO ARMANDO COLMENARES GIL", "10/01/2009",
        "CARMEN GIL COLMENARES", "0416-5551103", "M", "Regular", "Mañana", "Activo", 4, 1
    ),
    (
        "V-31201104", "SOFIA ISABELLA GUTIERREZ PARRA", "09/08/2009",
        "PATRICIA PARRA GUTIERREZ", "0412-5551104", "F", "Regular", "Mañana", "Activo", 4, 1
    ),
    (
        "V-31201105", "JESUS DAVID ZAMBRANO CASTILLO", "19/11/2008",
        "MANUEL ZAMBRANO", "0414-5551105", "M", "Materia Pendiente", "Mañana", "Activo", 4, 1
    ),  # <- Caso en riesgo (< 75%)
    (
        "V-31201106", "CAMILA ALEJANDRA RONDON BRICEÑO", "02/04/2009",
        "ALICIA BRICEÑO RONDON", "0424-5551106", "F", "Regular", "Mañana", "Activo", 4, 1
    ),
    (
        "V-31201107", "ANDRES EDUARDO PINEDA ROMERO", "17/07/2009",
        "EDUARDO PINEDA", "0416-5551107", "M", "Regular", "Mañana", "Activo", 4, 1
    ),  # <- Caso en riesgo (< 75%)

    # ── 4to Año Sección B (ID_GRADO=4, ID_SECCION=2) ──
    (
        "V-31201201", "VALERIA CAROLINA MENDEZ QUINTERO", "11/02/2009",
        "CAROLINA QUINTERO MENDEZ", "0414-5551201", "F", "Regular", "Tarde", "Activo", 4, 2
    ),
    (
        "V-31201202", "SEBASTIAN JOSE RIVERO LINARES", "30/06/2009",
        "JOSE GREGORIO RIVERO", "0424-5551202", "M", "Regular", "Tarde", "Activo", 4, 2
    ),
    (
        "V-31201203", "ISABELLA VICTORIA CAMPOS NIEVES", "23/09/2009",
        "VICTORIA NIEVES CAMPOS", "0416-5551203", "F", "Regular", "Tarde", "Activo", 4, 2
    ),
    (
        "V-31201204", "SANTIAGO DANIEL FERRER OJEDA", "05/12/2008",
        "DANIEL FERRER", "0412-5551204", "M", "Repite", "Tarde", "Activo", 4, 2
    ),  # <- Caso en riesgo (< 75%)
    (
        "V-31201205", "LUCIA DANIELA TERAN MONTILLA", "18/03/2009",
        "DANIELA MONTILLA TERAN", "0414-5551205", "F", "Regular", "Tarde", "Activo", 4, 2
    ),
    (
        "V-31201206", "SAMUEL ANTONIO ALBARRAN SUAREZ", "25/10/2009",
        "ANTONIO ALBARRAN", "0424-5551206", "M", "Regular", "Tarde", "Activo", 4, 2
    ),
    (
        "V-31201207", "PAULA ANDREA BASTIDAS RANGEL", "08/01/2009",
        "ANDREA RANGEL BASTIDAS", "0416-5551207", "F", "Regular", "Tarde", "Activo", 4, 2
    ),
]

FECHAS_CLASES_SEED = [
    "2026-11-03",
    "2026-11-04",
    "2026-11-05",
    "2026-11-06",
    "2026-11-10",
    "2026-11-11",
    "2026-11-12",
    "2026-11-13",
    "2026-11-17",
    "2026-11-18",
]

# Matriz de asistencia por estudiante para las 10 fechas:
# Retorna lista de tuplas (estado: EstadoAsistencia, motivo: Optional[str])
def generar_patron_asistencia(cedula: str) -> list[tuple[EstadoAsistencia, str | None]]:
    """Genera 10 registros de asistencia simulando patrones realistas."""
    P = (EstadoAsistencia.PRESENTE, None)
    A = (EstadoAsistencia.AUSENTE, None)
    J_GRIPE = (EstadoAsistencia.JUSTIFICADO, "Fiebre viral y reposo médico certificado")
    J_ODONTO = (EstadoAsistencia.JUSTIFICADO, "Consulta odontológica programada")
    J_SAIME = (EstadoAsistencia.JUSTIFICADO, "Trámite de renovación de cédula en SAIME")

    # 1. Casos críticos intencionales (< 75.0% según Art. 109 RGLOE)
    if cedula == "V-31201105":  # Jesús Zambrano: 4 efectivas (3P + 1J) / 10 = 40.0% -> ALERTA ROJA
        return [P, A, A, J_GRIPE, A, P, A, A, P, A]

    if cedula == "V-31201107":  # Andrés Pineda: 6 efectivas (6P) / 10 = 60.0% -> ALERTA ROJA
        return [P, P, A, A, P, P, A, A, P, P]

    if cedula == "V-31201204":  # Santiago Ferrer: 7 efectivas (6P + 1J) / 10 = 70.0% -> ALERTA AMBAR (< 75%)
        return [P, P, A, J_SAIME, P, P, A, P, A, P]

    # 2. Casos regulares con asistencia alta y justificaciones esporádicas (80% a 100%)
    patrones_regulares = {
        "V-31201101": [P, P, P, P, P, P, P, P, P, P],  # 100%
        "V-31201102": [P, P, J_ODONTO, P, P, P, P, P, P, P],  # 100% efectivas
        "V-31201103": [P, P, P, A, P, P, P, P, P, P],  # 90%
        "V-31201104": [P, P, P, P, P, J_GRIPE, P, P, P, P],  # 100%
        "V-31201106": [P, A, P, P, P, P, P, P, P, P],  # 90%
        "V-31201201": [P, P, P, P, P, P, P, P, P, P],  # 100%
        "V-31201202": [P, P, A, P, P, P, P, A, P, P],  # 80%
        "V-31201203": [P, P, P, P, J_GRIPE, P, P, P, P, P],  # 100%
        "V-31201205": [P, P, P, P, P, P, P, P, P, P],  # 100%
        "V-31201206": [P, P, P, A, P, P, P, P, P, P],  # 90%
        "V-31201207": [P, J_SAIME, P, P, P, P, P, P, P, P],  # 100%
    }
    return patrones_regulares.get(cedula, [P] * 10)


# =============================================================================
# FUNCIÓN PRINCIPAL DE CARGA
# =============================================================================

def poblar_base_de_datos(reset: bool = False):
    """Ejecuta la inserción de datos de prueba en sistema_escolar.db."""
    print("=" * 72)
    print("  COMPLEJO EDUCATIVO 'COLINAS DEL LLANO' — BARINAS, VENEZUELA")
    print("  Script de Semillero de Datos de Prueba (Seed)")
    print("=" * 72)

    db = ConexionBD()
    conn = db.conectar()
    if not conn:
        print("❌ Error crítico: No se pudo conectar a sistema_escolar.db")
        sys.exit(1)

    cur = conn.cursor()

    if reset:
        print("\n🧹 [--reset detectado] Limpiando datos operativos previos...")
        cur.execute("DELETE FROM TBL_JUSTIFICACIONES")
        cur.execute("DELETE FROM TBL_ASISTENCIA")
        cur.execute("DELETE FROM TBL_CLASES")
        cur.execute("DELETE FROM TBL_ESTUDIANTES")
        cur.execute("DELETE FROM TBL_PROFESORES")
        conn.commit()
        print("   Tablas operativas restablecidas con éxito.")

    # 1. Semillero de Profesores
    print("\n👨‍🏫 1. Insertando Profesores...")
    repo_prof = SQLiteRepositorioProfesor(db)
    profs_insertados = 0
    mapa_profesores_id = {}

    for ced, nom in DOCENTES_SEED:
        prof = Profesor(cedula=ced, nombre_completo=nom)
        try:
            repo_prof.guardar(prof)
            profs_insertados += 1
        except Exception:
            pass  # Ya existía

    todos_profs = repo_prof.obtener_todos()
    for p in todos_profs:
        mapa_profesores_id[p.cedula] = p.id_profesor
    print(f"   ✓ {len(todos_profs)} profesores activos registrados en la institución.")

    # 2. Semillero de Clases de 4to Año
    print("\n📚 2. Configurando Materias y Carga Académica de 4to Año...")
    repo_clase = SQLiteRepositorioClase(db)

    id_carlos = mapa_profesores_id.get("V-12456789", 1)
    id_maria = mapa_profesores_id.get("V-14890123", 1)
    id_jose = mapa_profesores_id.get("V-16234567", 1)
    id_ana = mapa_profesores_id.get("V-18567890", 1)

    clases_a_crear = [
        # Sección A
        Clase("MATEMATICAS", id_carlos, 4, 1),
        Clase("FISICA", id_maria, 4, 1),
        Clase("CASTELLANO", id_jose, 4, 1),
        Clase("INGLES", id_ana, 4, 1),
        # Sección B
        Clase("MATEMATICAS", id_carlos, 4, 2),
        Clase("QUIMICA", id_maria, 4, 2),
        Clase("CASTELLANO", id_jose, 4, 2),
    ]

    for c in clases_a_crear:
        cur.execute(
            """
            SELECT ID_CLASE FROM TBL_CLASES 
            WHERE NOMBRE_MATERIA = ? AND ID_GRADO = ? AND ID_SECCION = ?
            """,
            (c.nombre_materia, c.id_grado, c.id_seccion)
        )
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION)
                VALUES (?, ?, ?, ?)
                """,
                (c.nombre_materia, c.id_profesor, c.id_grado, c.id_seccion)
            )
    conn.commit()

    clases_totales = repo_clase.obtener_clases_disponibles()
    print(f"   ✓ {len(clases_totales)} materias activas asignadas en 4to Año.")

    # 3. Semillero de Estudiantes de 4to Año
    print("\n👤 3. Inscribiendo Estudiantes de 4to Año (Secciones A y B)...")
    repo_est = RepositorioEstudianteSQLite(db)
    estudiantes_insertados = 0

    for datos in ESTUDIANTES_SEED:
        e = Estudiante(
            cedula=datos[0],
            nombre=datos[1],
            fecha_nacimiento=datos[2],
            representante=datos[3],
            telefono=datos[4],
            genero=datos[5],
            escolaridad=datos[6],
            turno=datos[7],
            condicion=datos[8],
            id_grado=datos[9],
            id_seccion=datos[10]
        )
        if repo_est.guardar(e):
            estudiantes_insertados += 1

    total_estudiantes = repo_est.obtener_todos_activos()
    print(f"   ✓ {len(total_estudiantes)} estudiantes activos en el sistema.")

    # 4. Semillero de Asistencias (10 jornadas para Matemáticas de 4to A y 4to B)
    print("\n📋 4. Registrando Jornadas de Asistencia y Justificaciones Legales...")
    repo_asist = RepositorioAsistenciaSQLite(db)

    # Identificar ID de clases de Matemáticas en 4to A y 4to B
    cur.execute("SELECT ID_CLASE, ID_SECCION FROM TBL_CLASES WHERE NOMBRE_MATERIA = 'MATEMATICAS' AND ID_GRADO = 4")
    clases_matematicas = cur.fetchall()

    total_asistencias_marcadas = 0
    total_justificaciones_creadas = 0

    for id_clase, id_sec in clases_matematicas:
        # Obtener alumnos de la sección
        alumnos_sec = [est for est in ESTUDIANTES_SEED if est[10] == id_sec]

        for i, fecha in enumerate(FECHAS_CLASES_SEED):
            planilla = PlanillaAsistencia(id_clase=id_clase, fecha=fecha)

            for est in alumnos_sec:
                cedula = est[0]
                patron = generar_patron_asistencia(cedula)
                estado, motivo = patron[i]

                reg = RegistroAsistencia(id_estudiante=cedula, estado=estado)
                if estado == EstadoAsistencia.JUSTIFICADO and motivo:
                    reg.motivo_justificacion = motivo
                    total_justificaciones_creadas += 1

                planilla.registros.append(reg)
                total_asistencias_marcadas += 1

            repo_asist.guardar_planilla(planilla)

    print(f"   ✓ {total_asistencias_marcadas} marcajes de asistencia guardados en {len(FECHAS_CLASES_SEED)} fechas.")
    print(f"   ✓ {total_justificaciones_creadas} justificaciones registradas con motivos auditables.")

    # Resumen de Casos en Riesgo (< 75% Art. 109 RGLOE)
    print("\n⚠️ 5. Verificación de Casos Críticos (Art. 109 RGLOE < 75%):")
    print("   ---------------------------------------------------------------------")
    print("   Cédula      Estudiante                        % Asist.   Estado")
    print("   ---------------------------------------------------------------------")
    print("   V-31201105  JESUS DAVID ZAMBRANO CASTILLO      40.0%    🚨 EN RIESGO")
    print("   V-31201107  ANDRES EDUARDO PINEDA ROMERO       60.0%    🚨 EN RIESGO")
    print("   V-31201204  SANTIAGO DANIEL FERRER OJEDA       70.0%    🚨 EN RIESGO")
    print("   (Los restantes 11 alumnos cumplen con el estándar legal >= 75.0%)")
    print("   ---------------------------------------------------------------------")

    print("\n✅ ¡Semillero completado con éxito!")
    print("   Ahora puedes abrir la aplicación con 'python main.py' para probar:")
    print("   - Inicio de Sesión con admin / 1234")
    print("   - Pasar Lista de Asistencia con respaldo anti-apagones")
    print("   - Módulo de Reportes -> '⚠️ VER ALERTAS DE RIESGO' para ver los alumnos destacados en rojo")
    print("   - Exportar a PDF oficial con membrete y tabla zebra")
    print("   - Cierre y Promoción Anual de 4to a 5to Año con clave DIRECTOR2025\n")

    db.cerrar()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semillero de datos de prueba para el Sistema Escolar.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Limpia datos operativos previos antes de poblar la base de datos."
    )
    args = parser.parse_args()
    poblar_base_de_datos(reset=args.reset)
