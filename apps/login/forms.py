from django import forms
from django.core.exceptions import ValidationError
from apps.login.models import Usuarios
import re

class RecuperarForm(forms.Form):
    """Formulario para ingresar el correo de recuperación"""
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@sena.edu.co'
        }),
        error_messages={
            'required': 'El correo electrónico es obligatorio',
            'invalid': 'Ingrese un correo electrónico válido'
        }
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            usuario = Usuarios.objects.get(correo=email)
            self.usuario = usuario
        except Usuarios.DoesNotExist:
            raise ValidationError('No existe una cuenta con este correo electrónico')
        return email


class ConfirmarCodigoForm(forms.Form):
    """Formulario para ingresar el código de verificación"""
    codigo = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'off'
        }),
        error_messages={
            'required': 'El código es obligatorio',
            'min_length': 'El código debe tener 6 dígitos',
            'max_length': 'El código debe tener 6 dígitos'
        }
    )


class NuevaPasswordForm(forms.Form):
    """Formulario para establecer nueva contraseña"""
    password = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nueva contraseña'
        }),
        error_messages={
            'required': 'La contraseña es obligatoria'
        }
    )
    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su nueva contraseña'
        }),
        error_messages={
            'required': 'Debe confirmar la contraseña'
        }
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Las contraseñas no coinciden')
        
        # Validar fortaleza de contraseña
        if password:
            if len(password) < 8:
                raise ValidationError('La contraseña debe tener al menos 8 caracteres')
            if not re.search(r'[A-Z]', password):
                raise ValidationError('La contraseña debe contener al menos una mayúscula')
            if not re.search(r'[0-9]', password):
                raise ValidationError('La contraseña debe contener al menos un número')
        
        return cleaned_data