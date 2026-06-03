"""
Pruebas unitarias — apps.gestion_asistencia_justificacion.aprendiz
Archivo consolidado con todos los tests del módulo.

"""

import datetime
import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import (
    AsistenciaAmbiente,
    Competencia,
    Jornada,
    Justificacion,
    Programa,
)

User = get_user_model()


# ─── helpers ────────────────────────────────────────────────────────────────

def _mock_asistencia(fecha, estado, justificada=False):
    """Objeto liviano que simula AsistenciaAmbiente para tests sin BD."""
    return SimpleNamespace(
        fecha=fecha,
        estado_asistencia=estado,
        tiene_justificacion_aprobada=justificada,
    )


def _crear_usuario(cedula, nombre='Test', apellido='User'):
    return Usuarios.objects.create_user(
        cedula=cedula,
        password='testpass123',
        nombre=nombre,
        apellido=apellido,
    )


# ============================================================================
# calcular_dias_entre
# ============================================================================

class TestCalcularDiasEntre(unittest.TestCase):
    """
    Función pura — no requiere base de datos.
    Firma: calcular_dias_entre(fecha_inicio, fecha_fin=None) → int
    """

    def setUp(self):
        from apps.gestion_asistencia_justificacion.aprendiz.utils.fechas import calcular_dias_entre
        self.fn = calcular_dias_entre

    # ── casos normales ────────────────────────────────────────────────────

    def test_diferencia_varios_dias(self):
        self.assertEqual(self.fn(date(2025, 1, 1), date(2025, 1, 10)), 9)

    def test_diferencia_de_un_dia(self):
        self.assertEqual(self.fn(date(2025, 3, 5), date(2025, 3, 6)), 1)

    def test_diferencia_en_anio_bisiesto(self):
        self.assertEqual(self.fn(date(2024, 1, 1), date(2025, 1, 1)), 366)

    # ── casos límite ─────────────────────────────────────────────────────

    def test_mismo_dia_retorna_cero(self):
        d = date(2025, 6, 15)
        self.assertEqual(self.fn(d, d), 0)

    def test_sin_fecha_fin_usa_hoy(self):
        """Pasar solo fecha_inicio = ayer debe retornar 1."""
        ayer = date.today() - timedelta(days=1)
        self.assertEqual(self.fn(ayer), 1)

    def test_fecha_fin_none_explicito_equivale_a_omitirla(self):
        ayer = date.today() - timedelta(days=1)
        self.assertEqual(self.fn(ayer, None), 1)

    # ── casos de error ────────────────────────────────────────────────────

    def test_inicio_posterior_a_fin_retorna_negativo(self):
        """No debe lanzar excepción; retorna diferencia negativa."""
        resultado = self.fn(date(2025, 5, 10), date(2025, 5, 1))
        self.assertEqual(resultado, -9)


# ============================================================================
# analizar_inasistencias
# ============================================================================

