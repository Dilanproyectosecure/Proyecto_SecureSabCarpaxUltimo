"""
Tests unitarios para apps.seguridad_administracion.vigilante

Ejecutar:
    python manage.py test apps.seguridad_administracion.vigilante -v 2

"""
import json
from datetime import time
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.seguridad_administracion.vigilante.models import Area, Visitante, RegistroManual
from apps.seguridad_administracion.vigilante.views import (
    validar_nombre_apellido,
    iniciov,
    consultar_invitado,
    registrar_invitado,
    entrada_invitado,
    salida_invitado,
    registro_manual,
    historial,
    buscar_visitante_por_cedula,
)


# ─── Helpers compartidos ──────────────────────────────────────────────────────

def _usuario_mock(nombre='Juan', estado='Activo'):
    """Usuario autenticado en memoria, sin acceso a BD."""
    user = MagicMock()
    user.is_authenticated = True
    user.nombre = nombre
    user.apellido = 'Vigilante'
    user.cedula = '12345678'
    user.estado = estado
    return user


def _request(factory, method, path, data=None, autenticado=True):
    """
    Request listo con soporte completo de messages (FallbackStorage).
    Usa RequestFactory para no pasar por middleware ni BD de sesiones.
    """
    build = factory.get if method == 'GET' else factory.post
    req = build(path, data or {})
    req.user = _usuario_mock() if autenticado else AnonymousUser()
    req.session = {}
    req._messages = FallbackStorage(req)
    return req


def _mensajes(request):
    """Extrae los mensajes agregados al request durante la ejecución de la vista."""
    return [str(m) for m in list(request._messages)]


def _qs_mock(items=None):
    """
    Mock que simula un QuerySet completamente encadenable.
    Soporta: filter, select_related, all, order_by, count, first, none,
    iteración y slicing.
    """
    qs = MagicMock()
    qs.filter.return_value = qs
    qs.annotate.return_value = qs
    qs.select_related.return_value = qs
    qs.all.return_value = qs
    qs.order_by.return_value = qs
    qs.none.return_value = []
    qs.count.return_value = len(items or [])
    qs.first.return_value = (items[0] if items else None)
    qs.__iter__ = MagicMock(return_value=iter(items or []))
    qs.__getitem__ = MagicMock(return_value=items or [])
    return qs


# ─── 1. validar_nombre_apellido ───────────────────────────────────────────────

class TestValidarNombreApellido(SimpleTestCase):

    def test_nombre_valido_retorna_true_y_sin_error(self):
        ok, msg = validar_nombre_apellido('Carlos', 'Nombre')
        self.assertTrue(ok)
        self.assertEqual(msg, '')

    def test_nombre_con_acento_es_valido(self):
        ok, _ = validar_nombre_apellido('Sofía', 'Nombre')
        self.assertTrue(ok)

    def test_nombre_con_enye_es_valido(self):
        ok, _ = validar_nombre_apellido('Muñoz', 'Nombre')
        self.assertTrue(ok)

    def test_nombre_multipalabra_es_valido(self):
        ok, _ = validar_nombre_apellido('Juan Pablo', 'Nombre')
        self.assertTrue(ok)

    def test_nombre_exactamente_3_chars_es_valido(self):
        ok, _ = validar_nombre_apellido('Ana', 'Nombre')
        self.assertTrue(ok)

    def test_nombre_exactamente_40_chars_es_valido(self):
        ok, _ = validar_nombre_apellido('A' * 40, 'Nombre')
        self.assertTrue(ok)

    def test_nombre_de_2_chars_falla(self):
        ok, msg = validar_nombre_apellido('Al', 'Nombre')
        self.assertFalse(ok)
        self.assertIn('3', msg)

    def test_nombre_de_41_chars_falla(self):
        ok, msg = validar_nombre_apellido('A' * 41, 'Nombre')
        self.assertFalse(ok)
        self.assertIn('40', msg)

    def test_nombre_con_numeros_falla(self):
        ok, msg = validar_nombre_apellido('Carlos3', 'Nombre')
        self.assertFalse(ok)
        self.assertIn('alfabéticos', msg)

    def test_nombre_con_caracteres_especiales_falla(self):
        ok, _ = validar_nombre_apellido('Ana@!', 'Nombre')
        self.assertFalse(ok)

    def test_none_falla_con_mensaje_requerido(self):
        ok, msg = validar_nombre_apellido(None, 'El apellido')
        self.assertFalse(ok)
        self.assertIn('requerido', msg)

    def test_cadena_vacia_falla(self):
        ok, _ = validar_nombre_apellido('', 'Nombre')
        self.assertFalse(ok)

    def test_solo_espacios_falla(self):
        ok, _ = validar_nombre_apellido('   ', 'Nombre')
        self.assertFalse(ok)

    def test_mensaje_error_contiene_nombre_del_campo(self):
        _, msg = validar_nombre_apellido(None, 'El apellido')
        self.assertIn('El apellido', msg)


