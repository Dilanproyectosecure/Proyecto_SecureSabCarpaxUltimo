from datetime import date

def calcular_dias_entre(fecha_inicio, fecha_fin=None):
    """
    Retorna la diferencia en días entre dos fechas
    """
    if fecha_fin is None:
        fecha_fin = date.today()

    return (fecha_fin - fecha_inicio).days