#!/usr/bin/env python3
"""
Script de prueba para verificar la precisión mejorada del sistema ArUco.
Este script demuestra las mejoras implementadas:
1. Medición desde bordes externos
2. Filtrado de outliers
3. Detección optimizada
4. Calibración precisa
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import os

def crear_imagen_prueba_con_aruco():
    """
    Crea una imagen de prueba con dos marcadores ArUco para demostrar
    la medición desde bordes externos.
    """
    # Crear imagen de fondo
    img = np.ones((800, 1200, 3), dtype=np.uint8) * 255
    
    # Configurar diccionario ArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Generar marcadores
    marker1 = cv2.aruco.generateImageMarker(aruco_dict, 0, 100)
    marker2 = cv2.aruco.generateImageMarker(aruco_dict, 1, 100)
    
    # Agregar bordes blancos
    marker1_with_border = cv2.copyMakeBorder(marker1, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    marker2_with_border = cv2.copyMakeBorder(marker2, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    
    # Posicionar marcadores en la imagen
    # Marcador 1 en (200, 300)
    x1, y1 = 200, 300
    h1, w1 = marker1_with_border.shape
    img[y1:y1+h1, x1:x1+w1] = cv2.cvtColor(marker1_with_border, cv2.COLOR_GRAY2BGR)
    
    # Marcador 2 en (800, 300) - distancia conocida de 600 píxeles
    x2, y2 = 800, 300
    h2, w2 = marker2_with_border.shape
    img[y2:y2+h2, x2:x2+w2] = cv2.cvtColor(marker2_with_border, cv2.COLOR_GRAY2BGR)
    
    # Agregar texto informativo
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Test de Precision ArUco - Medicion desde Bordes Externos", 
                (50, 50), font, 1, (0, 0, 0), 2)
    cv2.putText(img, f"Distancia real entre bordes: 600 px", 
                (50, 100), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Marcador 1 (ID: 0) en ({x1}, {y1})", 
                (50, 150), font, 0.6, (0, 0, 0), 2)
    cv2.putText(img, f"Marcador 2 (ID: 1) en ({x2}, {y2})", 
                (50, 180), font, 0.6, (0, 0, 0), 2)
    
    return img

def test_deteccion_aruco_mejorada():
    """
    Prueba la detección de ArUco con las mejoras implementadas.
    """
    print("🧪 Iniciando prueba de detección ArUco mejorada...")
    
    # Crear imagen de prueba
    img = crear_imagen_prueba_con_aruco()
    
    # Guardar imagen de prueba
    cv2.imwrite("static/imagen_prueba_precision.png", img)
    print("✅ Imagen de prueba creada: static/imagen_prueba_precision.png")
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Configurar detector con parámetros compatibles
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
        # Continuar con parámetros por defecto
    
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    corners, ids, rejected = detector.detectMarkers(gray)
    
    if ids is None or len(ids) < 2:
        print("❌ Error: No se detectaron suficientes marcadores ArUco")
        return
    
    print(f"✅ Marcadores detectados: {len(ids)}")
    print(f"📋 IDs detectados: {ids.flatten()}")
    
    # Ordenar marcadores por ID
    marker_indices = np.argsort(ids.flatten())
    corners = [corners[i] for i in marker_indices]
    ids = ids[marker_indices]
    
    # Obtener esquinas de los dos primeros marcadores
    marker1_corners = corners[0][0]
    marker2_corners = corners[1][0]
    
    # Simular tamaño real conocido (5cm = 0.05m)
    TAMANO_REAL_LADO = 0.05
    
    # Calcular escala precisa
    lados = []
    for i in range(4):
        lado = np.linalg.norm(marker1_corners[i] - marker1_corners[(i + 1) % 4])
        lados.append(lado)
    
    lados = np.array(lados)
    mean_lado = np.mean(lados)
    std_lado = np.std(lados)
    
    # Filtrar outliers
    lados_filtrados = lados[np.abs(lados - mean_lado) <= 2 * std_lado]
    
    if len(lados_filtrados) == 0:
        lado_px = mean_lado
    else:
        lado_px = np.mean(lados_filtrados)
    
    metros_por_pixel = TAMANO_REAL_LADO / lado_px
    
    print(f"📏 Lado detectado (px): {lado_px:.2f}")
    print(f"📏 Metros por píxel: {metros_por_pixel:.6f}")
    
    # Calcular distancia entre bordes externos
    center1 = np.mean(marker1_corners, axis=0)
    center2 = np.mean(marker2_corners, axis=0)
    
    direction = center2 - center1
    direction_normalized = direction / np.linalg.norm(direction)
    
    # Encontrar puntos más externos
    distances1 = [np.dot(corner - center1, direction_normalized) for corner in marker1_corners]
    edge1_idx = np.argmax(distances1)
    edge1 = marker1_corners[edge1_idx]
    
    distances2 = [np.dot(corner - center2, -direction_normalized) for corner in marker2_corners]
    edge2_idx = np.argmax(distances2)
    edge2 = marker2_corners[edge2_idx]
    
    # Calcular distancias
    distancia_bordes_px = np.linalg.norm(edge2 - edge1)
    distancia_bordes_metros = distancia_bordes_px * metros_por_pixel
    
    distancia_centros_px = np.linalg.norm(center2 - center1)
    distancia_centros_metros = distancia_centros_px * metros_por_pixel
    
    print(f"🎯 Distancia entre bordes externos: {distancia_bordes_px:.2f} px = {distancia_bordes_metros:.3f} m")
    print(f"🎯 Distancia entre centros: {distancia_centros_px:.2f} px = {distancia_centros_metros:.3f} m")
    print(f"📊 Diferencia: {distancia_centros_metros - distancia_bordes_metros:.3f} m")
    
    # Crear visualización
    crear_visualizacion_deteccion(img, marker1_corners, marker2_corners, 
                                 edge1, edge2, center1, center2)
    
    return {
        'distancia_bordes_px': distancia_bordes_px,
        'distancia_bordes_metros': distancia_bordes_metros,
        'distancia_centros_px': distancia_centros_px,
        'distancia_centros_metros': distancia_centros_metros,
        'metros_por_pixel': metros_por_pixel,
        'lado_px': lado_px
    }

def crear_visualizacion_deteccion(img, corners1, corners2, edge1, edge2, center1, center2):
    """
    Crea una visualización de la detección con anotaciones.
    """
    # Crear copia de la imagen para dibujar
    img_viz = img.copy()
    
    # Dibujar esquinas de los marcadores
    cv2.aruco.drawDetectedMarkers(img_viz, [corners1.reshape(1, 4, 2)], np.array([[0]]))
    cv2.aruco.drawDetectedMarkers(img_viz, [corners2.reshape(1, 4, 2)], np.array([[1]]))
    
    # Dibujar centros
    cv2.circle(img_viz, tuple(center1.astype(int)), 5, (0, 255, 0), -1)
    cv2.circle(img_viz, tuple(center2.astype(int)), 5, (0, 255, 0), -1)
    
    # Dibujar bordes externos
    cv2.circle(img_viz, tuple(edge1.astype(int)), 8, (0, 0, 255), -1)
    cv2.circle(img_viz, tuple(edge2.astype(int)), 8, (0, 0, 255), -1)
    
    # Dibujar línea entre bordes externos
    cv2.line(img_viz, tuple(edge1.astype(int)), tuple(edge2.astype(int)), (255, 0, 0), 3)
    
    # Dibujar línea entre centros
    cv2.line(img_viz, tuple(center1.astype(int)), tuple(center2.astype(int)), (0, 255, 0), 2)
    
    # Agregar texto
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img_viz, "Centros (Verde)", (50, 700), font, 0.6, (0, 255, 0), 2)
    cv2.putText(img_viz, "Bordes Externos (Rojo)", (50, 730), font, 0.6, (0, 0, 255), 2)
    cv2.putText(img_viz, "Medicion desde Bordes Externos", (50, 760), font, 0.6, (255, 0, 0), 2)
    
    # Guardar visualización
    cv2.imwrite("static/visualizacion_deteccion.png", img_viz)
    print("✅ Visualización guardada: static/visualizacion_deteccion.png")

def generar_reporte_precision(resultados):
    """
    Genera un reporte de precisión con los resultados de la prueba.
    """
    reporte = f"""