# ─── 2. Métodos __str__ de modelos ────────────────────────────────────────────

class TestModelStr(SimpleTestCase):

    def test_area_str_retorna_nombre(self):
        self.assertEqual(str(Area(nombre='Sistemas')), 'Sistemas')

    def test_visitante_str_concatena_nombre_y_apellido(self):
        self.assertEqual(str(Visitante(nombre='Ana', apellido='Gómez')), 'Ana Gómez')

    def test_visitante_str_con_nulos_no_falla(self):
        self.assertEqual(str(Visitante(nombre=None, apellido=None)), 'None None')

    def test_registro_manual_str_prefiere_campo_nombre(self):
        reg = RegistroManual(nombre='Pedro', nombres=None, tipo_movimiento='Ingreso')
        self.assertEqual(str(reg), 'Pedro - Ingreso')

    def test_registro_manual_str_usa_nombres_si_nombre_es_none(self):
        reg = RegistroManual(nombre=None, nombres='Lucia Morales', tipo_movimiento='Salida')
        self.assertEqual(str(reg), 'Lucia Morales - Salida')


# ─── 3. iniciov ───────────────────────────────────────────────────────────────

class TestIniciovView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_get_retorna_200(self, mock_v, mock_rm, mock_render):
        mock_v.count.return_value = 5
        mock_v.filter.return_value.count.return_value = 2
        mock_rm.filter.return_value.count.return_value = 3
        mock_rm.count.return_value = 10
        mock_render.return_value = HttpResponse(status=200)

        resp = iniciov(_request(self.factory, 'GET', '/vigilante/iniciov/'))
        self.assertEqual(resp.status_code, 200)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_contexto_contiene_stats_con_valores_correctos(self, mock_v, mock_rm, mock_render):
        mock_v.count.return_value = 8
        mock_v.filter.return_value.count.return_value = 3
        mock_rm.filter.return_value.count.return_value = 2
        mock_rm.count.return_value = 20
        mock_render.return_value = HttpResponse(status=200)

        iniciov(_request(self.factory, 'GET', '/vigilante/iniciov/'))

        _, template, ctx = mock_render.call_args[0]
        self.assertEqual(template, 'iniciov.html')
        self.assertEqual(ctx['stats']['totalVisitantes'], 8)
        self.assertEqual(ctx['stats']['visitantesDentro'], 3)
        self.assertEqual(ctx['stats']['movimientosHoy'], 2)
        self.assertEqual(ctx['stats']['totalMovimientos'], 20)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_contexto_usa_nombre_del_usuario_autenticado(self, mock_v, mock_rm, mock_render):
        mock_v.count.return_value = 0
        mock_v.filter.return_value.count.return_value = 0
        mock_rm.filter.return_value.count.return_value = 0
        mock_rm.count.return_value = 0
        mock_render.return_value = HttpResponse(status=200)

        iniciov(_request(self.factory, 'GET', '/vigilante/iniciov/'))

        _, _, ctx = mock_render.call_args[0]
        self.assertEqual(ctx['vigilante_nombre'], 'Juan')

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido_al_login(self):
        req = _request(self.factory, 'GET', '/vigilante/iniciov/', autenticado=False)
        resp = iniciov(req)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)


