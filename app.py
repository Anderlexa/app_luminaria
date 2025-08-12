# --- Importaciones necesarias ---
from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from calcular_luminarias import calcular_y_generar_imagen
from config_optimizacion import obtener_configuracion, cambiar_configuracion
import os
import cv2
import numpy as np
import base64
from PIL import Image
import io
from collections import deque
import time
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo para servidor
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Inicialización de la app Flask ---
app = Flask(__name__)
CORS(app)  # Permite peticiones desde otros orígenes

# --- Variables globales para filtrado temporal ---
mediciones_previas = deque(maxlen=10)  # Almacena las últimas 10 mediciones
ultima_medicion_tiempo = 0

# --- Funciones mejoradas para detección precisa ---

def detectar_esquinas_subpixel(imagen, corners, ventana=None, zona_muerta=(-1, -1)):
    """
    Refina las esquinas detectadas con precisión subpíxel (optimizada para velocidad).
    
    Args:
        imagen: Imagen en escala de grises
        corners: Esquinas detectadas por ArUco
        ventana: Tamaño de la ventana de búsqueda
        zona_muerta: Zona muerta para el refinamiento
    
    Returns:
        corners_refinadas: Esquinas con precisión subpíxel
    """
    config = obtener_configuracion()
    if ventana is None:
        ventana = config['VENTANA_SUBPIXEL']
    
    corners_refinadas = []
    
    for marker_corners in corners:
        # Convertir a formato float32 para subpíxel
        corners_float = np.float32(marker_corners)
        
        # Una sola iteración para mayor velocidad
        corners_refinadas_marker = cv2.cornerSubPix(
            imagen, 
            corners_float, 
            ventana, 
            zona_muerta,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 
                     config['ITERACIONES_SUBPIXEL'], 
                     config['PRECISION_SUBPIXEL'])
        )
        
        corners_refinadas.append(corners_refinadas_marker)
    
    return corners_refinadas

def calcular_distancia_multipunto(corners1, corners2, metros_por_pixel):
    """
    Calcula la distancia usando múltiples puntos de referencia para mayor precisión.
    
    Args:
        corners1: Esquinas del primer marcador ArUco
        corners2: Esquinas del segundo marcador ArUco
        metros_por_pixel: Factor de conversión
    
    Returns:
        distancia_promedio: Distancia promedio calculada
        puntos_medicion: Puntos utilizados para la medición
    """
    # Calcular centro de masa de cada marcador
    centro1 = np.mean(corners1, axis=0)
    centro2 = np.mean(corners2, axis=0)
    
    # Calcular distancia entre centros
    distancia_centros = np.linalg.norm(centro2 - centro1)
    
    # Calcular distancias desde múltiples esquinas
    distancias_esquinas = []
    puntos_medicion = []
    
    # Vector dirección entre centros
    direccion = centro2 - centro1
    direccion_normalizada = direccion / np.linalg.norm(direccion)
    
    # Para cada esquina del primer marcador, encontrar la esquina más cercana del segundo
    for i, esquina1 in enumerate(corners1):
        # Encontrar la esquina del segundo marcador más alejada en la dirección opuesta
        distancias_proyeccion = []
        for esquina2 in corners2:
            # Proyección de la línea entre esquinas en la dirección de los centros
            vector_esquinas = esquina2 - esquina1
            proyeccion = np.dot(vector_esquinas, direccion_normalizada)
            distancias_proyeccion.append(proyeccion)
        
        # Usar la esquina con mayor proyección (más alejada)
        idx_max = np.argmax(distancias_proyeccion)
        esquina2_seleccionada = corners2[idx_max]
        
        # Calcular distancia entre estas esquinas
        distancia_esquinas = np.linalg.norm(esquina2_seleccionada - esquina1)
        distancias_esquinas.append(distancia_esquinas)
        puntos_medicion.append((esquina1, esquina2_seleccionada))
    
    # Calcular distancia promedio ponderada con pesos mejorados
    distancias_esquinas = np.array(distancias_esquinas)
    
    # Usar pesos basados en la estabilidad y consistencia
    # Dar más peso a las mediciones que están más cerca de la mediana
    mediana = np.median(distancias_esquinas)
    desviaciones = np.abs(distancias_esquinas - mediana)
    
    # Pesos inversamente proporcionales a la desviación, con suavizado
    pesos = 1.0 / (1.0 + desviaciones / (mediana * 0.1))  # Factor de suavizado
    pesos = pesos / np.sum(pesos)
    
    distancia_promedio_px = np.sum(distancias_esquinas * pesos)
    distancia_promedio_metros = distancia_promedio_px * metros_por_pixel
    
    return distancia_promedio_metros, puntos_medicion, distancia_centros * metros_por_pixel

