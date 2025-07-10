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

@app.route("/test")
def test():
    return render_template("test.html")

@app.route("/test_faceio")
def test_faceio():
    return render_template("test_faceio.html")

# --- Ruta para calcular luminarias ---
@app.route("/generar")
def generar():
    # Recibe base y altura, calcula luminarias y devuelve resultados
    try:
        base = float(request.args.get("base", 0))
        altura = float(request.args.get("altura", 0))
        if base <= 0 or altura <= 0:
            return jsonify({"error": "Base y altura deben ser mayores que 0."})
        resultado = calcular_y_generar_imagen(base, altura)
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
        # Convierte a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Configura el detector de ArUco
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
        corners, ids, rejected = detector.detectMarkers(gray)
        if ids is None or len(ids) < 2:
            return jsonify({"error": "Se necesitan al menos 2 códigos ArUco para medir"})
        # Obtiene las esquinas y calcula el centro de cada marcador
        marker1_corners = corners[0][0]
        marker2_corners = corners[1][0]
        center1 = np.mean(marker1_corners, axis=0)
        center2 = np.mean(marker2_corners, axis=0)
        # Calcula el lado del primer marcador en píxeles (promedio de los 4 lados)
        lados_marker1 = [
            np.linalg.norm(marker1_corners[0] - marker1_corners[1]),
            np.linalg.norm(marker1_corners[1] - marker1_corners[2]),
            np.linalg.norm(marker1_corners[2] - marker1_corners[3]),
            np.linalg.norm(marker1_corners[3] - marker1_corners[0])
        ]
        lado_px = float(np.mean(lados_marker1))
        # Calcula la escala metros/píxel
        metros_por_pixel = TAMANO_REAL_LADO / lado_px
        # Diferencia en X y Y (en píxeles)
        delta_x = abs(center2[0] - center1[0])
        delta_y = abs(center2[1] - center1[1])
        # Base y altura en metros
        base_metros = delta_x * metros_por_pixel
        altura_metros = delta_y * metros_por_pixel
        area = base_metros * altura_metros
        # Distancia diagonal entre centros (opcional)
        distancia_centros_px = float(np.linalg.norm(center2 - center1))
        distancia_real_metros = distancia_centros_px * metros_por_pixel
        # Devuelve los resultados al frontend
        return jsonify({
            "success": True,
            "base": round(float(base_metros), 2),
            "altura": round(float(altura_metros), 2),
            "area": round(float(area), 2),
            "distancia_detectada_px": round(float(distancia_centros_px), 2),
            "distancia_real_metros": round(float(distancia_real_metros), 3),
            "metros_por_pixel": metros_por_pixel,
            "tamano_lado": TAMANO_REAL_LADO
        })
    except Exception as e:
        return jsonify({"error": f"Error al procesar imagen: {str(e)}"})

# --- Ejecuta la app en modo debug ---
if __name__ == "__main__":
    app.run(debug=True)
