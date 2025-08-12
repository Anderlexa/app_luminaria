# --- Configuración de Optimización de Rendimiento ---

# Configuración para velocidad vs precisión
CONFIG_VELOCIDAD = {
    'REDUCIR_IMAGEN': True,  # Reducir imagen si es muy grande
    'MAX_WIDTH': 800,        # Ancho máximo de imagen
    'MAX_HEIGHT': 600,       # Alto máximo de imagen
    'GENERAR_VISUALIZACION': True,  # Por defecto generar visualización
    'COMPRESION_JPEG': 80,   # Calidad de compresión JPEG (más rápida)
    'VENTANA_SUBPIXEL': (3, 3),  # Ventana más pequeña para subpíxel
    'ITERACIONES_SUBPIXEL': 15,   # Menos iteraciones
    'PRECISION_SUBPIXEL': 0.001,  # Menos precisa pero más rápida
    'POLYGONAL_ACCURACY': 0.03,   # Menos precisa pero más rápida
    'CORNER_REFINEMENT_WIN_SIZE': 3,  # Ventana más pequeña
    'CORNER_REFINEMENT_MAX_ITER': 10,  # Menos iteraciones
    'CORNER_REFINEMENT_MIN_ACCURACY': 0.02,  # Menos precisa
}

# Configuración para máxima precisión
CONFIG_PRECISION = {
    'REDUCIR_IMAGEN': False,  # No reducir imagen
    'MAX_WIDTH': 1920,       # Ancho máximo de imagen
    'MAX_HEIGHT': 1080,      # Alto máximo de imagen
    'GENERAR_VISUALIZACION': True,  # Generar visualización
    'COMPRESION_JPEG': 95,   # Calidad de compresión JPEG
    'VENTANA_SUBPIXEL': (5, 5),  # Ventana más grande para subpíxel
    'ITERACIONES_SUBPIXEL': 100,  # Más iteraciones
    'PRECISION_SUBPIXEL': 0.00001,  # Más precisa
    'POLYGONAL_ACCURACY': 0.02,   # Más precisa
    'CORNER_REFINEMENT_WIN_SIZE': 5,  # Ventana más grande
    'CORNER_REFINEMENT_MAX_ITER': 30,  # Más iteraciones
    'CORNER_REFINEMENT_MIN_ACCURACY': 0.01,  # Más precisa
}

# Configuración actual (por defecto velocidad)
CONFIG_ACTUAL = CONFIG_VELOCIDAD

def cambiar_configuracion(tipo):
    """
    Cambia la configuración entre velocidad y precisión.
    
    Args:
        tipo: 'velocidad' o 'precision'
    """
    global CONFIG_ACTUAL
    if tipo == 'velocidad':
        CONFIG_ACTUAL = CONFIG_VELOCIDAD
    elif tipo == 'precision':
        CONFIG_ACTUAL = CONFIG_PRECISION
    else:
        raise ValueError("Tipo debe ser 'velocidad' o 'precision'")

def obtener_configuracion():
    """
    Obtiene la configuración actual.
    
    Returns:
        dict: Configuración actual
    """
    return CONFIG_ACTUAL