# ─── 4. consultar_invitado ────────────────────────────────────────────────────

class TestConsultarInvitadoView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_get_retorna_200(self, mock_v, mock_area, mock_render):
        mock_v.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        resp = consultar_invitado(_request(self.factory, 'GET', '/vigilante/consultar-invitado/'))
        self.assertEqual(resp.status_code, 200)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_filtro_nombre_invoca_filter_en_queryset(self, mock_v, mock_area, mock_render):
        qs = _qs_mock()
        mock_v.select_related.return_value.all.return_value.order_by.return_value = qs
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        consultar_invitado(_request(
            self.factory, 'GET', '/vigilante/consultar-invitado/', {'nombre': 'Carlos'}
        ))
        qs.filter.assert_called()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_filtro_nombre_completo_aplica_un_filtro_por_palabra(self, mock_v, mock_area, mock_render):
        qs = _qs_mock()
        mock_v.select_related.return_value.all.return_value.order_by.return_value = qs
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        consultar_invitado(_request(
            self.factory, 'GET', '/vigilante/consultar-invitado/', {'nombre': 'Juan Perez'}
        ))
        self.assertEqual(qs.annotate.call_count, 1)
        self.assertEqual(qs.filter.call_count, 1)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_filtro_cedula_invoca_filter_en_queryset(self, mock_v, mock_area, mock_render):
        qs = _qs_mock()
        mock_v.select_related.return_value.all.return_value.order_by.return_value = qs
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        consultar_invitado(_request(
            self.factory, 'GET', '/vigilante/consultar-invitado/', {'cedula': '9999'}
        ))
        qs.filter.assert_called()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_contexto_incluye_areas_activas(self, mock_v, mock_area, mock_render):
        mock_v.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        areas = [MagicMock(nombre='Sistemas'), MagicMock(nombre='Redes')]
        mock_area.filter.return_value.order_by.return_value = areas
        mock_render.return_value = HttpResponse(status=200)

        consultar_invitado(_request(self.factory, 'GET', '/vigilante/consultar-invitado/'))

        _, _, ctx = mock_render.call_args[0]
        self.assertEqual(ctx['areas'], areas)

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(self.factory, 'GET', '/vigilante/consultar-invitado/', autenticado=False)
        self.assertEqual(consultar_invitado(req).status_code, 302)


# ─── 5. registrar_invitado ────────────────────────────────────────────────────

