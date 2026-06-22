import logging
from apps.email_service import enviar_correo_seguro

logger = logging.getLogger(__name__)


def _construir_html_inasistencia(aprendiz, ficha, fecha, competencia):
    nombre_completo = f"{aprendiz.nombre} {aprendiz.apellido}"
    numero_ficha = ficha.numero_ficha if ficha else "N/D"
    nombre_competencia = competencia.nombre_competencia if competencia else "N/D"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:20px;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;text-align:center;">
                            <h1 style="color:#ffffff;margin:0;font-size:24px;">SecureSab</h1>
                            <p style="color:#e0e0ff;margin:5px 0 0;font-size:14px;">Sistema de Control de Asistencia SENA</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;">
                            <h2 style="color:#333;margin-top:0;">Notificacion de Inasistencia</h2>
                            <p style="color:#555;font-size:16px;">Estimado/a <strong>{nombre_completo}</strong>,</p>
                            <p style="color:#555;font-size:15px;">
                                Le informamos que su asistencia no fue registrada en el sistema. A continuacion los detalles:
                            </p>
                            <table width="100%" cellpadding="10" cellspacing="0" style="background:#f8f9fa;border-radius:6px;margin:15px 0;">
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Fecha:</td>
                                    <td style="color:#333;">{fecha}</td>
                                </tr>
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Ficha:</td>
                                    <td style="color:#333;">{numero_ficha}</td>
                                </tr>
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Competencia:</td>
                                    <td style="color:#333;">{nombre_competencia}</td>
                                </tr>
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Estado:</td>
                                    <td style="color:#c0392b;font-weight:bold;">Inasistio</td>
                                </tr>
                            </table>
                            <p style="color:#555;font-size:15px;">
                                Si cuenta con un justificativo, por favor radicarlo a traves del sistema o contactar a su instructor.
                            </p>
                            <p style="color:#888;font-size:12px;margin-top:30px;border-top:1px solid #eee;padding-top:15px;">
                                SecureSab - Sistema de Control de Asistencia SENA<br>
                                Este es un correo automatico, por favor no responder.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """
    return html


def enviar_correos_inasistencia(aprendices_inasistentes, ficha, fecha, competencia):
    enviados = 0
    fallidos = 0
    sin_correo = 0
    detalles = []

    for aprendiz in aprendices_inasistentes:
        if not aprendiz.correo:
            sin_correo += 1
            detalles.append({
                'id': aprendiz.id_usuario,
                'nombre': f"{aprendiz.nombre} {aprendiz.apellido}",
                'correo': None,
                'estado': 'sin_correo'
            })
            continue

        nombre_completo = f"{aprendiz.nombre} {aprendiz.apellido}"
        asunto = f"SecureSab - Notificacion de inasistencia - {fecha}"
        texto_plano = (
            f"Hola {nombre_completo},\n\n"
            f"Se registro su inasistencia el {fecha} en la ficha {ficha.numero_ficha} "
            f"para la competencia {competencia.nombre_competencia if competencia else 'N/D'}.\n\n"
            f"Si cuenta con un justificativo, por favor radicarlo a traves del sistema.\n\n"
            f"SecureSab - Sistema de Control de Asistencia SENA"
        )
        html = _construir_html_inasistencia(aprendiz, ficha, fecha, competencia)

        resultado = enviar_correo_seguro(asunto, aprendiz.correo, texto_plano, html)

        if resultado:
            enviados += 1
            detalles.append({
                'id': aprendiz.id_usuario,
                'nombre': nombre_completo,
                'correo': aprendiz.correo,
                'estado': 'enviado'
            })
        else:
            fallidos += 1
            detalles.append({
                'id': aprendiz.id_usuario,
                'nombre': nombre_completo,
                'correo': aprendiz.correo,
                'estado': 'fallido'
            })

    return {
        'enviados': enviados,
        'fallidos': fallidos,
        'sin_correo': sin_correo,
        'total': len(aprendices_inasistentes),
        'detalles': detalles
    }


def enviar_correo_retardo(aprendiz, retardos_consecutivos, ficha, fecha):
    if not aprendiz.correo:
        return False

    nombre_completo = f"{aprendiz.nombre} {aprendiz.apellido}"
    asunto = f"SecureSab - Aviso de retardo consecutivo ({retardos_consecutivos} retardos)"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:20px;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#e67e22,#d35400);padding:30px;text-align:center;">
                            <h1 style="color:#ffffff;margin:0;font-size:24px;">SecureSab</h1>
                            <p style="color:#fdebd0;margin:5px 0 0;font-size:14px;">Aviso de Retardo Consecutivo</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;">
                            <h2 style="color:#333;margin-top:0;">Aviso Importante</h2>
                            <p style="color:#555;font-size:16px;">Estimado/a <strong>{nombre_completo}</strong>,</p>
                            <p style="color:#555;font-size:15px;">
                                Se ha registrado su <strong>retardo consecutivo numero {retardos_consecutivos}</strong>.
                                Segun el reglamento del aprendiz, con <strong>3 retardos consecutivos</strong> se procede con un llamado de atencion.
                            </p>
                            <table width="100%" cellpadding="10" cellspacing="0" style="background:#fdf2e9;border-radius:6px;margin:15px 0;border-left:4px solid #e67e22;">
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Retardos consecutivos:</td>
                                    <td style="color:#e67e22;font-weight:bold;">{retardos_consecutivos}</td>
                                </tr>
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Ficha:</td>
                                    <td style="color:#333;">{ficha.numero_ficha if ficha else 'N/D'}</td>
                                </tr>
                                <tr>
                                    <td style="color:#555;font-weight:bold;">Fecha:</td>
                                    <td style="color:#333;">{fecha}</td>
                                </tr>
                            </table>
                            <p style="color:#555;font-size:15px;">
                                Le recomendamos puntualidad en sus proximas sesiones de formacion.
                            </p>
                            <p style="color:#888;font-size:12px;margin-top:30px;border-top:1px solid #eee;padding-top:15px;">
                                SecureSab - Sistema de Control de Asistencia SENA<br>
                                Este es un correo automatico, por favor no responder.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    texto_plano = (
        f"Hola {nombre_completo},\n\n"
        f"Se ha registrado su retardo consecutivo numero {retardos_consecutivos}.\n"
        f"Segun el reglamento, con 3 retardos consecutivos se procede con un llamado de atencion.\n\n"
        f"SecureSab - Sistema de Control de Asistencia SENA"
    )

    return enviar_correo_seguro(asunto, aprendiz.correo, texto_plano, html)
