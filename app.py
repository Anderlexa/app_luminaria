# --- Importaciones necesarias ---
from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from calcular_luminarias import calcular_y_generar_imagen
import os
import cv2
import numpy as np
import base64
from PIL import Image
import io
from collections import deque
import time

# --- Inicialización de la app Flask ---
app = Flask(__name__)
CORS(app)  # Permite peticiones desde otros orígenes

# --- Variables globales para filtrado temporal ---
mediciones_previas = deque(maxlen=10)  # Almacena las últimas 10 mediciones
ultima_medicion_tiempo = 0

# --- Funciones mejoradas para detección precisa ---

def detectar_esquinas_subpixel(imagen, corners, ventana=(5, 5), zona_muerta=(-1, -1)):
    """
    Refina las esquinas detectadas con precisión subpíxel.
    
    Args:
        imagen: Imagen en escala de grises
        corners: Esquinas detectadas por ArUco
        ventana: Tamaño de la ventana de búsqueda
        zona_muerta: Zona muerta para el refinamiento
    
    Returns:
        corners_refinadas: Esquinas con precisión subpíxel
    """
    corners_refinadas = []
    
    for marker_corners in corners:
        # Convertir a formato float32 para subpíxel
        corners_float = np.float32(marker_corners)
        
        # Refinar esquinas con precisión subpíxel
        corners_refinadas_marker = cv2.cornerSubPix(
            imagen, 
            corners_float, 
            ventana, 
            zona_muerta,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
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
    
    # Calcular distancia promedio ponderada
    # Dar más peso a las mediciones más estables
    distancias_esquinas = np.array(distancias_esquinas)
    pesos = 1.0 / (1.0 + np.abs(distancias_esquinas - np.median(distancias_esquinas)))
    pesos = pesos / np.sum(pesos)
    
    distancia_promedio_px = np.sum(distancias_esquinas * pesos)
    distancia_promedio_metros = distancia_promedio_px * metros_por_pixel
    
    return distancia_promedio_metros, puntos_medicion, distancia_centros * metros_por_pixel

def filtrar_mediciones_temporales(nueva_medicion, ventana_tiempo=2.0):
    """
    Filtra outliers y promedia mediciones temporales.
    
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
    
    # Extraer distancias
    distancias = [m['distancia'] for m in mediciones_previas]
    
    # Calcular estadísticas
    media = np.mean(distancias)
    desviacion = np.std(distancias)
    
    # Filtrar outliers (más de 2 desviaciones estándar)
    distancias_filtradas = [d for d in distancias if abs(d - media) <= 2 * desviacion]
    
    if len(distancias_filtradas) == 0:
        # Si todas son outliers, usar la mediana
        medicion_filtrada = np.median(distancias)
        confianza = 0.3
    else:
        # Usar promedio de mediciones no-outliers
        medicion_filtrada = np.mean(distancias_filtradas)
        # Calcular confianza basada en la consistencia
        confianza = 1.0 - (desviacion / media) if media > 0 else 0.5
        confianza = max(0.1, min(1.0, confianza))
    
    return medicion_filtrada, confianza

def mejorar_deteccion_aruco(imagen):
    """
    Mejora la detección de ArUco con múltiples técnicas.
    
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
    
    # Aplicar filtros para mejorar la detección
    # Filtro Gaussiano para reducir ruido
    gray_suavizada = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Ecualización de histograma para mejorar contraste
    gray_ecualizada = cv2.equalizeHist(gray_suavizada)
    
    # Configurar detector ArUco con parámetros optimizados
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aruco_params = cv2.aruco.DetectorParameters()
    
    # Parámetros optimizados para mayor precisión
    aruco_params.adaptiveThreshWinSizeMin = 3
    aruco_params.adaptiveThreshWinSizeMax = 23
    aruco_params.adaptiveThreshWinSizeStep = 10
    aruco_params.adaptiveThreshConstant = 7
    aruco_params.minMarkerPerimeterRate = 0.03
    aruco_params.maxMarkerPerimeterRate = 4.0
    aruco_params.polygonalApproxAccuracyRate = 0.02  # Más preciso
    aruco_params.minCornerDistanceRate = 0.05
    aruco_params.minDistanceToBorder = 3
    aruco_params.minOtsuStdDev = 5.0
    aruco_params.perspectiveRemovePixelPerCell = 4
    aruco_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
    aruco_params.maxErroneousBitsInBorderRate = 0.35
    
    # Configurar refinamiento de esquinas si está disponible
    if hasattr(aruco_params, 'cornerRefinementMethod'):
        aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    if hasattr(aruco_params, 'cornerRefinementWinSize'):
        aruco_params.cornerRefinementWinSize = 5
    if hasattr(aruco_params, 'cornerRefinementMaxIterations'):
        aruco_params.cornerRefinementMaxIterations = 30
    if hasattr(aruco_params, 'cornerRefinementMinAccuracy'):
        aruco_params.cornerRefinementMinAccuracy = 0.01
    
    # Detectar ArUco
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    corners, ids, rejected = detector.detectMarkers(gray_ecualizada)
    
    if ids is None or len(ids) < 2:
        # Intentar con imagen original si falla
        corners, ids, rejected = detector.detectMarkers(gray)
    
    if ids is None or len(ids) < 2:
        return None, None
    
    # Refinar esquinas con precisión subpíxel
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

# --- Ruta para procesar imagen y detectar ArUco con precisión mejorada ---
@app.route("/detectar_aruco", methods=["POST"])
def detectar_aruco():
    try:
        # Recibe imagen y tamaño del lado del ArUco (en metros)
        data = request.get_json()
        image_data = data.get('image')
        TAMANO_REAL_LADO = float(data.get('tamano_lado', 0.05))  # 0.05 m = 5 cm por defecto
        
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
            "distancia_filtrada_metros": float(distancia_filtrada),
            "confianza_medicion": float(confianza),
            "num_mediciones_previas": len(mediciones_previas),
            "diferencia_centros_bordes": float(distancia_centros_metros - distancia_bordes_metros),
            "diferencia_multipunto_bordes": float(distancia_multipunto_metros - distancia_bordes_metros),
            "ids_detectados": ids.flatten().tolist(),
            "num_puntos_medicion": len(puntos_medicion)
        }
        
        # Determinar qué distancia usar basado en la confianza
        if confianza > 0.7:
            distancia_final = distancia_filtrada
            metodo_usado = "filtrado_temporal"
        elif confianza > 0.5:
            distancia_final = distancia_multipunto_metros
            metodo_usado = "multipunto"
        else:
            distancia_final = distancia_bordes_metros
            metodo_usado = "bordes_externos"
        
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
            "debug_info": debug_info
        })
        
    except Exception as e:
        import traceback
        print(f"Error en detectar_aruco: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Error al procesar imagen: {str(e)}"})

# --- Ejecuta la app en modo debug ---
if __name__ == "__main__":
    app.run(debug=True)