def calcular_distancia_con_correccion_perspectiva(corners1, corners2, metros_por_pixel, imagen_shape):
    """
    Calcula la distancia con corrección de perspectiva para mayor precisión.
    
    Args:
        corners1: Esquinas del primer marcador ArUco
        corners2: Esquinas del segundo marcador ArUco
        metros_por_pixel: Factor de conversión
        imagen_shape: Forma de la imagen (altura, ancho)
    
    Returns:
        distancia_corregida: Distancia corregida por perspectiva
    """
    # Calcular centro de cada marcador
    centro1 = np.mean(corners1, axis=0)
    centro2 = np.mean(corners2, axis=0)
    
    # Calcular distancia básica
    distancia_basica = np.linalg.norm(centro2 - centro1)
    
    # Corrección de perspectiva basada en la posición en la imagen
    # Los objetos más cerca del centro de la imagen tienen menos distorsión
    centro_imagen = np.array([imagen_shape[1] / 2, imagen_shape[0] / 2])
    
    # Calcular factor de corrección basado en la distancia al centro
    distancia_al_centro1 = np.linalg.norm(centro1 - centro_imagen)
    distancia_al_centro2 = np.linalg.norm(centro2 - centro_imagen)
    
    # Factor de corrección (mayor para objetos más alejados del centro)
    factor_correccion1 = 1.0 + (distancia_al_centro1 / (imagen_shape[0] + imagen_shape[1])) * 0.1
    factor_correccion2 = 1.0 + (distancia_al_centro2 / (imagen_shape[0] + imagen_shape[1])) * 0.1
    
    # Factor de corrección promedio
    factor_correccion = (factor_correccion1 + factor_correccion2) / 2
    
    # Aplicar corrección
    distancia_corregida = distancia_basica / factor_correccion
    
    return distancia_corregida * metros_por_pixel

def calcular_escala_precisa(corners, tamano_real_lado):
    """
    Calcula la escala precisa usando múltiples mediciones del marcador.
    
    Args:
        corners: Esquinas del marcador ArUco
        tamano_real_lado: Tamaño real del lado en metros
    
    Returns:
        metros_por_pixel: Factor de conversión
        lado_px: Tamaño del lado en píxeles
    """
    # Calcular los lados del marcador usando las esquinas
    lados = []
    
    # Lado 1: esquina 0 a esquina 1
    lado1 = np.linalg.norm(corners[1] - corners[0])
    lados.append(lado1)
    
    # Lado 2: esquina 1 a esquina 2
    lado2 = np.linalg.norm(corners[2] - corners[1])
    lados.append(lado2)
    
    # Lado 3: esquina 2 a esquina 3
    lado3 = np.linalg.norm(corners[3] - corners[2])
    lados.append(lado3)
    
    # Lado 4: esquina 3 a esquina 0
    lado4 = np.linalg.norm(corners[0] - corners[3])
    lados.append(lado4)
    
    # Filtrar outliers usando MAD (Median Absolute Deviation)
    lados = np.array(lados)
    mediana = np.median(lados)
    mad = np.median(np.abs(lados - mediana))
    umbral_outlier = 2.0 * mad
    
    # Usar solo lados que no sean outliers
    lados_validos = lados[np.abs(lados - mediana) <= umbral_outlier]
    
    if len(lados_validos) == 0:
        # Si todos son outliers, usar la mediana
        lado_px = mediana
    else:
        # Usar promedio de lados válidos
        lado_px = np.mean(lados_validos)
    
    # Calcular factor de conversión
    metros_por_pixel = tamano_real_lado / lado_px
    
    return metros_por_pixel, lado_px

