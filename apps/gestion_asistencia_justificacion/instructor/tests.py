"""
Pruebas unitarias — apps.gestion_asistencia_justificacion.instructor

"""

import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from django.test import TestCase

from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import (
    AsistenciaAmbiente,
    Competencia,
    Justificacion,
)


# ─── helpers ────────────────────────────────────────────────────────────────

def _crear_usuario(cedula, nombre='Test', apellido='User'):
    return Usuarios.objects.create_user(
        cedula=cedula,
        password='testpass123',
        nombre=nombre,
        apellido=apellido,
    )


def _crear_asistencia(usuario, fecha, estado, instructor=None, competencia=None):
    return AsistenciaAmbiente.objects.create(
        id_usuario=usuario,
        fecha=fecha,
        estado_asistencia=estado,
        id_instructor=instructor,
        id_competencia=competencia,
    )


# ============================================================================
# calcular_inasistencias_aprendiz
# ============================================================================

class TestCalcularInasistenciasAprendiz(TestCase):
    """
    Requiere BD.
    Firma: calcular_inasistencias_aprendiz(aprendiz) → dict
    Retorna: {'tiene_3': bool, 'tiene_5': bool, 'total': int}

    Diferencias clave con analizar_inasistencias (aprendiz):
      - Esta versión consulta la BD directamente.
      - El algoritmo de consecutivos es CORRECTO (resetea contador en lugar de break).
    """

    @classmethod
    def setUpTestData(cls):
        cls.aprendiz = _crear_usuario('10000001', 'Maria', 'Gomez')

    def setUp(self):
        from apps.gestion_asistencia_justificacion.instructor.services.inasistencias_service import calcular_inasistencias_aprendiz
        self.fn = calcular_inasistencias_aprendiz

    # ── casos normales ────────────────────────────────────────────────────

    def test_sin_asistencias_retorna_ceros(self):
        resultado = self.fn(self.aprendiz)
        self.assertFalse(resultado['tiene_3'])
        self.assertFalse(resultado['tiene_5'])
        self.assertEqual(resultado['total'], 0)

    def test_tres_inasistencias_consecutivas_activan_tiene_3(self):
        hoy = date.today()
        for i in range(3):
            _crear_asistencia(self.aprendiz, hoy - timedelta(days=i), 'Inasistio')
        resultado = self.fn(self.aprendiz)
        self.assertTrue(resultado['tiene_3'])

    def test_cinco_inasistencias_no_consecutivas_activan_tiene_5(self):
        hoy = date.today()
        for i in range(5):
            _crear_asistencia(self.aprendiz, hoy - timedelta(days=i * 5), 'Inasistio')
        resultado = self.fn(self.aprendiz)
        self.assertTrue(resultado['tiene_5'])

    def test_solo_asistencias_presentes_retorna_ceros(self):
        hoy = date.today()
        for i in range(7):
            _crear_asistencia(self.aprendiz, hoy - timedelta(days=i), 'Asistio')
        resultado = self.fn(self.aprendiz)
        self.assertFalse(resultado['tiene_3'])
        self.assertEqual(resultado['total'], 0)

    # ── casos límite ─────────────────────────────────────────────────────

    def test_justificacion_aprobada_no_cuenta_como_inasistencia(self):
        """Una inasistencia con justificación Aprobada no debe sumarse al total."""
        hoy = date.today()
        for i in range(3):
            asist = _crear_asistencia(self.aprendiz, hoy - timedelta(days=i), 'Inasistio')
            Justificacion.objects.create(
                id_asistencia_ambiente=asist,
                estado='Aprobado',
                motivo='Enfermedad',
            )
        resultado = self.fn(self.aprendiz)
        self.assertFalse(resultado['tiene_3'])
        self.assertEqual(resultado['total'], 0)

    def test_justificacion_pendiente_si_cuenta(self):
        """Una justificación Pendiente (no Aprobada) no exime la inasistencia."""
        hoy = date.today()
        for i in range(3):
            asist = _crear_asistencia(self.aprendiz, hoy - timedelta(days=i), 'Inasistio')
            Justificacion.objects.create(
                id_asistencia_ambiente=asist,
                estado='Pendiente',
                motivo='Calamidad',
            )
        resultado = self.fn(self.aprendiz)
        self.assertTrue(resultado['tiene_3'])

    def test_dia_con_asistio_e_inasistio_no_cuenta(self):
        """Si hay Asistio e Inasistio el mismo día, el día NO se cuenta."""
        hoy = date.today()
        _crear_asistencia(self.aprendiz, hoy, 'Asistio')
        _crear_asistencia(self.aprendiz, hoy, 'Inasistio')
        resultado = self.fn(self.aprendiz)
        self.assertEqual(resultado['total'], 0)

    def test_retardo_anula_inasistencia_del_mismo_dia(self):
        hoy = date.today()
        _crear_asistencia(self.aprendiz, hoy, 'Retardo')
        _crear_asistencia(self.aprendiz, hoy, 'Inasistio')
        resultado = self.fn(self.aprendiz)
        self.assertEqual(resultado['total'], 0)

    # ── casos de error ────────────────────────────────────────────────────

    def test_asistencias_de_otro_aprendiz_no_interfieren(self):
        otro = _crear_usuario('10000099', 'Otro', 'Aprendiz')
        hoy = date.today()
        for i in range(5):
            _crear_asistencia(otro, hoy - timedelta(days=i), 'Inasistio')
        resultado = self.fn(self.aprendiz)
        self.assertEqual(resultado['total'], 0)

    def test_detecta_consecutivos_despues_de_un_gap(self):
        """
        A diferencia de analizar_inasistencias (aprendiz), esta versión
        reinicia el contador al encontrar un gap → detecta correctamente
        tres días consecutivos después de una interrupción.
        """
        hoy = date.today()
        # Secuencia: hoy, ayer, [gap], hace 5, hace 6, hace 7 → últimos 3 son consecutivos
        _crear_asistencia(self.aprendiz, hoy, 'Inasistio')
        _crear_asistencia(self.aprendiz, hoy - timedelta(days=1), 'Inasistio')
        _crear_asistencia(self.aprendiz, hoy - timedelta(days=5), 'Inasistio')
        _crear_asistencia(self.aprendiz, hoy - timedelta(days=6), 'Inasistio')
        _crear_asistencia(self.aprendiz, hoy - timedelta(days=7), 'Inasistio')
        resultado = self.fn(self.aprendiz)
        # Días 5-6-7 son consecutivos → tiene_3 debe ser True
        self.assertTrue(resultado['tiene_3'])


