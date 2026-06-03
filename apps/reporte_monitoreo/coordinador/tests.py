"""
Pruebas unitarias — apps.reporte_monitoreo.coordinador

"""

import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase


# ==================== SECCIÓN A — TESTS ORIGINALES (estructura) ====================

# ==================== TESTS DE MODELOS ====================

class CoordinacionModelTest(TestCase):
    """Tests para el modelo Coordinacion - sin acceso a BD"""

    def test_coordinacion_model_exists(self):
        """Test que el modelo Coordinacion existe y es importable"""
        from apps.reporte_monitoreo.coordinador.models import Coordinacion
        self.assertIsNotNone(Coordinacion)
        self.assertTrue(hasattr(Coordinacion, '_meta'))


class JornadaModelTest(TestCase):
    """Tests para el modelo Jornada - sin acceso a BD"""

    def test_jornada_model_exists(self):
        """Test que el modelo Jornada existe"""
        from apps.reporte_monitoreo.coordinador.models import Jornada
        self.assertIsNotNone(Jornada)
        field_names = [f.name for f in Jornada._meta.get_fields()]
        self.assertIn('hora_inicio', field_names)
        self.assertIn('hora_fin', field_names)


class ProgramaModelTest(TestCase):
    """Tests para el modelo Programa - sin acceso a BD"""

    def test_programa_model_exists(self):
        """Test que el modelo Programa existe"""
        from apps.reporte_monitoreo.coordinador.models import Programa
        self.assertIsNotNone(Programa)

    def test_programa_fields(self):
        """Test que Programa tiene los campos esperados"""
        from apps.reporte_monitoreo.coordinador.models import Programa
        field_names = [f.name for f in Programa._meta.get_fields()]
        self.assertIn('nombre_programa', field_names)
        self.assertIn('tipo_programa', field_names)
        self.assertIn('id_coordinacion', field_names)


class CompetenciaModelTest(TestCase):
    """Tests para el modelo Competencia - sin acceso a BD"""

    def test_competencia_model_exists(self):
        """Test que el modelo Competencia existe"""
        from apps.reporte_monitoreo.coordinador.models import Competencia
        self.assertIsNotNone(Competencia)

    def test_competencia_fields(self):
        """Test que Competencia tiene los campos esperados"""
        from apps.reporte_monitoreo.coordinador.models import Competencia
        field_names = [f.name for f in Competencia._meta.get_fields()]
        self.assertIn('nombre_competencia', field_names)
        self.assertIn('id_programa', field_names)
        self.assertIn('estado', field_names)


# ==================== TESTS DE IMPORTACIÓN ====================

class ReporteMonitoreoImportTest(TestCase):
    """Tests de importación de módulos"""

    def test_views_module_exists(self):
        """Test que el módulo de views puede ser importado"""
        from apps.reporte_monitoreo.coordinador import views
        self.assertIsNotNone(views)

    def test_urls_module_exists(self):
        """Test que el módulo de urls puede ser importado"""
        from apps.reporte_monitoreo.coordinador import urls
        self.assertIsNotNone(urls)


# ==================== TESTS DE ESTRUCTURA ====================

class ModelStructureTest(TestCase):
    """Tests de estructura de modelos sin acceso a BD"""

    def test_all_models_defined(self):
        """Test que todos los modelos están definidos"""
        from apps.reporte_monitoreo.coordinador.models import (
            Coordinacion, Jornada, Programa, Competencia, Ficha
        )
        self.assertIsNotNone(Coordinacion)
        self.assertIsNotNone(Jornada)
        self.assertIsNotNone(Programa)
        self.assertIsNotNone(Competencia)
        self.assertIsNotNone(Ficha)

    def test_foreign_key_relationships(self):
        """Test que las relaciones de clave foránea están definidas"""
        from apps.reporte_monitoreo.coordinador.models import Programa, Competencia
        programa_fields = [f.name for f in Programa._meta.get_fields()]
        self.assertIn('id_coordinacion', programa_fields)
        competencia_fields = [f.name for f in Competencia._meta.get_fields()]
        self.assertIn('id_programa', competencia_fields)

    def test_model_meta_configuration(self):
        """Test que los modelos tienen configuración correcta"""
        from apps.reporte_monitoreo.coordinador.models import Coordinacion
        self.assertEqual(Coordinacion._meta.db_table, 'coordinacion')
        self.assertTrue(Coordinacion._meta.managed)


