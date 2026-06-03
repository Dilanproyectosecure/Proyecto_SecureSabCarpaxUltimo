from django.db import models
from apps.login.models import Usuarios
import sys


# ==================== MODELOS DE FICHAS Y PROGRAMAS ====================

class Jornada(models.Model):
    id_jornada = models.AutoField(primary_key=True)
    nombre_jornada = models.CharField(max_length=50, blank=True, null=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        db_table = 'jornada'
        app_label = 'coordinador'
        managed = False

    def __str__(self):
        return self.nombre_jornada


class Coordinacion(models.Model):
    id_coordinacion = models.AutoField(primary_key=True)
    nombre_coordinacion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'coordinacion'
        managed = False

    def __str__(self):
        return self.nombre_coordinacion


class Programa(models.Model):
    id_programa = models.AutoField(primary_key=True)
    nombre_programa = models.CharField(max_length=255, blank=True, null=True)
    tipo_programa = models.CharField(max_length=255, blank=True, null=True)
    id_coordinacion = models.ForeignKey(
    Coordinacion,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    class Meta:
        db_table = 'programa'
        managed = False

    def __str__(self):
        return self.nombre_programa


class Ficha(models.Model):
    id_ficha = models.AutoField(primary_key=True)
    numero_ficha = models.CharField(max_length=50, blank=True, null=True)
    fecha = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)
    id_programa = models.ForeignKey(
    Programa,
    on_delete=models.DO_NOTHING,
    db_column='id_programa',
    null=True,
    blank=True
)
    id_jornada = models.ForeignKey(
    Jornada,
    on_delete=models.DO_NOTHING,
    db_column='id_jornada',
    null=True,
    blank=True
)

    class Meta:
        db_table = 'ficha'
        managed = False

    def __str__(self):
        return self.numero_ficha


class FichaInstructor(models.Model):
    id_ficha = models.ForeignKey(
    Ficha,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)
    id_instructor = models.ForeignKey(
    Usuarios,
    on_delete=models.CASCADE,
    db_column='id_instructor',
    null=True,
    blank=True
)

    class Meta:
        db_table = 'ficha_instructor'
        unique_together = (('id_ficha', 'id_instructor'),)
        managed = False


# ==================== MODELOS DE COMPETENCIAS ====================

class Competencia(models.Model):
    id_competencia = models.AutoField(primary_key=True)
    nombre_competencia = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    id_programa = models.ForeignKey(
    Programa,
    on_delete=models.CASCADE,
    db_column='id_programa',
    null=True,
    blank=True
)
    estado = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'competencia'
        managed = False

    def __str__(self):
        return self.nombre_competencia


class ProgramaCompetencia(models.Model):
    programa = models.ForeignKey(
    Programa,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)
    competencia = models.ForeignKey(
    Competencia,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    class Meta:
        db_table = 'programa_competencia'
        managed = False


class ResultadoAprendizaje(models.Model):
    id_resultado_aprendizaje = models.AutoField(db_column='id_Resultado_Aprendizaje', primary_key=True)
    resultado_aprendizaje = models.TextField(db_column='Resultado_Aprendizaje', blank=True, null=True)
    id_competencia = models.ForeignKey(
    Competencia,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    class Meta:
        db_table = 'resultado_aprendizaje'
        managed = False


# ==================== MODELOS DE ASISTENCIAS ====================

class AsistenciaAmbiente(models.Model):
    id_asistencia_ambiente = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
    Usuarios,
    on_delete=models.CASCADE,
    db_column='id_usuario',
    null=True,
    blank=True
)
    id_instructor = models.ForeignKey('login.Usuarios', on_delete=models.DO_NOTHING, db_column='id_instructor', related_name='asistencias_instructor', blank=True, null=True)
    id_competencia = models.ForeignKey(Competencia, on_delete=models.DO_NOTHING, db_column='id_competencia', blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    estado_asistencia = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'asistencia_ambiente'
        managed = False

    def __str__(self):
        return f"{self.fecha} - {self.id_usuario} - {self.estado_asistencia}"


class AsistenciaSede(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
    Usuarios,
    on_delete=models.CASCADE,
    db_column='id_usuario',
    null=True,
    blank=True
)
    fecha = models.DateField(blank=True, null=True)
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    estado_asistencia = models.CharField(max_length=255, blank=True, null=True)
    id_instructor = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'asistencia_sede'
        managed = False


class Justificacion(models.Model):
    id_justificacion = models.BigAutoField(primary_key=True)
    id_asistencia_ambiente = models.ForeignKey(
        AsistenciaAmbiente,
        on_delete=models.DO_NOTHING,
        db_column='id_asistencia_ambiente',
        blank=True,
        null=True
    )
    motivo = models.CharField(max_length=255, blank=True, null=True)
    soporte = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'justificacion'
        managed = False

    def __str__(self):
        return f"Justificación {self.id_justificacion} - {self.estado}"


class Novedad(models.Model):

    id_novedad = models.AutoField(
        primary_key=True,
        db_column='id_novedad'
    )

    id_coordinador = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_coordinador',
        null=True,
        blank=True,
        related_name='novedades_coordinador'
    )

    id_instructor = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='id_instructor',
        null=True,
        blank=True,
        related_name='novedades_instructor'
    )

    titulo = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    fecha = models.DateTimeField(
        blank=True,
        null=True
    )

    respuesta = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)

    id_ficha = models.ForeignKey(
        Ficha,
        models.DO_NOTHING,
        db_column='id_ficha',
        blank=True,
        null=True
    )

    archivo_adjunto = models.CharField(max_length=255, blank=True, null=True)
    respuesta_instructor = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'novedad'
        managed = False