# ============================================================================
# procesar_accion_justificacion
# ============================================================================

class TestProcesarAccionJustificacion(TestCase):
    """
    Requiere BD.
    Firma: procesar_accion_justificacion(justificacion_id, accion, observaciones=None)
           → (bool, str)
    """

    @classmethod
    def setUpTestData(cls):
        cls.aprendiz = _crear_usuario('20000001', 'Pedro', 'Lopez')
        cls.asistencia = _crear_asistencia(
            cls.aprendiz, date.today(), 'Inasistio'
        )

    def setUp(self):
        from apps.gestion_asistencia_justificacion.instructor.services.justificacion_action_service import procesar_accion_justificacion
        self.fn = procesar_accion_justificacion
        self.justif = Justificacion.objects.create(
            id_asistencia_ambiente=self.asistencia,
            motivo='Cita médica',
            estado='Pendiente',
            observaciones='',
        )

    # ── casos normales ────────────────────────────────────────────────────

    def test_aprobar_cambia_estado_a_aprobado(self):
        ok, _ = self.fn(self.justif.id_justificacion, 'aprobar')
        self.assertTrue(ok)
        self.justif.refresh_from_db()
        self.assertEqual(self.justif.estado, 'Aprobado')

    def test_aprobar_marca_asistencia_como_justificada(self):
        self.fn(self.justif.id_justificacion, 'aprobar')
        self.asistencia.refresh_from_db()
        self.assertEqual(self.asistencia.estado_asistencia, 'Justificada')

    def test_rechazar_cambia_estado_a_rechazado(self):
        ok, _ = self.fn(self.justif.id_justificacion, 'rechazar')
        self.assertTrue(ok)
        self.justif.refresh_from_db()
        self.assertEqual(self.justif.estado, 'Rechazado')

    def test_rechazar_no_modifica_estado_asistencia(self):
        self.fn(self.justif.id_justificacion, 'rechazar')
        self.asistencia.refresh_from_db()
        self.assertEqual(self.asistencia.estado_asistencia, 'Inasistio')

    def test_observaciones_se_guardan(self):
        self.fn(self.justif.id_justificacion, 'aprobar', observaciones='Documento válido')
        self.justif.refresh_from_db()
        self.assertEqual(self.justif.observaciones, 'Documento válido')

    # ── casos límite ─────────────────────────────────────────────────────

    def test_aprobar_justificacion_sin_asistencia_vinculada(self):
        """Justificación sin FK a asistencia debe aprobarse sin lanzar error."""
        justif_suelta = Justificacion.objects.create(
            id_asistencia_ambiente=None,
            motivo='Sin asistencia vinculada',
            estado='Pendiente',
        )
        ok, _ = self.fn(justif_suelta.id_justificacion, 'aprobar')
        self.assertTrue(ok)
        justif_suelta.refresh_from_db()
        self.assertEqual(justif_suelta.estado, 'Aprobado')

    def test_observaciones_vacias_no_sobreescriben_existentes(self):
        """Si observaciones es cadena vacía (falsy), el campo no debe cambiar."""
        self.justif.observaciones = 'Nota original'
        self.justif.save()
        self.fn(self.justif.id_justificacion, 'rechazar', observaciones='')
        self.justif.refresh_from_db()
        self.assertEqual(self.justif.observaciones, 'Nota original')

    # ── casos de error ────────────────────────────────────────────────────

    def test_id_inexistente_retorna_false(self):
        ok, mensaje = self.fn(999999, 'aprobar')
        self.assertFalse(ok)
        self.assertEqual(mensaje, 'Justificación no encontrada')

    def test_accion_desconocida_no_cambia_estado(self):
        """Una acción no reconocida no debe modificar el estado."""
        self.fn(self.justif.id_justificacion, 'eliminar')
        self.justif.refresh_from_db()
        self.assertEqual(self.justif.estado, 'Pendiente')