def filtrar_mediciones_temporales(nueva_medicion, ventana_tiempo=2.0):
    """
    Filtra outliers y promedia mediciones temporales con algoritmo mejorado.
    
    Args:
        nueva_medicion: Nueva medición a agregar
        ventana_tiempo: Ventana de tiempo en segundos para considerar mediciones válidas
    
    Returns:
        medicion_filtrada: Medición filtrada y promediada
        confianza: Nivel de confianza de la medición
    """
    global mediciones_previas, ultima_medicion_tiempo
    
    tiempo_actual = time.time()
    
    # Limpiar mediciones muy antiguas
    while mediciones_previas and (tiempo_actual - mediciones_previas[0]['tiempo']) > ventana_tiempo:
        mediciones_previas.popleft()
    
    # Agregar nueva medición
    mediciones_previas.append({
        'distancia': nueva_medicion,
        'tiempo': tiempo_actual
    })
    
    if len(mediciones_previas) < 3:
        # Si hay pocas mediciones, usar la más reciente
        return nueva_medicion, 0.5
    
    # Extraer distancias y tiempos
    distancias = [m['distancia'] for m in mediciones_previas]
    tiempos = [m['tiempo'] for m in mediciones_previas]
    
    # Calcular estadísticas robustas
    mediana = np.median(distancias)
    mad = np.median(np.abs(distancias - mediana))  # Median Absolute Deviation
    
    # Usar MAD para detectar outliers (más robusto que desviación estándar)
    umbral_outlier = 2.5 * mad
    distancias_filtradas = [d for d in distancias if abs(d - mediana) <= umbral_outlier]
    
    if len(distancias_filtradas) == 0:
        # Si todas son outliers, usar la mediana
        medicion_filtrada = mediana
        confianza = 0.3
    else:
        # Usar promedio ponderado por tiempo (mediciones más recientes tienen más peso)
        pesos_tiempo = []
        for t in tiempos:
            # Peso basado en qué tan reciente es la medición
            tiempo_relativo = tiempo_actual - t
            peso = np.exp(-tiempo_relativo / ventana_tiempo)  # Decaimiento exponencial
            pesos_tiempo.append(peso)
        
        # Normalizar pesos
        pesos_tiempo = np.array(pesos_tiempo)
        pesos_tiempo = pesos_tiempo / np.sum(pesos_tiempo)
        
        # Calcular promedio ponderado
        medicion_filtrada = np.sum(np.array(distancias) * pesos_tiempo)
        
        # Calcular confianza basada en consistencia y número de mediciones
        desviacion_filtrada = np.std(distancias_filtradas)
        consistencia = 1.0 - (desviacion_filtrada / mediana) if mediana > 0 else 0.5
        factor_muestras = min(1.0, len(distancias_filtradas) / 5.0)  # Más muestras = mayor confianza
        
        confianza = consistencia * factor_muestras
        confianza = max(0.1, min(1.0, confianza))
    
    return medicion_filtrada, confianza