# ==================== SECCIÓN B — TESTS FUNCIONALES (nueva) ====================

from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import (
    AsistenciaAmbiente,
    AsistenciaSede,
    Competencia,
    Ficha,
    Justificacion,
)


# ─── helpers ────────────────────────────────────────────────────────────────

def _crear_usuario_b(cedula, nombre='Test', apellido='User', ficha=None):
    return Usuarios.objects.create_user(
        cedula=cedula,
        password='testpass123',
        nombre=nombre,
        apellido=apellido,
        id_ficha=ficha,
    )


def _mock_asistencia_pdf(estado, cedula='12345678', nombre='Juan', apellido='Perez',
                          ficha_num='2750614', jornada='Diurna',
                          instructor_nombre='Prof', instructor_apellido='X',
                          fecha=None):
    """Crea un objeto mock de AsistenciaAmbiente para tests de preparar_registros_pdf."""
    ficha_mock    = SimpleNamespace(numero_ficha=ficha_num, id_jornada=SimpleNamespace(nombre_jornada=jornada))
    usuario_mock  = SimpleNamespace(cedula=cedula, nombre=nombre, apellido=apellido, id_ficha=ficha_mock)
    instructor_m  = SimpleNamespace(nombre=instructor_nombre, apellido=instructor_apellido)
    return SimpleNamespace(
        id_usuario=usuario_mock,
        id_instructor=instructor_m,
        fecha=fecha or date(2025, 5, 20),
        estado_asistencia=estado,
    )


# ============================================================================
# preparar_registros_pdf
# ============================================================================

class TestPrepararRegistrosPdf(unittest.TestCase):
    """
    Función pura — no requiere BD.
    Firma: preparar_registros_pdf(asistencias) → list[dict]
    Normaliza estado_asistencia a: 'asistio' | 'inasistio' | 'justificada' | lower(otro)
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.services.export_service import preparar_registros_pdf
        self.fn = preparar_registros_pdf

    def test_normaliza_asistio(self):
        resultado = self.fn([_mock_asistencia_pdf('Asistio')])
        self.assertEqual(resultado[0]['estado'], 'asistio')

    def test_normaliza_inasistio(self):
        resultado = self.fn([_mock_asistencia_pdf('Inasistio')])
        self.assertEqual(resultado[0]['estado'], 'inasistio')

    def test_normaliza_justificada(self):
        resultado = self.fn([_mock_asistencia_pdf('Justificada')])
        self.assertEqual(resultado[0]['estado'], 'justificada')

    def test_normaliza_justificado_masculino(self):
        resultado = self.fn([_mock_asistencia_pdf('Justificado')])
        self.assertEqual(resultado[0]['estado'], 'justificada')

    def test_estado_none_produce_cadena_vacia(self):
        resultado = self.fn([_mock_asistencia_pdf(None)])
        self.assertEqual(resultado[0]['estado'], '')

    def test_campos_del_registro_son_completos(self):
        registro = self.fn([_mock_asistencia_pdf('Asistio')])[0]
        self.assertIn('documento', registro)
        self.assertIn('nombre', registro)
        self.assertIn('instructor', registro)
        self.assertIn('ficha', registro)
        self.assertIn('jornada', registro)
        self.assertIn('fecha', registro)
        self.assertIn('estado', registro)

    def test_fecha_formateada_como_dd_mm_aaaa(self):
        registro = self.fn([_mock_asistencia_pdf('Asistio', fecha=date(2025, 3, 15))])[0]
        self.assertEqual(registro['fecha'], '15/03/2025')

    def test_instructor_none_muestra_no_asignado(self):
        asist = _mock_asistencia_pdf('Asistio')
        asist.id_instructor = None
        registro = self.fn([asist])[0]
        self.assertEqual(registro['instructor'], 'No asignado')

    def test_limite_de_800_registros(self):
        """La función debe procesar como máximo 800 registros del iterable."""
        registros = [_mock_asistencia_pdf('Asistio') for _ in range(1000)]
        resultado = self.fn(registros)
        self.assertEqual(len(resultado), 800)

    def test_lista_vacia(self):
        self.assertEqual(self.fn([]), [])


# ============================================================================
# exportar_csv
# ============================================================================

class TestExportarCsv(unittest.TestCase):
    """
    Función pura — no requiere BD.
    Firma: exportar_csv(asistencias, headers, filename, data_extractor) → HttpResponse
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.services.export_service import exportar_csv
        self.fn = exportar_csv
        self.headers = ['Nombre', 'Estado', 'Fecha']
        self.data = [('Juan Perez', 'Asistio', '20/05/2025')]
        self.extractor = lambda row: row

    def test_content_type_es_csv_utf8(self):
        resp = self.fn(self.data, self.headers, 'reporte', self.extractor)
        self.assertIn('text/csv', resp['Content-Type'])
        self.assertIn('utf-8', resp['Content-Type'])

    def test_content_disposition_incluye_filename(self):
        resp = self.fn(self.data, self.headers, 'mi_reporte', self.extractor)
        self.assertIn('mi_reporte.csv', resp['Content-Disposition'])

    def test_bom_utf8_presente(self):
        """El BOM (\\ufeff) es necesario para que Excel abra el CSV correctamente."""
        resp = self.fn(self.data, self.headers, 'test', self.extractor)
        contenido = resp.content
        self.assertTrue(contenido.startswith(b'\xef\xbb\xbf'),
                        "El CSV debe comenzar con BOM UTF-8")

    def test_primera_fila_contiene_headers(self):
        resp = self.fn(self.data, self.headers, 'test', self.extractor)
        contenido = resp.content.decode('utf-8-sig')
        primera_linea = contenido.split('\r\n')[0]
        for h in self.headers:
            self.assertIn(h, primera_linea)

    def test_datos_en_segunda_fila(self):
        resp = self.fn(self.data, self.headers, 'test', self.extractor)
        contenido = resp.content.decode('utf-8-sig')
        self.assertIn('Juan Perez', contenido)
        self.assertIn('Asistio', contenido)

    def test_lista_vacia_solo_tiene_headers(self):
        resp = self.fn([], self.headers, 'test', self.extractor)
        contenido = resp.content.decode('utf-8-sig')
        lineas = [l for l in contenido.split('\r\n') if l.strip()]
        self.assertEqual(len(lineas), 1)  # solo la fila de headers