class TestRegistrarInvitadoView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_get_retorna_200(self, mock_area, mock_render):
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)
        resp = registrar_invitado(_request(self.factory, 'GET', '/vigilante/registrar-invitado/'))
        self.assertEqual(resp.status_code, 200)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_campos_obligatorios_vacios_muestra_error(self, mock_area, mock_render):
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': '', 'apellido': '', 'cedula': '', 'motivo': '',
        })
        registrar_invitado(req)
        self.assertTrue(any('obligatorios' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_nombre_con_numeros_muestra_error_alfabetico(self, mock_area, mock_render):
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'Carlos123', 'apellido': 'Valido', 'cedula': '9999', 'motivo': 'Test',
        })
        registrar_invitado(req)
        self.assertTrue(any('alfabéticos' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_apellido_invalido_muestra_error(self, mock_area, mock_render):
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'Carlos', 'apellido': '99abc', 'cedula': '9999', 'motivo': 'Test',
        })
        registrar_invitado(req)
        self.assertTrue(len(_mensajes(req)) > 0)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_visita_activa_existente_bloquea_nuevo_registro(self, mock_area, mock_v, mock_render):
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)
        qs = _qs_mock()
        qs.first.return_value = MagicMock(nombre='Luis', apellido='Torres')
        mock_v.filter.return_value.select_related.return_value = qs

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'Ana', 'apellido': 'Perez', 'cedula': '99999', 'motivo': 'Visita',
        })
        registrar_invitado(req)
        msgs = _mensajes(req)
        self.assertTrue(any('salida' in m.lower() or 'no se puede' in m.lower() for m in msgs))

    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_nuevo_invitado_valido_redirige_a_consultar(self, mock_area, mock_as, mock_v):
        mock_area.filter.return_value.order_by.return_value = []
        qs = _qs_mock()
        qs.first.return_value = None
        mock_v.filter.return_value.select_related.return_value = qs
        mock_as.create.return_value = MagicMock()
        mock_v.create.return_value = MagicMock()

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'Ana', 'apellido': 'Perez', 'cedula': '99999', 'motivo': 'Visita',
        })
        resp = registrar_invitado(req)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('consultar', resp.url)

    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_nombre_capitalizado_antes_de_guardar(self, mock_area, mock_as, mock_v):
        mock_area.filter.return_value.order_by.return_value = []
        qs = _qs_mock()
        qs.first.return_value = None
        mock_v.filter.return_value.select_related.return_value = qs
        mock_as.create.return_value = MagicMock()
        mock_v.create.return_value = MagicMock()

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'ANA LUCIA', 'apellido': 'PEREZ GOMEZ',
            'cedula': '111', 'motivo': 'Test',
        })
        registrar_invitado(req)
        kwargs = mock_v.create.call_args[1]
        self.assertEqual(kwargs['nombre'], 'Ana Lucia')
        self.assertEqual(kwargs['apellido'], 'Perez Gomez')

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.get_object_or_404')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_editar_con_ingreso_activo_sin_salida_bloquea(self, mock_area, mock_404, mock_render):
        mock_area.filter.return_value.order_by.return_value = []
        mock_render.return_value = HttpResponse(status=200)
        asistencia = MagicMock(hora_salida=None)
        mock_404.return_value = MagicMock(
            nombre='Pedro', apellido='Ruiz', id_asistencia_sede=asistencia
        )

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'Pedro', 'apellido': 'Ruiz', 'cedula': '111',
            'motivo': 'Test', 'id_visitante': '42',
        })
        registrar_invitado(req)
        msgs = _mensajes(req)
        self.assertTrue(any('salida' in m.lower() or 'activo' in m.lower() for m in msgs))

    @patch('apps.seguridad_administracion.vigilante.views.get_object_or_404')
    @patch('apps.seguridad_administracion.vigilante.views.Area.objects')
    def test_post_editar_con_salida_ya_registrada_guarda_cambios(self, mock_area, mock_404):
        mock_area.filter.return_value.order_by.return_value = []
        asistencia = MagicMock(hora_salida=time(17, 0))
        visitante = MagicMock(nombre='Pedro', apellido='Ruiz', id_asistencia_sede=asistencia)
        mock_404.return_value = visitante

        req = _request(self.factory, 'POST', '/vigilante/registrar-invitado/', {
            'nombre': 'Pedro', 'apellido': 'Ruiz', 'cedula': '111',
            'motivo': 'Test', 'id_visitante': '42',
        })
        resp = registrar_invitado(req)
        visitante.save.assert_called_once()
        self.assertEqual(resp.status_code, 302)

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(self.factory, 'GET', '/vigilante/registrar-invitado/', autenticado=False)
        self.assertEqual(registrar_invitado(req).status_code, 302)


# ─── 6. entrada_invitado ──────────────────────────────────────────────────────

