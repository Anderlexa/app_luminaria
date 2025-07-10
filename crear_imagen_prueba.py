import cv2
import numpy as np

def crear_imagen_prueba():
    """
    Crea una imagen de prueba con códigos ArUco para simular la detección
    """
    
    # Crear imagen de fondo
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Fondo blanco
    
    # Configurar diccionario ArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Generar dos códigos ArUco
    marker1 = cv2.aruco.generateImageMarker(aruco_dict, 0, 100)
    marker2 = cv2.aruco.generateImageMarker(aruco_dict, 1, 100)
    
    # Agregar bordes blancos
    marker1 = cv2.copyMakeBorder(marker1, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    marker2 = cv2.copyMakeBorder(marker2, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    
    # Convertir a color si es necesario
    if len(marker1.shape) == 2:
        marker1 = cv2.cvtColor(marker1, cv2.COLOR_GRAY2BGR)
    if len(marker2.shape) == 2:
        marker2 = cv2.cvtColor(marker2, cv2.COLOR_GRAY2BGR)
    
    # Colocar los marcadores en la imagen
    # Marcador 1 en la esquina superior izquierda
    img[50:50+marker1.shape[0], 50:50+marker1.shape[1]] = marker1
    
    # Marcador 2 en la esquina superior derecha (separado por ~300 píxeles = ~1 metro)
    img[50:50+marker2.shape[0], 450:450+marker2.shape[1]] = marker2
    
    # Agregar texto explicativo
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Imagen de Prueba - Códigos ArUco", (50, 30), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "ArUco ID: 0", (50, 200), font, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "ArUco ID: 1", (450, 200), font, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Distancia: ~300px = ~1 metro", (200, 300), font, 0.6, (0, 0, 0), 2)
    
    # Agregar líneas de referencia
    cv2.line(img, (140, 120), (540, 120), (0, 255, 0), 2)
    cv2.putText(img, "1 metro", (320, 110), font, 0.4, (0, 255, 0), 1)
    
    # Guardar imagen
    cv2.imwrite("static/imagen_prueba_aruco.png", img)
    print("✅ Imagen de prueba creada: static/imagen_prueba_aruco.png")
    print("📏 Esta imagen simula dos códigos ArUco separados por ~1 metro")
    print("📱 Puedes usar esta imagen para probar la detección automática")

if __name__ == "__main__":
    crear_imagen_prueba() 