# ============================================================================
# registrar_asistencia
# ============================================================================

class TestRegistrarAsistencia(TestCase):
    """
    Requiere BD + mock de HttpRequest.
    Firma: registrar_asistencia(aprendices, request, fecha, competencia) → int
    """

    @classmethod
    def setUpTestData(cls):
        cls.instructor  = _crear_usuario('30000001', 'Carlos', 'Instructor')
        cls.aprendiz1   = _crear_usuario('30000002', 'Ana', 'Gomez')
        cls.aprendiz2   = _crear_usuario('30000003', 'Luis', 'Mora')
        cls.competencia = Competencia.objects.create(nombre_competencia='Programación')

    def setUp(self):
        from apps.gestion_asistencia_justificacion.instructor.services.asistencia_service import registrar_asistencia
        self.fn = registrar_asistencia
        self.fecha = date.today()
        self.request = MagicMock()
        self.request.user = self.instructor
        self.request.POST = {
            f'asistencia_{self.aprendiz1.id_usuario}': 'Asistio',
            f'asistencia_{self.aprendiz2.id_usuario}': 'Inasistio',
        }

    # ── casos normales ────────────────────────────────────────────────────

    def test_crea_registros_para_todos_los_aprendices(self):
        n = self.fn([self.aprendiz1, self.aprendiz2], self.request, self.fecha, self.competencia)
        self.assertEqual(n, 2)

    def test_estado_guardado_correctamente(self):
        self.fn([self.aprendiz1], self.request, self.fecha, self.competencia)
        asistencia = AsistenciaAmbiente.objects.get(
            id_usuario=self.aprendiz1,
            fecha=self.fecha,
            id_competencia=self.competencia,
        )
        self.assertEqual(asistencia.estado_asistencia, 'Asistio')

    def test_instructor_asignado_correctamente(self):
        self.fn([self.aprendiz1], self.request, self.fecha, self.competencia)
        asistencia = AsistenciaAmbiente.objects.get(
            id_usuario=self.aprendiz1, fecha=self.fecha
        )
        self.assertEqual(asistencia.id_instructor, self.instructor)

    def test_actualiza_registro_existente(self):
        """update_or_create: si ya existe un registro, debe actualizarse."""
        AsistenciaAmbiente.objects.create(
            id_usuario=self.aprendiz1,
            fecha=self.fecha,
            id_competencia=self.competencia,
            estado_asistencia='Retardo',
        )
        self.fn([self.aprendiz1], self.request, self.fecha, self.competencia)
        registro = AsistenciaAmbiente.objects.get(
            id_usuario=self.aprendiz1,
            fecha=self.fecha,
            id_competencia=self.competencia,
        )
        self.assertEqual(registro.estado_asistencia, 'Asistio')

    # ── casos límite ─────────────────────────────────────────────────────

    def test_lista_vacia_retorna_cero(self):
        n = self.fn([], self.request, self.fecha, self.competencia)
        self.assertEqual(n, 0)

    # ── casos de error ────────────────────────────────────────────────────

    def test_aprendiz_sin_estado_en_post_no_se_registra(self):
        """Si el aprendiz no tiene entrada en POST, no se crea registro."""
        self.request.POST = {}
        n = self.fn([self.aprendiz1], self.request, self.fecha, self.competencia)
        self.assertEqual(n, 0)
        self.assertFalse(
            AsistenciaAmbiente.objects.filter(
                id_usuario=self.aprendiz1, fecha=self.fecha
            ).exists()
        )