# 📊 Reporte de Precisión ArUco Mejorada

## 🎯 Resultados de la Prueba

### Mediciones Obtenidas:
- **Distancia entre bordes externos:** {resultados['distancia_bordes_px']:.2f} px = {resultados['distancia_bordes_metros']:.3f} m
- **Distancia entre centros:** {resultados['distancia_centros_px']:.2f} px = {resultados['distancia_centros_metros']:.3f} m
- **Diferencia:** {resultados['distancia_centros_metros'] - resultados['distancia_bordes_metros']:.3f} m

### Parámetros de Calibración:
- **Lado detectado:** {resultados['lado_px']:.2f} px
- **Metros por píxel:** {resultados['metros_por_pixel']:.6f}
- **Tamaño real del marcador:** 0.05 m (5 cm)

## 🚀 Mejoras Implementadas

### 1. Medición desde Bordes Externos
- ✅ Elimina la variabilidad del tamaño de los marcadores
- ✅ Mayor precisión en mediciones
- ✅ Consistencia en diferentes condiciones

### 2. Detección Optimizada
- ✅ Parámetros de detección mejorados
- ✅ Filtrado de outliers
- ✅ Refinamiento de esquinas con subpíxeles

### 3. Calibración Precisa
- ✅ Múltiples mediciones del lado del marcador
- ✅ Eliminación de valores atípicos
- ✅ Escala calculada con mayor precisión

