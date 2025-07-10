import cv2
import numpy as np
import os

def generar_codigos_aruco():
    """
    Genera códigos ArUco para usar en la medición de distancias.
    Los códigos se guardan en la carpeta static/aruco/
    """
    
    # Crear directorio si no existe
    if not os.path.exists("static/aruco"):
        os.makedirs("static/aruco")
    
    # Configurar diccionario ArUco
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Generar códigos ArUco
    for i in range(10):  # Generar 10 códigos diferentes
        # Crear imagen del marcador
        marker_size = 200  # Tamaño en píxeles
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, i, marker_size)
        
        # Agregar borde blanco para mejor detección
        border_size = 50
        marker_with_border = cv2.copyMakeBorder(
            marker_img, 
            border_size, border_size, border_size, border_size,
            cv2.BORDER_CONSTANT, 
            value=(255, 255, 255)
        )
        
        # Agregar texto identificador
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(marker_with_border, f'ArUco ID: {i}', 
                   (10, marker_with_border.shape[0] - 10), 
                   font, 0.5, (0, 0, 0), 1)
        
        # Guardar imagen
        filename = f"static/aruco/aruco_{i}.png"
        cv2.imwrite(filename, marker_with_border)
        print(f"Generado: {filename}")
    
    # Crear archivo de instrucciones
    instrucciones = """
# Códigos ArUco para Medición de Luminarias

## Instrucciones de Uso:

1. **Imprime los códigos ArUco** que necesites (recomendamos al menos 2)
2. **Coloca los códigos** en el espacio que quieres medir
3. **Separa los códigos** por una distancia conocida (ej: 1 metro)
4. **Usa la cámara** de la aplicación para detectar automáticamente las dimensiones

## Códigos Disponibles:
- aruco_0.png - ID: 0
- aruco_1.png - ID: 1  
- aruco_2.png - ID: 2
- aruco_3.png - ID: 3
- aruco_4.png - ID: 4
- aruco_5.png - ID: 5
- aruco_6.png - ID: 6
- aruco_7.png - ID: 7
- aruco_8.png - ID: 8
- aruco_9.png - ID: 9

## Consejos:
- Imprime los códigos en papel blanco
- Asegúrate de que estén bien iluminados
- Mantén la cámara estable al capturar
- Los códigos deben estar completamente visibles en la imagen
"""
    
    with open("static/aruco/INSTRUCCIONES.txt", "w", encoding="utf-8") as f:
        f.write(instrucciones)
    
    print("\n✅ Códigos ArUco generados exitosamente!")
    print("📁 Revisa la carpeta: static/aruco/")
    print("📖 Lee las instrucciones en: static/aruco/INSTRUCCIONES.txt")

if __name__ == "__main__":
    generar_codigos_aruco() 