# apps/login/urls.py

from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),


    # Rutas de recuperación de contraseña
    path('recuperar/', views.recuperar, name='recuperar'),
    path('recuperar/confirmar/<str:email>/', views.recuperar_confirmar, name='recuperar_confirmar'),
    path('recuperar/reenviar/<str:email>/', views.reenviar_codigo, name='reenviar_codigo'),
    path('recuperar/nueva-pass/<str:token>/', views.recuperar_nueva_pass, name='recuperar_nueva_pass'),
]