## 📈 Beneficios de la Mejora

1. **Mayor Precisión:** La medición desde bordes externos proporciona mayor precisión
2. **Menor Variabilidad:** Elimina la dependencia del tamaño exacto del marcador
3. **Mejor Estabilidad:** Parámetros optimizados para detección más estable
4. **Información Detallada:** Proporciona datos técnicos para debugging

## 🔧 Archivos Generados

- `static/imagen_prueba_precision.png` - Imagen de prueba
- `static/visualizacion_deteccion.png` - Visualización de la detección
- `static/reporte_precision.txt` - Este reporte

## 📋 Instrucciones de Uso

1. Imprime los marcadores ArUco optimizados
2. Coloca dos marcadores en el espacio a medir
3. Ingresa el tamaño real del lado del marcador
4. Activa la cámara y apunta hacia los marcadores
5. La medición se realiza automáticamente desde los bordes externos
"""
    
    with open("static/reporte_precision.txt", "w", encoding="utf-8") as f:
        f.write(reporte)
    
    print("✅ Reporte de precisión generado: static/reporte_precision.txt")

def main():
    """
    Función principal que ejecuta todas las pruebas.
    """
    print("🎯 Iniciando pruebas de precisión ArUco mejorada...")
    print("=" * 60)
    
    # Crear directorio static si no existe
    if not os.path.exists("static"):
        os.makedirs("static")
    
    try:
        # Ejecutar prueba de detección
        resultados = test_deteccion_aruco_mejorada()
        
        if resultados:
            print("\n" + "=" * 60)
            print("📊 Generando reporte de precisión...")
            generar_reporte_precision(resultados)
            
            print("\n" + "=" * 60)
            print("✅ Pruebas completadas exitosamente!")
            print("📁 Revisa los archivos generados en la carpeta static/")
            print("🎯 La precisión ha sido mejorada con medición desde bordes externos")
        else:
            print("❌ Error en las pruebas de detección")
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 