# ============================================================================
# generar_reporte / generar_totales — advertencia de case sensitivity
# ============================================================================

class TestGenearReporteTotales(TestCase):
    """
    Requiere BD.
    Prueba generar_reporte() y generar_totales().

    AVISO DE DISEÑO (potencial bug en PostgreSQL):
    Los Case/When usan estados en minúscula ('asistio', 'inasistio', 'retardo')
    pero los datos se almacenan en TitleCase ('Asistio', 'Inasistio', 'Retardo').
    SQLite y MySQL (collation ci) son case-insensitive → los tests pasan.
    PostgreSQL es case-sensitive → todos los conteos serían 0 con esos datos.
    Si el proyecto migra a PostgreSQL se debe normalizar: o los datos al guardar,
    o los Case/When en la función.
    """

    @classmethod
    def setUpTestData(cls):
        cls.aprendiz = _crear_usuario('40000001', 'Rosa', 'Rios')
        hoy = date.today()
        AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz, fecha=hoy,
            estado_asistencia='Asistio',
        )
        AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz, fecha=hoy - timedelta(days=1),
            estado_asistencia='Inasistio',
        )
        AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz, fecha=hoy - timedelta(days=2),
            estado_asistencia='Retardo',
        )
        cls.qs = AsistenciaAmbiente.objects.filter(id_usuario=cls.aprendiz)

    def setUp(self):
        from apps.gestion_asistencia_justificacion.instructor.services.asistencia_service import (
            generar_reporte,
            generar_totales,
        )
        self.generar_reporte = generar_reporte
        self.generar_totales = generar_totales

    def test_generar_totales_conteos_correctos(self):
        totales = self.generar_totales(self.qs)
        self.assertEqual(totales['total_asistio'],   1)
        self.assertEqual(totales['total_inasistio'], 1)
        self.assertEqual(totales['total_retardo'],   1)

    def test_generar_reporte_incluye_datos_por_aprendiz(self):
        reporte = list(self.generar_reporte(self.qs))
        self.assertEqual(len(reporte), 1)
        registro = reporte[0]
        self.assertEqual(registro['id_usuario__nombre'],   'Rosa')
        self.assertEqual(registro['id_usuario__apellido'], 'Rios')
        self.assertEqual(registro['asistio'],   1)
        self.assertEqual(registro['inasistio'], 1)
        self.assertEqual(registro['retardo'],   1)