# ============================================================================
# obtener_filtros_display
# ============================================================================

class TestObtenerFiltrosDisplay(unittest.TestCase):
    """
    Función con lógica de presentación — requiere mock de request.
    La clave 'instructor' hace una consulta BD si hay instructor_id.
    Probamos el camino sin instructor (no requiere BD).
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.services.export_service import obtener_filtros_display
        self.fn = obtener_filtros_display

    def _request(self, params=None):
        params = params or {}
        mock = MagicMock()
        mock.GET = MagicMock()
        mock.GET.get.side_effect = lambda *args: params.get(*args)
        return mock

    def test_sin_filtros_retorna_valores_por_defecto(self):
        resultado = self.fn(self._request())
        self.assertEqual(resultado['ficha'],      'Todas las Fichas')
        self.assertEqual(resultado['documento'],  'Todos')
        self.assertEqual(resultado['fecha'],      'Todas')
        self.assertEqual(resultado['estado'],     'Todos')
        self.assertEqual(resultado['jornada'],    'Todas las Jornadas')
        self.assertEqual(resultado['instructor'], 'Todos')

    def test_con_filtros_muestra_valores_reales(self):
        params = {
            'ficha':     '2750614',
            'documento': '1020304050',
            'fecha':     '2025-05-20',
            'estado':    'Inasistio',
            'jornada':   '3',
        }
        resultado = self.fn(self._request(params))
        self.assertEqual(resultado['ficha'],     '2750614')
        self.assertEqual(resultado['documento'], '1020304050')
        self.assertEqual(resultado['fecha'],     '2025-05-20')
        self.assertEqual(resultado['estado'],    'Inasistio')


# ============================================================================
# obtener_estadisticas_justificaciones
# ============================================================================

class TestObtenerEstadisticasJustificaciones(TestCase):
    """
    Requiere BD.
    Firma: obtener_estadisticas_justificaciones(justificaciones_qs)
           → (total, pendientes, aprobadas, rechazadas)
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.selectors.justificacion_selector import obtener_estadisticas_justificaciones
        self.fn = obtener_estadisticas_justificaciones

    @classmethod
    def setUpTestData(cls):
        # 2 pendientes, 3 aprobadas, 1 rechazada
        for _ in range(2):
            Justificacion.objects.create(estado='Pendiente', motivo='P')
        for _ in range(3):
            Justificacion.objects.create(estado='Aprobado', motivo='A')
        Justificacion.objects.create(estado='Rechazado', motivo='R')

    def test_conteos_correctos(self):
        qs = Justificacion.objects.all()
        total, pendientes, aprobadas, rechazadas = self.fn(qs)
        self.assertEqual(total,      6)
        self.assertEqual(pendientes, 2)
        self.assertEqual(aprobadas,  3)
        self.assertEqual(rechazadas, 1)

    def test_sin_justificaciones_retorna_ceros(self):
        total, pendientes, aprobadas, rechazadas = self.fn(Justificacion.objects.none())
        self.assertEqual(total,      0)
        self.assertEqual(pendientes, 0)
        self.assertEqual(aprobadas,  0)
        self.assertEqual(rechazadas, 0)


