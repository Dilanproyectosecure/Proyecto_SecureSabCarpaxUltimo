from django.db import models
from apps.login.models import Usuarios
# Some legacy models exist in the DB and are referenced by older migrations.
# We declare lightweight unmanaged stubs here to avoid Django generating
# destructive DeleteModel migrations when those models are now defined in
# their original apps (e.g. apps.login, apps.reporte_monitoreo).


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'usuarios'
        managed = False


class Role(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'roles'
        managed = False


class RoleUser(models.Model):
    id_usuario = models.IntegerField()
    role_id = models.BigIntegerField()

    class Meta:
        db_table = 'role_user'
        managed = False


class Ficha(models.Model):
    id_ficha = models.AutoField(primary_key=True)
    numero_ficha = models.CharField(max_length=50)

    class Meta:
        db_table = 'ficha'
        managed = False


class AsistenciaSede(models.Model):
    id_asistencia = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'asistencia_sede'
        managed = False


class AsistenciaAmbiente(models.Model):
    id_asistencia_ambiente = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'asistencia_ambiente'
        managed = False
from django.contrib.auth.models import User

# Create your models here.
# NOTE: AsistenciaSede, AsistenciaAmbiente, Ficha are imported from coordinador app
# to avoid duplication. gestorsistema only adds Huella, registro_actividad, HistorialFallos


class Huella(models.Model):
    id_huella = models.AutoField(primary_key=True, db_column='id_huella')
    usuario = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='huellas'
    )
    datos_huella_dactilar = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    tiene_huella = models.BooleanField(default=True)

    class Meta:
        db_table = 'huella'
        managed = False
        
    def __str__(self):
        return f"Huella - {self.usuario.nombre} ({self.fecha_registro})"



class registro_actividad(models.Model):
    id_registro_actividad = models.AutoField(primary_key=True)

    id_usuario = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='usuario_id',
        null=True,
        blank=True
    )

    actividad = models.CharField(max_length=255)

    fecha = models.DateField(auto_now_add=True)

    hora = models.TimeField(
        null=True,
        blank=True
    )

    tipo_accion = models.CharField(max_length=50)

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'registro_actividad'
        managed = False
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"{self.actividad}"

class HistorialFallos(models.Model):
    TIPO_FALLOS = [
        ('HUELLA_FALLIDA', 'Huella no coincide'),
        ('SIN_HUELLA', 'Usuario sin huella registrada'),
        ('LECTOR_ERROR', 'Error en el lector biométrico'),
        ('TIMEOUT', 'Tiempo excedido'),
        ('USUARIO_NO_EXISTE', 'Usuario no registrado en el sistema'),
    ]

    id_fallo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, null=True, blank=True)
    tipo_fallo = models.CharField(max_length=50, choices=TIPO_FALLOS)
    cedula_intentada = models.CharField(max_length=191, null=True, blank=True)
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    detalles = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'historial_fallos'
        managed = False
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"{self.fecha} {self.hora} - {self.get_tipo_fallo_display()} - {self.cedula_intentada or 'N/A'}"