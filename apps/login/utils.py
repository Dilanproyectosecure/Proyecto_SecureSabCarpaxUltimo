import random
import string
from django.core.mail import send_mail
from django.conf import settings
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

def generar_codigo_recuperacion():
    """Genera un código aleatorio de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))


def generar_token_seguro(email):
    """Genera un token seguro basado en email y timestamp"""
    timestamp = str(int(time.time()))
    contenido = f"{email}_{timestamp}"
    token = hashlib.sha256(contenido.encode()).hexdigest()[:32]
    return token


def enviar_codigo_recuperacion(email, codigo):
    """Envía el código de recuperación por correo"""
    asunto = "SecureSab - Recuperación de contraseña"
    mensaje_texto = (
        "SecureSab - Recuperacion de contrasena\n\n"
        f"Tu codigo de verificacion es: {codigo}\n"
        "Este codigo expira en 10 minutos."
    )
    mensaje = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Recuperación de contraseña</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">SecureSab</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">Sistema de Control de Asistencia</p>
            </div>
            <div style="padding: 30px;">
                <h2 style="color: #333; margin-top: 0;">Recuperación de contraseña</h2>
                <p>Hemos recibido una solicitud para restablecer tu contraseña. Utiliza el siguiente código para continuar:</p>
                <div style="background: #f8f9fa; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #667eea;">{codigo}</span>
                </div>
                <p>Este código expirará en <strong>10 minutos</strong>.</p>
                <p>Si no solicitaste este cambio, ignora este mensaje.</p>
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    SecureSab - Sistema de Control de Asistencia SENA<br>
                    Este es un correo automático, por favor no responder.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            settings.EMAIL_HOST_USER,
            [email],
            html_message=mensaje,
            fail_silently=False
        )
        return True, None
    except Exception as e:
        logger.exception("Error al enviar correo de recuperación")
        return False, str(e)