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

# --- Inicialización de la app Flask ---
app = Flask(__name__)
CORS(app)  # Permite peticiones desde otros orígenes

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

# --- Ruta para procesar imagen y detectar ArUco ---
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
        
        # Convierte a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Configura el detector de ArUco con parámetros compatibles
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        
        # Parámetros optimizados compatibles con diferentes versiones de OpenCV
        try:
            aruco_params.adaptiveThreshWinSizeMin = 3
            aruco_params.adaptiveThreshWinSizeMax = 23
            aruco_params.adaptiveThreshWinSizeStep = 10
            aruco_params.adaptiveThreshConstant = 7
            aruco_params.minMarkerPerimeterRate = 0.03
            aruco_params.maxMarkerPerimeterRate = 4.0
            aruco_params.polygonalApproxAccuracyRate = 0.03
            aruco_params.minCornerDistanceRate = 0.05
            aruco_params.minDistanceToBorder = 3
            aruco_params.minOtsuStdDev = 5.0
            aruco_params.perspectiveRemovePixelPerCell = 4
            aruco_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
            aruco_params.maxErroneousBitsInBorderRate = 0.35
            
            # Parámetros que pueden no estar disponibles en todas las versiones
            if hasattr(aruco_params, 'cornerRefinementMethod'):
                aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
            if hasattr(aruco_params, 'cornerRefinementWinSize'):
                aruco_params.cornerRefinementWinSize = 5
            if hasattr(aruco_params, 'cornerRefinementMaxIterations'):
                aruco_params.cornerRefinementMaxIterations = 30
            if hasattr(aruco_params, 'cornerRefinementMinAccuracy'):
                aruco_params.cornerRefinementMinAccuracy = 0.01
        except AttributeError as e:
            print(f"Advertencia: Algunos parámetros no están disponibles: {e}")
            # Continuar con parámetros por defecto si algunos no están disponibles
        
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
        corners, ids, rejected = detector.detectMarkers(gray)
        
        if ids is None or len(ids) < 2:
            return jsonify({"error": "Se necesitan al menos 2 códigos ArUco para medir. Asegúrate de que ambos marcadores sean completamente visibles."})
        
        # Ordenar marcadores por ID para consistencia
        marker_indices = np.argsort(ids.flatten())
        corners = [corners[i] for i in marker_indices]
        ids = ids[marker_indices]
        
        # Obtener las esquinas de los dos primeros marcadores
        marker1_corners = corners[0][0]
        marker2_corners = corners[1][0]
        
        # Calcular escala precisa usando el primer marcador
        metros_por_pixel, lado_px = calcular_escala_precisa(marker1_corners, TAMANO_REAL_LADO)
        
        # Calcular distancia entre bordes externos
        distancia_bordes_metros, edge1, edge2 = calcular_distancia_entre_bordes(
            marker1_corners, marker2_corners, metros_por_pixel
        )
        
        # Calcular también distancia entre centros para comparación
        center1 = np.mean(marker1_corners, axis=0)
        center2 = np.mean(marker2_corners, axis=0)
        distancia_centros_px = np.linalg.norm(center2 - center1)
        distancia_centros_metros = distancia_centros_px * metros_por_pixel
        
        # Área del cuadrado usando la distancia entre bordes
        area = distancia_bordes_metros * distancia_bordes_metros
        
        # Información adicional para debugging
        debug_info = {
            "lado_px": float(lado_px),
            "metros_por_pixel": float(metros_por_pixel),
            "distancia_centros_metros": float(distancia_centros_metros),
            "diferencia_centros_bordes": float(distancia_centros_metros - distancia_bordes_metros),
            "ids_detectados": ids.flatten().tolist()
        }
        
        # Devuelve los resultados al frontend
        return jsonify({
            "success": True,
            "distancia": round(float(distancia_bordes_metros), 3),
            "area": round(float(area), 2),
            "distancia_detectada_px": round(float(np.linalg.norm(edge2 - edge1)), 2),
            "metros_por_pixel": float(metros_por_pixel),
            "tamano_lado": TAMANO_REAL_LADO,
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