def mejorar_deteccion_aruco(imagen):
    """
    Mejora la detección de ArUco con múltiples técnicas (optimizada para velocidad).
    
    Args:
        imagen: Imagen de entrada
    
    Returns:
        corners_mejoradas: Esquinas detectadas mejoradas
        ids: IDs de los marcadores
    """
    # Convertir a escala de grises
    if len(imagen.shape) == 3:
        gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    else:
        gray = imagen.copy()
    
    # Reducir tamaño de imagen para mayor velocidad (si es muy grande)
    config = obtener_configuracion()
    if config['REDUCIR_IMAGEN']:
        height, width = gray.shape
        if width > config['MAX_WIDTH'] or height > config['MAX_HEIGHT']:
            scale_factor = min(config['MAX_WIDTH']/width, config['MAX_HEIGHT']/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height))
    
    # Aplicar filtros para mejorar la detección (optimizados)
    # Filtro Gaussiano más pequeño para mayor velocidad
    gray_suavizada = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Configurar detector ArUco con parámetros optimizados para velocidad
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aruco_params = cv2.aruco.DetectorParameters()
    
    # Parámetros optimizados para velocidad y precisión balanceada
    config = obtener_configuracion()
    aruco_params.adaptiveThreshWinSizeMin = 3
    aruco_params.adaptiveThreshWinSizeMax = 23
    aruco_params.adaptiveThreshWinSizeStep = 10
    aruco_params.adaptiveThreshConstant = 7
    aruco_params.minMarkerPerimeterRate = 0.03
    aruco_params.maxMarkerPerimeterRate = 4.0
    aruco_params.polygonalApproxAccuracyRate = config['POLYGONAL_ACCURACY']
    aruco_params.minCornerDistanceRate = 0.05
    aruco_params.minDistanceToBorder = 3
    aruco_params.minOtsuStdDev = 5.0
    aruco_params.perspectiveRemovePixelPerCell = 4
    aruco_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
    aruco_params.maxErroneousBitsInBorderRate = 0.35
    
    # Configurar refinamiento de esquinas (reducido para velocidad)
    if hasattr(aruco_params, 'cornerRefinementMethod'):
        aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    if hasattr(aruco_params, 'cornerRefinementWinSize'):
        aruco_params.cornerRefinementWinSize = config['CORNER_REFINEMENT_WIN_SIZE']
    if hasattr(aruco_params, 'cornerRefinementMaxIterations'):
        aruco_params.cornerRefinementMaxIterations = config['CORNER_REFINEMENT_MAX_ITER']
    if hasattr(aruco_params, 'cornerRefinementMinAccuracy'):
        aruco_params.cornerRefinementMinAccuracy = config['CORNER_REFINEMENT_MIN_ACCURACY']
    
    # Detectar ArUco
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    corners, ids, rejected = detector.detectMarkers(gray_suavizada)
    
    if ids is None or len(ids) < 2:
        # Intentar con imagen original si falla
        corners, ids, rejected = detector.detectMarkers(gray)
    
    if ids is None or len(ids) < 2:
        return None, None
    
    # Refinar esquinas con precisión subpíxel (solo si es necesario)
    corners_refinadas = detectar_esquinas_subpixel(gray, corners)
    
    return corners_refinadas, ids