class TestAnalizarInasistencias(unittest.TestCase):
    """
    Función pura — no requiere base de datos.
    Firma: analizar_inasistencias(todas_asistencias) → (tiene_3, tiene_5, total)

    Recibe objetos con atributos:
        fecha                       : date
        estado_asistencia           : str  ('Asistio', 'Retardo', 'Inasistio')
        tiene_justificacion_aprobada: bool

    Un día se cuenta como inasistencia completa solo si:
      - NO hubo ningún 'Asistio' ni 'Retardo' ese día, Y
      - Al menos un 'Inasistio' sin justificación aprobada.
    """

    BASE = date(2025, 5, 20)

    def setUp(self):
        from apps.gestion_asistencia_justificacion.aprendiz.services.asistencia_service import analizar_inasistencias
        self.fn = analizar_inasistencias

    def _dia(self, offset_dias, estado='Inasistio', justificada=False):
        """Crea una asistencia N días antes de BASE."""
        return _mock_asistencia(self.BASE - timedelta(days=offset_dias), estado, justificada)

    # ── casos normales ────────────────────────────────────────────────────

    def test_lista_vacia_retorna_ceros(self):
        tiene_3, tiene_5, total = self.fn([])
        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 0)

    def test_todos_asistieron_retorna_ceros(self):
        registros = [self._dia(i, 'Asistio') for i in range(5)]
        tiene_3, tiene_5, total = self.fn(registros)
        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 0)

    def test_inasistencias_todas_justificadas_no_suman(self):
        registros = [self._dia(i, 'Inasistio', justificada=True) for i in range(6)]
        tiene_3, tiene_5, total = self.fn(registros)
        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 0)

    def test_una_inasistencia_injustificada(self):
        datos = [_mock_asistencia(datetime.date(2026, 5, 1), 'Inasistio')]
        tiene_3, tiene_5, total = self.fn(datos)
        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 1)

    # ── detección de 3 días consecutivos ─────────────────────────────────

    def test_tres_dias_consecutivos_activan_tiene_3(self):
        datos = [
            _mock_asistencia(datetime.date(2026, 5, 3), 'Inasistio'),
            _mock_asistencia(datetime.date(2026, 5, 2), 'Inasistio'),
            _mock_asistencia(datetime.date(2026, 5, 1), 'Inasistio'),
        ]
        tiene_3, tiene_5, total = self.fn(datos)
        self.assertTrue(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 3)

    def test_dos_consecutivos_no_activan_tiene_3(self):
        registros = [self._dia(0), self._dia(1)]
        tiene_3, _, _ = self.fn(registros)
        self.assertFalse(tiene_3)

    def test_tres_separados_no_activan_tiene_3(self):
        registros = [self._dia(0), self._dia(3), self._dia(6)]
        tiene_3, _, total = self.fn(registros)
        self.assertFalse(tiene_3)
        self.assertEqual(total, 3)

    def test_consecutivas_detectadas_despues_de_un_gap(self):
        """
        Tres días consecutivos que aparecen DESPUÉS de un gap deben
        detectarse correctamente (el contador se reinicia al ver el gap).

        Secuencia (desc): 20, 19, [gap], 15, 14, 13
          → 15-14-13 son tres consecutivos → tiene_3 debe ser True.
        """
        registros = [
            self._dia(0),   # 20
            self._dia(1),   # 19  ← gap después de aquí
            self._dia(5),   # 15
            self._dia(6),   # 14
            self._dia(7),   # 13  ← tres consecutivos
        ]
        tiene_3, _, _ = self.fn(registros)
        self.assertTrue(tiene_3)

    # ── detección de 5 días totales ───────────────────────────────────────

    def test_cinco_dias_consecutivos_activan_ambas_alertas(self):
        datos = [
            _mock_asistencia(datetime.date(2026, 5, 5), 'Inasistio'),
            _mock_asistencia(datetime.date(2026, 5, 4), 'Inasistio'),
            _mock_asistencia(datetime.date(2026, 5, 3), 'Inasistio'),
            _mock_asistencia(datetime.date(2026, 5, 2), 'Inasistio'),
            _mock_asistencia(datetime.date(2026, 5, 1), 'Inasistio'),
        ]
        tiene_3, tiene_5, total = self.fn(datos)
        self.assertTrue(tiene_3)
        self.assertTrue(tiene_5)
        self.assertEqual(total, 5)

    def test_cinco_dias_espaciados_activan_solo_tiene_5(self):
        registros = [self._dia(i * 4) for i in range(5)]
        tiene_3, tiene_5, total = self.fn(registros)
        self.assertFalse(tiene_3)
        self.assertTrue(tiene_5)
        self.assertEqual(total, 5)

    def test_cuatro_dias_no_activan_tiene_5(self):
        registros = [self._dia(i * 4) for i in range(4)]
        _, tiene_5, _ = self.fn(registros)
        self.assertFalse(tiene_5)

    # ── comportamiento especial de un día ────────────────────────────────

    def test_retardo_mismo_dia_anula_inasistencia(self):
        """Un Retardo en el mismo día que un Inasistio hace que ese día NO cuente."""
        registros = [
            _mock_asistencia(self.BASE, 'Retardo'),
            _mock_asistencia(self.BASE, 'Inasistio'),
        ]
        _, _, total = self.fn(registros)
        self.assertEqual(total, 0)

    def test_asistio_y_inasistio_mismo_dia_no_cuenta(self):
        registros = [
            _mock_asistencia(self.BASE, 'Asistio'),
            _mock_asistencia(self.BASE, 'Inasistio'),
        ]
        _, _, total = self.fn(registros)
        self.assertEqual(total, 0)

    def test_multiples_inasistencias_mismo_dia_cuentan_como_una(self):
        registros = [_mock_asistencia(self.BASE, 'Inasistio') for _ in range(4)]
        _, _, total = self.fn(registros)
        self.assertEqual(total, 1)

    # ── combinados ───────────────────────────────────────────────────────

    def test_tres_consecutivos_mas_dos_separados_activan_ambas_alertas(self):
        consecutivos = [self._dia(i) for i in range(3)]   # 20, 19, 18
        separados    = [self._dia(10), self._dia(20)]
        tiene_3, tiene_5, total = self.fn(consecutivos + separados)
        self.assertTrue(tiene_3)
        self.assertTrue(tiene_5)
        self.assertEqual(total, 5)


