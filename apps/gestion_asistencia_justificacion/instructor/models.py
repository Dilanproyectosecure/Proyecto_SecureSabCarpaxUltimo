from django.db import models
from apps.login.models import Usuarios


class LlamadoAtencion(models.Model):
    NIVEL_CHOICES = [
        (1, 'Primer llamado de atención'),
        (2, 'Segundo llamado de atención'),
        (3, 'Tercer llamado - Proceso de deserción'),
    ]

    id_llamado = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        Usuarios, on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='llamados_recibidos'
    )
    id_instructor = models.ForeignKey(
        Usuarios, on_delete=models.CASCADE,
        db_column='id_instructor',
        related_name='llamados_emitidos'
    )
    nivel = models.IntegerField(choices=NIVEL_CHOICES)
    total_inasistencias = models.IntegerField()
    notificado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_notificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'llamado_atencion'
        verbose_name = 'Llamado de atención'
        verbose_name_plural = 'Llamados de atención'

    def __str__(self):
        return f'{self.id_usuario} - Nivel {self.nivel}'