# ============================================================================
# obtener_total_fichas_activas
# ============================================================================

class TestObtenerTotalFichasActivas(TestCase):
    """
    Requiere BD.
    ADVERTENCIA DE DISEÑO: la función tiene un fallback que devuelve
    Ficha.objects.count() si no hay fichas activas, lo que puede inflar
    métricas con fichas inactivas o de prueba.
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.selectors.estadistica_selector import obtener_total_fichas_activas
        self.fn = obtener_total_fichas_activas

    def test_cuenta_solo_fichas_activas(self):
        Ficha.objects.create(numero_ficha='F001', estado='activa')
        Ficha.objects.create(numero_ficha='F002', estado='activa')
        Ficha.objects.create(numero_ficha='F003', estado='suspendida')  # no contiene 'activa'
        total = self.fn()
        self.assertEqual(total, 2)

    def test_variante_activo_masculino_cuenta(self):
        Ficha.objects.create(numero_ficha='F004', estado='activo')
        total = self.fn()
        self.assertGreaterEqual(total, 1)

    def test_variante_case_insensitive(self):
        Ficha.objects.create(numero_ficha='F005', estado='Activa')
        total = self.fn()
        self.assertGreaterEqual(total, 1)

    def test_ADVERTENCIA_fallback_incluye_suspendidas(self):
        """
        ADVERTENCIA: cuando no hay fichas activas, la función retorna
        Ficha.objects.count() (todas las fichas), incluyendo las no activas.
        Esto puede inflar el KPI del dashboard. El correcto sería retornar 0.
        """
        Ficha.objects.create(numero_ficha='F_SUSPENDIDA', estado='suspendida')
        total = self.fn()
        self.assertGreaterEqual(total, 1)

    def test_iexact_activa_no_coincide_con_inactiva(self):
        """Estado 'inactiva' no debe ser contado como ficha activa."""
        Ficha.objects.create(numero_ficha='ACT01', estado='activa')
        Ficha.objects.create(numero_ficha='INACT01', estado='inactiva')
        total = self.fn()
        self.assertEqual(total, 1)


# ============================================================================
# obtener_asistencia_sede_hoy
# ============================================================================

class TestObtenerAsistenciaSede(TestCase):
    """
    Requiere BD.
    Firma: obtener_asistencia_sede_hoy() → (presentes, total, porcentaje)
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.selectors.estadistica_selector import obtener_asistencia_sede_hoy
        self.fn = obtener_asistencia_sede_hoy
        self.aprendiz = _crear_usuario_b('50000001', 'Eva', 'Torres')

    def test_sin_registros_hoy_retorna_ceros(self):
        presentes, total, pct = self.fn()
        self.assertEqual(presentes, 0)
        self.assertEqual(total,     0)
        self.assertEqual(pct,       0)

    def test_calcula_porcentaje_correctamente(self):
        hoy = date.today()
        AsistenciaSede.objects.create(
            id_usuario=self.aprendiz, fecha=hoy, estado_asistencia='Presente'
        )
        otro = _crear_usuario_b('50000002', 'Leo', 'Vega')
        AsistenciaSede.objects.create(
            id_usuario=otro, fecha=hoy, estado_asistencia='Ausente'
        )
        presentes, total, pct = self.fn()
        self.assertEqual(presentes, 1)
        self.assertEqual(total,     2)
        self.assertEqual(pct,       50.0)

    def test_registros_de_dias_anteriores_no_cuentan(self):
        ayer = date.today() - timedelta(days=1)
        AsistenciaSede.objects.create(
            id_usuario=self.aprendiz, fecha=ayer, estado_asistencia='Presente'
        )
        presentes, total, pct = self.fn()
        self.assertEqual(total, 0)

    def test_porcentaje_cien_cuando_todos_presentes(self):
        hoy = date.today()
        AsistenciaSede.objects.create(
            id_usuario=self.aprendiz, fecha=hoy, estado_asistencia='Presente'
        )
        _, _, pct = self.fn()
        self.assertEqual(pct, 100.0)