class TestEntradaInvitadoView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.get_object_or_404')
    def test_invitado_ya_dentro_emite_warning_y_redirige(self, mock_404):
        asistencia = MagicMock(hora_salida=None)
        mock_404.return_value = MagicMock(id_asistencia_sede=asistencia)

        req = _request(self.factory, 'GET', '/vigilante/entrada-invitado/1/')
        resp = entrada_invitado(req, visitante_id=1)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(any('ya está dentro' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.get_object_or_404')
    def test_nueva_entrada_crea_asistencia_actualiza_visitante_y_redirige(self, mock_404, mock_as):
        asistencia_previa = MagicMock(hora_salida=time(14, 0))
        visitante = MagicMock(
            id_asistencia_sede=asistencia_previa,
            nombre='Luis', apellido='Torres'
        )
        mock_404.return_value = visitante
        mock_as.create.return_value = MagicMock()

        req = _request(self.factory, 'GET', '/vigilante/entrada-invitado/1/')
        resp = entrada_invitado(req, visitante_id=1)

        mock_as.create.assert_called_once()
        visitante.save.assert_called_once()
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(any('Entrada' in m for m in _mensajes(req)))

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(self.factory, 'GET', '/vigilante/entrada-invitado/1/', autenticado=False)
        resp = entrada_invitado(req, visitante_id=1)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)


# ─── 7. salida_invitado ───────────────────────────────────────────────────────

class TestSalidaInvitadoView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.get_object_or_404')
    def test_salida_ya_registrada_emite_warning_y_redirige(self, mock_404):
        asistencia = MagicMock(hora_salida=time(17, 0))
        mock_404.return_value = MagicMock(id_asistencia_sede=asistencia)

        req = _request(self.factory, 'GET', '/vigilante/salida-invitado/1/')
        resp = salida_invitado(req, visitante_id=1)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(any('ya tiene registrada' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.get_object_or_404')
    def test_salida_exitosa_actualiza_estado_asistencia_y_redirige(self, mock_404):
        asistencia = MagicMock(hora_salida=None)
        visitante = MagicMock(
            id_asistencia_sede=asistencia,
            nombre='Ana', apellido='López'
        )
        mock_404.return_value = visitante

        req = _request(self.factory, 'GET', '/vigilante/salida-invitado/1/')
        resp = salida_invitado(req, visitante_id=1)

        asistencia.save.assert_called_once()
        self.assertEqual(asistencia.estado_asistencia, 'Fuera')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(any('Salida' in m for m in _mensajes(req)))

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(self.factory, 'GET', '/vigilante/salida-invitado/1/', autenticado=False)
        resp = salida_invitado(req, visitante_id=1)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)


# ─── 8. registro_manual ───────────────────────────────────────────────────────

class TestRegistroManualView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    def test_get_retorna_200(self, mock_rm, mock_render):
        mock_rm.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_render.return_value = HttpResponse(status=200)

        resp = registro_manual(_request(self.factory, 'GET', '/vigilante/registro-manual/'))
        self.assertEqual(resp.status_code, 200)

    def test_post_sin_documento_redirige_con_error(self):
        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '', 'tipoMovimiento': 'Ingreso',
        })
        resp = registro_manual(req)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(any('cédula' in m.lower() or 'documento' in m.lower()
                            for m in _mensajes(req)))

    def test_post_sin_tipo_movimiento_redirige_con_error(self):
        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': '',
        })
        resp = registro_manual(req)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(any('movimiento' in m.lower() for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_documento_no_registrado_muestra_error(self, mock_u):
        from apps.login.models import Usuarios as U
        mock_u.get.side_effect = U.DoesNotExist

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '00000', 'tipoMovimiento': 'Ingreso',
        })
        registro_manual(req)
        self.assertTrue(any('no está registrado' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_usuario_inactivo_muestra_error(self, mock_u):
        mock_u.get.return_value = MagicMock(estado='Inactivo', nombre='Pedro', apellido='Ruiz')

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Ingreso',
        })
        registro_manual(req)
        self.assertTrue(any('no está activo' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_ingreso_con_ingreso_pendiente_no_crea_asistencia(self, mock_u, mock_as):
        mock_u.get.return_value = MagicMock(estado='Activo', nombre='Ana', apellido='Ruiz')
        mock_as.filter.return_value.exists.return_value = True

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Ingreso',
        })
        registro_manual(req)
        mock_as.create.assert_not_called()

    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_ingreso_exitoso_crea_asistencia_y_registro_manual(self, mock_u, mock_as, mock_rm):
        mock_u.get.return_value = MagicMock(estado='Activo', nombre='Carlos', apellido='López')
        mock_as.filter.return_value.exists.return_value = False
        mock_as.create.return_value = MagicMock()
        mock_rm.create.return_value = MagicMock()

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Ingreso', 'motivo': 'Trabajo',
        })
        registro_manual(req)

        mock_as.create.assert_called_once()
        mock_rm.create.assert_called_once()
        self.assertTrue(any('exitosamente' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_salida_sin_ingreso_previo_hoy_muestra_error(self, mock_u, mock_as):
        mock_u.get.return_value = MagicMock(estado='Activo', nombre='Carlos', apellido='López')
        mock_as.filter.return_value.first.return_value = None

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Salida',
        })
        registro_manual(req)
        self.assertTrue(any('no tiene un ingreso' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_salida_exitosa_actualiza_estado_y_hora_asistencia(self, mock_u, mock_as, mock_rm):
        mock_u.get.return_value = MagicMock(estado='Activo', nombre='Carlos', apellido='López')
        asistencia = MagicMock()
        mock_as.filter.return_value.first.return_value = asistencia
        mock_rm.create.return_value = MagicMock()

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Salida',
        })
        registro_manual(req)

        asistencia.save.assert_called_once()
        self.assertEqual(asistencia.estado_asistencia, 'Salida')
        self.assertTrue(any('exitosamente' in m for m in _mensajes(req)))

    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_motivo_vacio_guarda_fallo_lectura_huella(self, mock_u, mock_as, mock_rm):
        mock_u.get.return_value = MagicMock(estado='Activo', nombre='Ana', apellido='Ruiz')
        mock_as.filter.return_value.exists.return_value = False
        mock_as.create.return_value = MagicMock()
        mock_rm.create.return_value = MagicMock()

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Ingreso', 'motivo': '',
        })
        registro_manual(req)

        kwargs = mock_rm.create.call_args[1]
        self.assertEqual(kwargs['motivo'], 'Fallo Lectura Huella')

    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.AsistenciaSede.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Usuarios.objects')
    def test_post_registro_manual_guarda_tipo_registro_manual(self, mock_u, mock_as, mock_rm):
        mock_u.get.return_value = MagicMock(estado='Activo', nombre='Ana', apellido='Ruiz')
        mock_as.filter.return_value.exists.return_value = False
        mock_as.create.return_value = MagicMock()
        mock_rm.create.return_value = MagicMock()

        req = _request(self.factory, 'POST', '/vigilante/registro-manual/', {
            'documento': '12345', 'tipoMovimiento': 'Ingreso', 'motivo': 'Test',
        })
        registro_manual(req)

        kwargs = mock_rm.create.call_args[1]
        self.assertEqual(kwargs['tipo_registro'], 'Manual')

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(self.factory, 'GET', '/vigilante/registro-manual/', autenticado=False)
        resp = registro_manual(req)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)


