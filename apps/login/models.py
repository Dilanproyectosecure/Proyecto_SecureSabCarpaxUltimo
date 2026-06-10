# apps/autenticacion/models.py

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UsuariosManager(BaseUserManager):
    """Manager personalizado para el modelo Usuarios"""
    
    def get_by_natural_key(self, cedula):
        return self.get(cedula=cedula)
    
    def create_user(self, cedula, password=None, **extra_fields):
        if not cedula:
            raise ValueError('La cédula es obligatoria')
        user = self.model(cedula=cedula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, cedula, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(cedula, password, **extra_fields)

class Usuarios(AbstractBaseUser):
    id_usuario = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(max_length=10, blank=True, null=True)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.CharField(max_length=255, blank=True, null=True)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    apellido = models.CharField(max_length=255, blank=True, null=True)
    id_ficha = models.ForeignKey('coordinador.Ficha', on_delete=models.DO_NOTHING, db_column='id_ficha', blank=True, null=True)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)
    foto_perfil = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # Agrégalo aunque no lo uses
    is_superuser = models.BooleanField(default=False)
    
    #last_login = None
    
    objects = UsuariosManager()

    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'correo']
    
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    
    class Meta:
        db_table = 'usuarios'
        managed = False


    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_rol(self):
        try:
            role_user = RoleUser.objects.get(id_usuario=self.id_usuario)
            return role_user.role.name
        except RoleUser.DoesNotExist:
            return None

class Roles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    guard_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'roles'
        unique_together = (('name', 'guard_name'),)
        managed = False

    def __str__(self):
        return self.name

class RoleUser(models.Model):
    id_usuario = models.OneToOneField(
        'Usuarios', 
        on_delete=models.DO_NOTHING, 
        db_column='id_usuario', 
        primary_key=True
    )
    role = models.ForeignKey(
    Roles,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    class Meta:
        db_table = 'role_user'
        managed = False

class Permissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    guard_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'permissions'
        unique_together = (('name', 'guard_name'),)
        managed = False