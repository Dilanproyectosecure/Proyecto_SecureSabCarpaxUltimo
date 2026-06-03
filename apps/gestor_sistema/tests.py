from django.test import TestCase, Client
from django.urls import reverse
from django.shortcuts import get_object_or_404
from apps.login.models import Usuarios # Asegúrate de importar tu modelo real

class TestGestionUsuarios(TestCase):
    def setUp(self):
        # Creamos el usuario que vamos a desactivar primero
        self.usuario = Usuarios.objects.create(
            nombre='Juan', 
            apellido='Perez', 
            estado='Inactivo'
        )
        # Creamos un usuario administrador para poder loguearnos
        self.admin = Usuarios.objects.create_user(username='admin')
        self.client = Client()
        self.client.force_login(self.admin)

    def test_activar_usuario_exitoso(self):
        """Verifica que la vista cambia el estado a 'Activo'"""
        # Suponiendo que tu URL se llama 'gestor_sistema:activar_usuario'
        url = reverse('gestor_sistema:activar_usuario', args=[self.usuario.id_usuario])
        
        response = self.client.post(url)
        
        # Recargamos el usuario desde la BD para ver los cambios
        self.usuario.refresh_from_db()
        
        # 1. Verificamos que el estado cambió
        self.assertEqual(self.usuario.estado, 'Activo')
        
        # 2. Verificamos la redirección
        self.assertRedirects(response, reverse('gestor_sistema:panel_admin'))

    def test_activar_usuario_404(self):
        """Verifica que responde 404 si el ID no existe"""
        url = reverse('gestor_sistema:activar_usuario', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)