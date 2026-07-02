import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

logger = logging.getLogger('apps.email_service')


class EmailSendError(Exception):
    """Excepción personalizada para errores de envío de correo."""
    def __init__(self, mensaje, destinatarios_rechazados=None):
        self.mensaje = mensaje
        self.destinatarios_rechazados = destinatarios_rechazados or []
        super().__init__(self.mensaje)


def enviar_correo_seguro(asunto, destinatario, mensaje_texto, mensaje_html, cc=None):
    msg = MIMEMultipart('alternative')
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg['Reply-To'] = settings.EMAIL_HOST_USER
    msg['X-Mailer'] = 'SecureSab-System'

    if cc:
        msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc

    msg.attach(MIMEText(mensaje_texto, 'plain', 'utf-8'))
    msg.attach(MIMEText(mensaje_html, 'html', 'utf-8'))

    todos_destinos = [destinatario]
    if cc:
        if isinstance(cc, list):
            todos_destinos.extend(cc)
        else:
            todos_destinos.append(cc)

    server = None
    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.ehlo()
        if getattr(settings, 'EMAIL_USE_TLS', True):
            server.starttls()
            server.ehlo()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        refused = server.sendmail(settings.EMAIL_HOST_USER, todos_destinos, msg.as_string())

        if refused:
            rechazados = list(refused.keys())
            logger.error(
                f"Destinatarios rechazados por el servidor SMTP: {rechazados}. "
                f"Detalles: {refused}"
            )
            raise EmailSendError(
                f"El servidor SMTP rechazó destinatarios: {rechazados}",
                destinatarios_rechazados=rechazados
            )

        logger.info(f"Correo enviado a {destinatario}" + (f" (CC: {cc})" if cc else ""))
        return True

    except EmailSendError:
        raise
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error de autenticación SMTP para {destinatario}: {e}")
        raise EmailSendError(f"Error de autenticación SMTP: {e}")
    except smtplib.SMTPConnectError as e:
        logger.error(f"Error de conexión SMTP para {destinatario}: {e}")
        raise EmailSendError(f"Error de conexión SMTP: {e}")
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP enviando correo a {destinatario}: {e}")
        raise EmailSendError(f"Error SMTP: {e}")
    except Exception as e:
        logger.exception(f"Error inesperado enviando correo a {destinatario}")
        raise EmailSendError(f"Error inesperado: {e}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
