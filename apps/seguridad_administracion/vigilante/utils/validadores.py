import re

def validar_nombre_apellido(texto, campo_nombre="Campo"):
    """
    Valida que un nombre o apellido contenga solo caracteres alfabéticos
    y tenga entre 3 y 40 caracteres.
    """
    if not texto or not isinstance(texto, str):
        return False, f"{campo_nombre} es requerido"
    
    texto = texto.strip()
    
    if len(texto) < 3:
        return False, f"{campo_nombre} debe tener mínimo 3 caracteres"
    
    if len(texto) > 40:
        return False, f"{campo_nombre} no puede exceder 40 caracteres"
    
    patron = r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$'
    if not re.match(patron, texto):
        return False, f"{campo_nombre} solo puede contener caracteres alfabéticos y espacios"
    
    return True, ""


def formatear_nombre(nombre):
    """Formatea un nombre (primera letra mayúscula, resto minúscula)"""
    return ' '.join([p.capitalize() for p in nombre.split()])