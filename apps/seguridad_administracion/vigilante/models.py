from django.db import models
from apps.login.models import Usuarios  # Importas Usuarios de login
from apps.reporte_monitoreo.coordinador.models import AsistenciaSede
import sys

# Create your models here.
class Area(models.Model):
    id_area = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    activo = models.IntegerField(default=1)

    class Meta:
        db_table = 'areas'
        managed = False

    def __str__(self):
        return self.nombre


class Visitante(models.Model):
    id_visitante = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    apellido = models.CharField(max_length=255, blank=True, null=True)
    tipo_documento = models.CharField(max_length=10, blank=True, null=True, default='CC')
    cedula = models.CharField(max_length=255, blank=True, null=True)
    motivo = models.CharField(max_length=255, blank=True, null=True)
    id_area = models.ForeignKey(Area, models.DO_NOTHING, db_column='id_area', blank=True, null=True)  # 👈 CAMBIADO
    id_asistencia_sede = models.ForeignKey(
        AsistenciaSede,
        on_delete=models.DO_NOTHING,
        db_column='id_asistencia_sede',
        null=False,
        blank=False,
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'visitante'
        managed = False

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    

class RegistroManual(models.Model):
    """
    Registros manuales de entrada/salida
    """
    id_registro_manual = models.BigAutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    id_asistencia_sede = models.ForeignKey(AsistenciaSede, models.DO_NOTHING, db_column='id_asistencia_sede', blank=True, null=True) 
    documento = models.CharField(max_length=255, blank=True, null=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    tipo_movimiento = models.CharField(max_length=255, blank=True, null=True)  # entrada/salida
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    motivo = models.CharField(max_length=255, blank=True, null=True)
    cedula = models.CharField(max_length=255, blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    nombres = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=255, blank=True, null=True)
    tipo_registro = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'registro_manual'
        managed = False
        
    def __str__(self):
        return f"{self.nombre or self.nombres} - {self.tipo_movimiento}"
    