# ============================================================================
# crear_justificaciones
# ============================================================================

class TestCrearJustificaciones(TestCase):
    """
    Requiere BD + mock de default_storage.
    Firma: crear_justificaciones(usuario, inasistencias_ids, motivo, soporte) → int

    Restricción clave: solo se justifican inasistencias con <= 3 días de antigüedad.
    """

    @classmethod
    def setUpTestData(cls):
        cls.aprendiz = _crear_usuario('11111111', 'Juan', 'Perez')
        hoy = date.today()
        cls.asistencia_reciente = AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz,
            fecha=hoy - timedelta(days=1),
            estado_asistencia='Inasistio',
        )
        cls.asistencia_hoy = AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz,
            fecha=hoy,
            estado_asistencia='Inasistio',
        )
        cls.asistencia_en_limite = AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz,
            fecha=hoy - timedelta(days=3),   # exactamente 3 días → DEBE aceptarse
            estado_asistencia='Inasistio',
        )
        cls.asistencia_antigua = AsistenciaAmbiente.objects.create(
            id_usuario=cls.aprendiz,
            fecha=hoy - timedelta(days=4),   # 4 días → DEBE rechazarse
            estado_asistencia='Inasistio',
        )

    def setUp(self):
        from apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service import crear_justificaciones
        self.fn = crear_justificaciones
        self.soporte = MagicMock()
        self.soporte.name = 'documento.pdf'

    def tearDown(self):
        Justificacion.objects.all().delete()

    # ── casos normales ────────────────────────────────────────────────────

    @patch('apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service.default_storage')
    def test_crea_justificacion_para_inasistencia_reciente(self, mock_storage):
        mock_storage.save.return_value = 'justificaciones/test.pdf'
        creadas = self.fn(
            self.aprendiz,
            [self.asistencia_reciente.id_asistencia_ambiente],
            'Cita médica',
            self.soporte,
        )
        self.assertEqual(creadas, 1)
        self.assertTrue(
            Justificacion.objects.filter(
                id_asistencia_ambiente=self.asistencia_reciente,
                estado='Pendiente',
                motivo='Cita médica',
            ).exists()
        )

    @patch('apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service.default_storage')
    def test_crea_multiples_justificaciones(self, mock_storage):
        """Se puede justificar más de una inasistencia en la misma llamada."""
        mock_storage.save.return_value = 'justificaciones/test.pdf'
        creadas = self.fn(
            self.aprendiz,
            [
                self.asistencia_reciente.id_asistencia_ambiente,
                self.asistencia_hoy.id_asistencia_ambiente,
            ],
            'Calamidad',
            self.soporte,
        )
        self.assertEqual(creadas, 2)

    # ── casos límite ─────────────────────────────────────────────────────

    @patch('apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service.default_storage')
    def test_acepta_inasistencia_exactamente_en_limite_de_3_dias(self, mock_storage):
        """dias_pasados == 3 debe ser aceptado (condición es > 3, no >= 3)."""
        mock_storage.save.return_value = 'justificaciones/test.pdf'
        creadas = self.fn(
            self.aprendiz,
            [self.asistencia_en_limite.id_asistencia_ambiente],
            'Emergencia',
            self.soporte,
        )
        self.assertEqual(creadas, 1)

    @patch('apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service.default_storage')
    def test_rechaza_inasistencia_con_mas_de_3_dias(self, mock_storage):
        creadas = self.fn(
            self.aprendiz,
            [self.asistencia_antigua.id_asistencia_ambiente],
            'Cita médica',
            self.soporte,
        )
        self.assertEqual(creadas, 0)
        self.assertFalse(
            Justificacion.objects.filter(id_asistencia_ambiente=self.asistencia_antigua).exists()
        )

    def test_lista_vacia_de_ids_retorna_cero(self):
        creadas = self.fn(self.aprendiz, [], 'Motivo', self.soporte)
        self.assertEqual(creadas, 0)

    # ── casos de error ────────────────────────────────────────────────────

    @patch('apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service.default_storage')
    def test_id_inexistente_se_omite_sin_excepcion(self, mock_storage):
        """Un ID que no existe en BD debe ignorarse (DoesNotExist → continue)."""
        creadas = self.fn(self.aprendiz, [999999], 'Motivo', self.soporte)
        self.assertEqual(creadas, 0)

    @patch('apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service.default_storage')
    def test_no_justifica_asistencia_de_otro_aprendiz(self, mock_storage):
        """La consulta filtra por id_usuario; IDs de otro aprendiz son ignorados."""
        otro = _crear_usuario('99999999', 'Otro', 'Aprendiz')
        asistencia_otro = AsistenciaAmbiente.objects.create(
            id_usuario=otro,
            fecha=date.today() - timedelta(days=1),
            estado_asistencia='Inasistio',
        )
        creadas = self.fn(
            self.aprendiz,
            [asistencia_otro.id_asistencia_ambiente],
            'Cita médica',
            self.soporte,
        )
        self.assertEqual(creadas, 0)