# --- Rutas de la app web ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/configuracion", methods=["POST"])
def cambiar_configuracion_route():
    """
    Ruta para cambiar la configuración de optimización.
    """
    try:
        data = request.get_json()
        tipo = data.get('tipo', 'velocidad')  # 'velocidad' o 'precision'
        
        cambiar_configuracion(tipo)
        config_actual = obtener_configuracion()
        
        return jsonify({
            "success": True,
            "mensaje": f"Configuración cambiada a: {tipo}",
            "configuracion": config_actual
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# --- Ruta para calcular luminarias ---
@app.route("/generar")
def generar():
    # Recibe distancia, calcula luminarias y devuelve resultados
    try:
        distancia = float(request.args.get("distancia", 0))
        if distancia <= 0:
            return jsonify({"error": "La distancia debe ser mayor que 0."})
        resultado = calcular_y_generar_imagen(distancia)
        return jsonify({
            "area": resultado["area"],
            "nl": resultado["nl"],
            "x": resultado["x"],
            "y": resultado["y"],
            "total": resultado["total"],
            "image_url": url_for("static", filename=os.path.basename(resultado["image_path"]))
        })
    except Exception as e:
        return jsonify({"error": str(e)})

def calcular_distancia_entre_bordes(corners1, corners2, metros_por_pixel):
    """
    Calcula la distancia entre los bordes externos de dos marcadores ArUco.
    Usa el punto más cercano entre los bordes externos para mayor precisión.
    """
    # Obtener los bordes externos de cada marcador
    # Para cada marcador, los bordes externos son los puntos más alejados
    # en la dirección de la línea que conecta los centros
    
    # Calcular centros de los marcadores
    center1 = np.mean(corners1, axis=0)
    center2 = np.mean(corners2, axis=0)
    
    # Vector dirección entre centros
    direction = center2 - center1
    direction_normalized = direction / np.linalg.norm(direction)
    
    # Encontrar los puntos más externos en cada marcador
    # en la dirección del otro marcador
    
    # Para el primer marcador: punto más alejado en dirección al segundo
    distances1 = [np.dot(corner - center1, direction_normalized) for corner in corners1]
    edge1_idx = np.argmax(distances1)
    edge1 = corners1[edge1_idx]
    
    # Para el segundo marcador: punto más alejado en dirección al primero
    distances2 = [np.dot(corner - center2, -direction_normalized) for corner in corners2]
    edge2_idx = np.argmax(distances2)
    edge2 = corners2[edge2_idx]
    
    # Calcular distancia entre bordes externos
    distancia_bordes_px = np.linalg.norm(edge2 - edge1)
    distancia_bordes_metros = distancia_bordes_px * metros_por_pixel
    
    return distancia_bordes_metros, edge1, edge2

def calcular_escala_precisa(corners, tamano_real_lado):
    """
    Calcula la escala de manera más precisa usando múltiples mediciones
    y eliminando outliers.
    """
    # Calcular todos los lados del marcador
    lados = []
    for i in range(4):
        lado = np.linalg.norm(corners[i] - corners[(i + 1) % 4])
        lados.append(lado)
    
    # Calcular estadísticas para detectar outliers
    lados = np.array(lados)
    mean_lado = np.mean(lados)
    std_lado = np.std(lados)
    
    # Filtrar outliers (valores que se desvían más de 2 desviaciones estándar)
    lados_filtrados = lados[np.abs(lados - mean_lado) <= 2 * std_lado]
    
    if len(lados_filtrados) == 0:
        # Si todos son outliers, usar el promedio
        lado_px = mean_lado
    else:
        # Usar el promedio de los lados no-outliers
        lado_px = np.mean(lados_filtrados)
    
    metros_por_pixel = tamano_real_lado / lado_px
    return metros_por_pixel, lado_px

def generar_visualizacion_medicion_optimizada(imagen_original, corners1, corners2, puntos_visualizacion, 
                                             distancia_final, metodo_usado, confianza, debug_info):
    """
    Genera una visualización ultra-rápida mostrando solo la distancia entre ArUcos.
    """
    # Crear una copia de la imagen para dibujar
    imagen_visualizacion = imagen_original.copy()
    
    # Colores para los marcadores
    color_rojo = (0, 0, 255)  # BGR
    color_azul = (255, 0, 0)  # BGR
    color_verde = (0, 255, 0)  # BGR
    color_naranja = (0, 165, 255)  # BGR
    color_purpura = (128, 0, 128)  # BGR
    
    # Dibujar marcadores (solo contornos)
    for i, corners in enumerate([corners1, corners2]):
        color = color_rojo if i == 0 else color_azul
        corners_int = corners.astype(np.int32)
        cv2.polylines(imagen_visualizacion, [corners_int], True, color, 2)
    
    # Dibujar línea de medición usando los puntos exactos calculados
    if metodo_usado == 'bordes_externos' and puntos_visualizacion:
        # Usar los bordes externos exactos calculados
        edge1, edge2 = puntos_visualizacion
        cv2.line(imagen_visualizacion, 
                 (int(edge1[0]), int(edge1[1])), 
                 (int(edge2[0]), int(edge2[1])), 
                 color_purpura, 3)
    
    elif metodo_usado in ['multipunto', 'filtrado_temporal'] and puntos_visualizacion:
        # Dibujar todas las líneas multipunto
        for punto1, punto2 in puntos_visualizacion:
            cv2.line(imagen_visualizacion, 
                     (int(punto1[0]), int(punto1[1])), 
                     (int(punto2[0]), int(punto2[1])), 
                     color_naranja, 2)
    
    elif puntos_visualizacion:
        # Para otros métodos, usar los puntos calculados
        for punto1, punto2 in puntos_visualizacion:
            cv2.line(imagen_visualizacion, 
                     (int(punto1[0]), int(punto1[1])), 
                     (int(punto2[0]), int(punto2[1])), 
                     color_verde, 3)
    
    # Convertir a base64 con compresión máxima para velocidad
    _, buffer = cv2.imencode('.jpg', imagen_visualizacion, 
                           [cv2.IMWRITE_JPEG_QUALITY, 70])  # Compresión máxima
    imagen_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return imagen_base64

def generar_visualizacion_medicion(imagen_original, corners1, corners2, puntos_visualizacion, 
                                   distancia_final, metodo_usado, confianza, debug_info):
    """
    Wrapper para la visualización optimizada.
    """
    return generar_visualizacion_medicion_optimizada(
        imagen_original, corners1, corners2, puntos_visualizacion,
        distancia_final, metodo_usado, confianza, debug_info
    )

# --- Ruta para procesar imagen y detectar ArUco con precisión mejorada ---
@app.route("/detectar_aruco", methods=["POST"])
def detectar_aruco():
    try:
        # Recibe imagen y tamaño del lado del ArUco (en metros)
        data = request.get_json()
        image_data = data.get('image')
        TAMANO_REAL_LADO = float(data.get('tamano_lado', 0.05))  # 0.05 m = 5 cm por defecto
        config = obtener_configuracion()
        generar_visualizacion = data.get('generar_visualizacion', True)  # Por defecto siempre generar visualización
        
        if not image_data:
            return jsonify({"error": "No se recibió imagen"})
        
        # Decodifica la imagen base64
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Convierte a imagen OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"error": "No se pudo decodificar la imagen"})
        
        # Usar función mejorada de detección de ArUco
        corners, ids = mejorar_deteccion_aruco(img)
        
        if ids is None or len(ids) < 2:
            return jsonify({"error": "Se necesitan al menos 2 códigos ArUco para medir. Asegúrate de que ambos marcadores sean completamente visibles y estén bien iluminados."})
        
        # Ordenar marcadores por ID para consistencia
        marker_indices = np.argsort(ids.flatten())
        corners = [corners[i] for i in marker_indices]
        ids = ids[marker_indices]
        
        # Obtener las esquinas de los dos primeros marcadores
        marker1_corners = corners[0][0]
        marker2_corners = corners[1][0]
        
        # Calcular escala precisa usando el primer marcador
        metros_por_pixel, lado_px = calcular_escala_precisa(marker1_corners, TAMANO_REAL_LADO)
        
        # Calcular distancia usando método multipunto mejorado
        distancia_multipunto_metros, puntos_medicion, distancia_centros_metros = calcular_distancia_multipunto(
            marker1_corners, marker2_corners, metros_por_pixel
        )
        
        # Calcular distancia con corrección de perspectiva
        distancia_perspectiva_metros = calcular_distancia_con_correccion_perspectiva(
            marker1_corners, marker2_corners, metros_por_pixel, img.shape
        )
        
        # Aplicar filtrado temporal para mayor estabilidad
        distancia_filtrada, confianza = filtrar_mediciones_temporales(distancia_multipunto_metros)
        
        # Calcular también distancia entre bordes externos para comparación
        distancia_bordes_metros, edge1, edge2 = calcular_distancia_entre_bordes(
            marker1_corners, marker2_corners, metros_por_pixel
        )
        
        # Área del cuadrado usando la distancia filtrada
        area = distancia_filtrada * distancia_filtrada
        
        # Información adicional para debugging y análisis
        debug_info = {
            "lado_px": float(lado_px),
            "metros_por_pixel": float(metros_por_pixel),
            "distancia_centros_metros": float(distancia_centros_metros),
            "distancia_bordes_metros": float(distancia_bordes_metros),
            "distancia_multipunto_metros": float(distancia_multipunto_metros),
            "distancia_perspectiva_metros": float(distancia_perspectiva_metros),
            "distancia_filtrada_metros": float(distancia_filtrada),
            "confianza_medicion": float(confianza),
            "num_mediciones_previas": len(mediciones_previas),
            "diferencia_centros_bordes": float(distancia_centros_metros - distancia_bordes_metros),
            "diferencia_multipunto_bordes": float(distancia_multipunto_metros - distancia_bordes_metros),
            "diferencia_perspectiva_bordes": float(distancia_perspectiva_metros - distancia_bordes_metros),
            "ids_detectados": ids.flatten().tolist(),
            "num_puntos_medicion": len(puntos_medicion),
            "desviacion_estandar": float(np.std([distancia_centros_metros, distancia_bordes_metros, distancia_multipunto_metros, distancia_perspectiva_metros])),
            "media_distancias": float(np.mean([distancia_centros_metros, distancia_bordes_metros, distancia_multipunto_metros, distancia_perspectiva_metros]))
        }
        
        # Determinar qué distancia usar basado en la confianza y consistencia
        distancias_disponibles = {
            "filtrado_temporal": distancia_filtrada,
            "multipunto": distancia_multipunto_metros,
            "perspectiva": distancia_perspectiva_metros,
            "bordes_externos": distancia_bordes_metros,
            "centros": distancia_centros_metros
        }
        
        # Calcular consistencia entre métodos
        desviacion_entre_metodos = debug_info["desviacion_estandar"]
        media_entre_metodos = debug_info["media_distancias"]
        consistencia_metodos = 1.0 - (desviacion_entre_metodos / media_entre_metodos) if media_entre_metodos > 0 else 0.5
        
        # Selección inteligente del método
        if confianza > 0.8 and consistencia_metodos > 0.9:
            # Alta confianza y alta consistencia: usar filtrado temporal
            distancia_final = distancia_filtrada
            metodo_usado = "filtrado_temporal"
        elif confianza > 0.6 and consistencia_metodos > 0.7:
            # Confianza media y buena consistencia: usar multipunto
            distancia_final = distancia_multipunto_metros
            metodo_usado = "multipunto"
        elif consistencia_metodos > 0.5:
            # Consistencia aceptable: usar perspectiva
            distancia_final = distancia_perspectiva_metros
            metodo_usado = "perspectiva"
        else:
            # Baja consistencia: usar bordes externos (más estable)
            distancia_final = distancia_bordes_metros
            metodo_usado = "bordes_externos"
        
        # Generar visualización del método de medición (solo si se solicita)
        imagen_base64 = None
        if generar_visualizacion:
            try:
                # Pasar los puntos exactos calculados para cada método
                puntos_visualizacion = None
                if metodo_usado == 'bordes_externos':
                    puntos_visualizacion = (edge1, edge2)  # Usar los bordes calculados
                elif metodo_usado in ['multipunto', 'filtrado_temporal']:
                    puntos_visualizacion = puntos_medicion  # Usar los puntos multipunto
                else:
                    # Para otros métodos, usar los centros
                    centro1 = np.mean(marker1_corners, axis=0)
                    centro2 = np.mean(marker2_corners, axis=0)
                    puntos_visualizacion = [(centro1, centro2)]
                
                imagen_base64 = generar_visualizacion_medicion(
                    img, marker1_corners, marker2_corners, puntos_visualizacion,
                    distancia_final, metodo_usado, confianza, debug_info
                )
            except Exception as e:
                print(f"Error generando visualización: {str(e)}")
                imagen_base64 = None
        
        # Devuelve los resultados al frontend con información mejorada
        return jsonify({
            "success": True,
            "distancia": round(float(distancia_final), 3),
            "area": round(float(area), 2),
            "distancia_detectada_px": round(float(np.linalg.norm(edge2 - edge1)), 2),
            "metros_por_pixel": float(metros_por_pixel),
            "tamano_lado": TAMANO_REAL_LADO,
            "confianza": round(float(confianza), 2),
            "metodo_usado": metodo_usado,
            "debug_info": debug_info,
            "visualizacion": imagen_base64
        })
        
    except Exception as e:
        import traceback
        print(f"Error en detectar_aruco: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error al procesar imagen: {str(e)}"})

# --- Ejecuta la app en modo debug ---
if __name__ == "__main__":
    app.run(debug=True)