# ─── 9. historial ─────────────────────────────────────────────────────────────

class TestHistorialView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_get_retorna_200(self, mock_v, mock_rm, mock_render):
        mock_v.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_rm.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_render.return_value = HttpResponse(status=200)

        resp = historial(_request(self.factory, 'GET', '/vigilante/historial/'))
        self.assertEqual(resp.status_code, 200)

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_filtro_tipo_visitante_pone_registros_manual_en_none(self, mock_v, mock_rm, mock_render):
        mock_v.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_rm.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_rm.none.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        historial(_request(
            self.factory, 'GET', '/vigilante/historial/', {'tipo': 'Visitante'}
        ))
        _, _, ctx = mock_render.call_args[0]
        self.assertIsNone(ctx['registrosManual'])

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_filtro_tipo_manual_pone_visitantes_en_none(self, mock_v, mock_rm, mock_render):
        mock_v.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_rm.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_v.none.return_value = []
        mock_render.return_value = HttpResponse(status=200)

        historial(_request(
            self.factory, 'GET', '/vigilante/historial/', {'tipo': 'Manual'}
        ))
        _, _, ctx = mock_render.call_args[0]
        self.assertIsNone(ctx['visitantes'])

    @patch('apps.seguridad_administracion.vigilante.views.render')
    @patch('apps.seguridad_administracion.vigilante.views.RegistroManual.objects')
    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_contexto_contiene_clave_registros_unificados(self, mock_v, mock_rm, mock_render):
        mock_v.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_rm.select_related.return_value.all.return_value.order_by.return_value = _qs_mock()
        mock_render.return_value = HttpResponse(status=200)

        historial(_request(self.factory, 'GET', '/vigilante/historial/'))
        _, _, ctx = mock_render.call_args[0]
        self.assertIn('registros_unificados', ctx)

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(self.factory, 'GET', '/vigilante/historial/', autenticado=False)
        self.assertEqual(historial(req).status_code, 302)