# ============================================================================
# obtener_asistencias_usuario (selector)
# ============================================================================

class TestAsistenciasSelector(TestCase):
    """Pruebas para selectors.asistencia_selector.obtener_asistencias_usuario."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user(
            cedula='22200001',
            correo='selector@test.com',
            nombre='Selector',
            apellido='User',
            telefono='123',
            estado='ACTIVO',
            password='123',
        )
        cls.programa = Programa.objects.create(
            nombre_programa='ADSO',
            tipo_programa='Tecnólogo',
        )
        cls.jornada = Jornada.objects.create(
            nombre_jornada='Mañana',
            hora_inicio='06:00',
            hora_fin='12:00',
        )
        cls.competencia = Competencia.objects.create(
            nombre_competencia='Python',
            descripcion='Programación',
            estado='ACTIVA',
            id_programa=cls.programa,
        )
        cls.asistencia = AsistenciaAmbiente.objects.create(
            id_usuario=cls.usuario,
            id_competencia=cls.competencia,
            estado_asistencia='INASISTENTE',
        )

    def setUp(self):
        from apps.gestion_asistencia_justificacion.aprendiz.selectors.asistencia_selector import obtener_asistencias_usuario
        self.fn = obtener_asistencias_usuario

    def test_sin_justificacion_aprobada_el_flag_es_false(self):
        resultado = self.fn(self.usuario)
        asistencia = resultado.first()
        self.assertFalse(asistencia.tiene_justificacion_aprobada)

    def test_con_justificacion_aprobada_el_flag_es_true(self):
        Justificacion.objects.create(
            id_asistencia_ambiente=self.asistencia,
            estado='Aprobado',
        )
        resultado = self.fn(self.usuario)
        asistencia = resultado.first()
        self.assertTrue(asistencia.tiene_justificacion_aprobada)


# ============================================================================
# obtener_inasistencias_usuario (selector)
# ============================================================================

class TestInasistenciasSelector(TestCase):
    """Pruebas para selectors.inasistencias_selector.obtener_inasistencias_usuario."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user(
            cedula='33300001',
            correo='inasist@test.com',
            nombre='Inasist',
            apellido='User',
            telefono='123',
            estado='ACTIVO',
            password='123',
        )
        cls.programa = Programa.objects.create(
            nombre_programa='ADSO',
            tipo_programa='Tecnólogo',
        )
        cls.jornada = Jornada.objects.create(
            nombre_jornada='Tarde',
            hora_inicio='12:00',
            hora_fin='18:00',
        )
        cls.competencia = Competencia.objects.create(
            nombre_competencia='Django',
            descripcion='Framework',
            estado='ACTIVA',
            id_programa=cls.programa,
        )
        AsistenciaAmbiente.objects.create(
            id_usuario=cls.usuario,
            id_competencia=cls.competencia,
            estado_asistencia='INASISTENTE',
        )

    def setUp(self):
        from apps.gestion_asistencia_justificacion.aprendiz.selectors.inasistencias_selector import obtener_inasistencias_usuario
        self.fn = obtener_inasistencias_usuario

    def test_retorna_las_inasistencias_del_usuario(self):
        resultado = self.fn(self.usuario)
        self.assertEqual(resultado.count(), 1)

    def test_incluye_prefetch_de_justificaciones(self):
        resultado = self.fn(self.usuario)
        asistencia = resultado.first()
        self.assertTrue(hasattr(asistencia, 'justificaciones'))
        self.assertEqual(len(asistencia.justificaciones), 0)


