import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

logger = logging.getLogger(__name__)


def enviar_correo_seguro(asunto, destinatario, mensaje_texto, mensaje_html):
    msg = MIMEMultipart('alternative')
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg['Reply-To'] = settings.EMAIL_HOST_USER
    msg['X-Mailer'] = 'SecureSab-System'

    msg.attach(MIMEText(mensaje_texto, 'plain', 'utf-8'))
    msg.attach(MIMEText(mensaje_html, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.EMAIL_HOST_USER, destinatario, msg.as_string())
        server.quit()
        logger.info(f"Correo enviado a {destinatario}: {asunto}")
        return True
    except Exception as e:
        logger.exception(f"Error al enviar correo a {destinatario}")
        return False