# ─── 10. buscar_visitante_por_cedula (API AJAX) ───────────────────────────────

class TestBuscarVisitantePorCedulaView(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_sin_parametro_cedula_retorna_400(self):
        req = _request(self.factory, 'GET', '/vigilante/api/buscar-visitante/')
        resp = buscar_visitante_por_cedula(req)
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(json.loads(resp.content)['encontrado'])

    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_cedula_inexistente_retorna_encontrado_false(self, mock_v):
        mock_v.filter.return_value.order_by.return_value.first.return_value = None

        req = _request(self.factory, 'GET', '/vigilante/api/buscar-visitante/', {'cedula': '00000'})
        resp = buscar_visitante_por_cedula(req)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content)['encontrado'])

    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_cedula_existente_retorna_datos_completos_del_visitante(self, mock_v):
        visitante = MagicMock(
            nombre='María', apellido='López',
            tipo_documento='CC', id_visitante=7
        )
        mock_v.filter.return_value.order_by.return_value.first.return_value = visitante

        req = _request(
            self.factory, 'GET', '/vigilante/api/buscar-visitante/', {'cedula': '12345678'}
        )
        data = json.loads(buscar_visitante_por_cedula(req).content)

        self.assertTrue(data['encontrado'])
        self.assertEqual(data['nombre'], 'María')
        self.assertEqual(data['apellido'], 'López')
        self.assertEqual(data['tipo_documento'], 'CC')
        self.assertEqual(data['id_visitante'], 7)

    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_respuesta_es_instancia_de_json_response(self, mock_v):
        mock_v.filter.return_value.order_by.return_value.first.return_value = None
        req = _request(self.factory, 'GET', '/vigilante/api/buscar-visitante/', {'cedula': '1'})
        self.assertIsInstance(buscar_visitante_por_cedula(req), JsonResponse)

    @patch('apps.seguridad_administracion.vigilante.views.Visitante.objects')
    def test_cedula_con_espacios_es_limpiada_antes_de_buscar(self, mock_v):
        mock_v.filter.return_value.order_by.return_value.first.return_value = None

        req = _request(
            self.factory, 'GET', '/vigilante/api/buscar-visitante/', {'cedula': '  123  '}
        )
        buscar_visitante_por_cedula(req)

        # El filter debe haberse llamado con '123', no '  123  '
        call_kwargs = mock_v.filter.call_args[1]
        self.assertEqual(call_kwargs['cedula'], '123')

    @override_settings(LOGIN_URL='/login/')
    def test_anonimo_es_redirigido(self):
        req = _request(
            self.factory, 'GET', '/vigilante/api/buscar-visitante/',
            autenticado=False
        )
        resp = buscar_visitante_por_cedula(req)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)