# ============================================================================
# Vistas: consultar_asistencia / radicar_justificacion
# ============================================================================

class TestVistasAprendiz(TestCase):
    """Pruebas de integración para las vistas del módulo aprendiz."""

    def setUp(self):
        self.client = Client()
        self.usuario = Usuarios.objects.create(
            cedula='44400001',
            nombre='Vista',
            apellido='User',
            correo='vista@test.com',
            estado='Activo',
        )
        self.competencia = Competencia.objects.create(
            nombre_competencia='Python',
            descripcion='Test',
            estado='ACTIVO',
        )
        self.asistencia = AsistenciaAmbiente.objects.create(
            id_usuario=self.usuario,
            id_competencia=self.competencia,
            fecha=datetime.date.today(),
            estado_asistencia='Inasistio',
        )

    # ── consultar_asistencia ──────────────────────────────────────────────

    def test_consultar_asistencia_retorna_200(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('aprendiz:consultar_asistencia'))
        self.assertEqual(response.status_code, 200)

    def test_consultar_asistencia_contexto_contiene_claves(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('aprendiz:consultar_asistencia'))
        self.assertIn('asistencias', response.context)
        self.assertIn('competencias', response.context)

    # ── radicar_justificacion ─────────────────────────────────────────────

    def test_get_radicar_justificacion_retorna_200(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('aprendiz:radicar_justificacion'))
        self.assertEqual(response.status_code, 200)

    def test_post_justificacion_exitosa_redirige(self):
        self.client.force_login(self.usuario)
        archivo = SimpleUploadedFile('soporte.pdf', b'test')
        response = self.client.post(
            reverse('aprendiz:radicar_justificacion'),
            {
                'inasistencias': [self.asistencia.id_asistencia_ambiente],
                'motivo': 'Prueba',
                'soporte': archivo,
            },
        )
        self.assertEqual(response.status_code, 302)