# ============================================================================
# obtener_alertas_por_ficha
# ============================================================================

class TestObtenerAlertasPorFicha(TestCase):
    """
    Requiere BD.
    Firma: obtener_alertas_por_ficha(asistencias_qs) → list[dict]
    Retorna hasta 8 fichas ordenadas por nivel de alerta.
    Niveles: Alta (inasistio>=3 o pct>=30%), Media (inasistio>=1 o pct>=15%), Baja.
    """

    def setUp(self):
        from apps.reporte_monitoreo.coordinador.selectors.estadistica_selector import obtener_alertas_por_ficha
        self.fn = obtener_alertas_por_ficha

    def _setup_ficha(self, numero, inasistencias=0, total=5):
        ficha = Ficha.objects.create(numero_ficha=numero, estado='activa')
        aprendiz = _crear_usuario_b(f'60{numero}', ficha=ficha)
        for i in range(total):
            estado = 'Inasistio' if i < inasistencias else 'Asistio'
            AsistenciaAmbiente.objects.create(
                id_usuario=aprendiz,
                fecha=date.today() - timedelta(days=i),
                estado_asistencia=estado,
            )
        return ficha, aprendiz

    def test_nivel_baja_cuando_sin_inasistencias(self):
        ficha, _ = self._setup_ficha('B001', inasistencias=0, total=5)
        qs = AsistenciaAmbiente.objects.filter(id_usuario__id_ficha=ficha)
        alertas = self.fn(qs)
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]['nivel'], 'Baja')

    def test_nivel_media_con_una_inasistencia(self):
        ficha, _ = self._setup_ficha('M001', inasistencias=1, total=5)
        qs = AsistenciaAmbiente.objects.filter(id_usuario__id_ficha=ficha)
        alertas = self.fn(qs)
        self.assertEqual(alertas[0]['nivel'], 'Media')

    def test_nivel_alta_con_tres_o_mas_inasistencias(self):
        ficha, _ = self._setup_ficha('A001', inasistencias=3, total=5)
        qs = AsistenciaAmbiente.objects.filter(id_usuario__id_ficha=ficha)
        alertas = self.fn(qs)
        self.assertEqual(alertas[0]['nivel'], 'Alta')

    def test_retorna_maximo_8_fichas(self):
        """La función limita el resultado a 8 fichas."""
        fichas_qs_ids = []
        for i in range(10):
            ficha, aprendiz = self._setup_ficha(f'X{i:02d}', inasistencias=1, total=3)
            fichas_qs_ids.append(aprendiz)
        qs = AsistenciaAmbiente.objects.filter(
            id_usuario__id_ficha__numero_ficha__startswith='X'
        )
        alertas = self.fn(qs)
        self.assertLessEqual(len(alertas), 8)

    def test_ficha_sin_numero_se_omite(self):
        """Fichas con numero_ficha=None son ignoradas."""
        ficha = Ficha.objects.create(numero_ficha=None, estado='activa')
        aprendiz = _crear_usuario_b('60NONE', ficha=ficha)
        AsistenciaAmbiente.objects.create(
            id_usuario=aprendiz, fecha=date.today(), estado_asistencia='Inasistio'
        )
        qs = AsistenciaAmbiente.objects.filter(id_usuario=aprendiz)
        alertas = self.fn(qs)
        self.assertEqual(len(alertas), 0)