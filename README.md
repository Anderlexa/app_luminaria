# 💡 Calculadora de Luminarias con Medición Automática

## 📋 Descripción

Sistema web para calcular la distribución de luminarias en espacios industriales o comerciales, ahora con **medición automática usando códigos ArUco y la cámara del teléfono**.

## ✨ Nuevas Funcionalidades

### 📷 Medición Automática con Cámara
- **Detección de códigos ArUco** para medición precisa
- **Cálculo automático** de dimensiones del espacio
- **Interfaz intuitiva** con instrucciones paso a paso
- **Modo alternativo** de medición manual

### 🔐 Autenticación Biométrica
- **Reconocimiento facial** con FaceIO
- **Seguridad mejorada** para el acceso al sistema

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Generar Códigos ArUco
```bash
python generar_aruco.py
```
Esto creará códigos ArUco imprimibles en `static/aruco/`

### 3. Ejecutar la Aplicación
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📱 Cómo Usar

### Paso 1: Autenticación
1. Haz clic en "🔐 Registrar Rostro" para crear tu perfil
2. Haz clic en "✅ Iniciar con Rostro" para autenticarte

### Paso 2: Medición del Espacio

#### Opción A: Medición Automática (Recomendada)
1. **Imprime los códigos ArUco** de la carpeta `static/aruco/`
2. **Coloca dos códigos** en el espacio a medir
3. **Separa los códigos** por una distancia conocida (ej: 1 metro)
4. Haz clic en "📷 Activar Cámara"
5. **Apunta la cámara** hacia los códigos ArUco
6. Haz clic en "📸 Capturar y Medir"
7. **Verifica los resultados** mostrados

#### Opción B: Medición Manual
1. Haz clic en "🔄 Cambiar a Medición Manual"
2. **Ingresa las dimensiones** manualmente
3. **Base y altura** en metros

### Paso 3: Cálculo de Luminarias
1. Haz clic en "Calcular"
2. **Revisa los resultados**:
   - Área total
   - Número de luminarias necesarias
   - Distribución en X e Y
   - Visualización gráfica

## 🔧 Configuración Técnica

### Códigos ArUco
- **Tipo**: DICT_4X4_50
- **Tamaño**: 200px con borde de 50px
- **Cantidad**: 10 códigos diferentes (ID 0-9)
- **Formato**: PNG con texto identificador

### Calibración
El sistema asume que los códigos ArUco están separados por **1 metro**. Para mayor precisión:
- Mide la distancia real entre los códigos
- Ajusta el valor `METROS_POR_PIXEL` en `app.py`

### Cámara
- **Resolución**: 1280x720 (ideal)
- **Orientación**: Cámara trasera en móviles
- **Formato**: JPEG con calidad 0.8

## 📊 Cálculos Realizados

### Constantes Utilizadas
- **LUXES requeridos**: 500 lx
- **Flujo luminoso por luminaria**: 1600 lm
- **Factor de mantenimiento (FM)**: 0.8

### Fórmulas
```
Área = Base × Altura
Número de luminarias = (LUXES × Área) / (LUMEN × FM)
Distribución X = √((Altura × NL) / Base)
Distribución Y = (Base × X) / Altura
```

## 🛠️ Estructura del Proyecto

```
app_luminaria-main/
├── app.py                 # Servidor Flask principal
├── calcular_luminarias.py # Lógica de cálculo
├── generar_aruco.py      # Generador de códigos ArUco
├── requirements.txt      # Dependencias Python
├── static/
│   ├── aruco/           # Códigos ArUco generados
│   ├── script.js        # JavaScript del frontend
│   └── style.css        # Estilos CSS
└── templates/
    └── index.html       # Interfaz principal
```

## 🔍 API Endpoints

### GET `/`
- Página principal de la aplicación

### GET `/generar`
- **Parámetros**: `base`, `altura`
- **Retorna**: Cálculos de luminarias y URL de imagen

### POST `/detectar_aruco`
- **Body**: `{"image": "base64_image_data"}`
- **Retorna**: Dimensiones detectadas automáticamente

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ Chrome (recomendado)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

### Dispositivos
- ✅ Teléfonos móviles
- ✅ Tablets
- ✅ Computadoras de escritorio

### Requisitos
- Cámara web o cámara de teléfono
- Permisos de cámara habilitados
- Conexión HTTPS (para cámara en producción)

## 🚀 Despliegue

### Heroku
El proyecto incluye `Procfile` para despliegue en Heroku:

```bash
git add .
git commit -m "Actualización con medición automática"
git push heroku main
```

### Variables de Entorno
```bash
FLASK_ENV=production
```

## 👥 Autores

**Grupo 2** - Instalaciones Industriales
- Changoluisa
- Sandoval  
- Mensias
- Taipicaña
- Hernandez

## 📄 Licencia

Proyecto académico para el curso de Instalaciones Industriales.

## 🆘 Solución de Problemas

### La cámara no se activa
- Verifica los permisos del navegador
- Asegúrate de usar HTTPS en producción
- Prueba en un navegador diferente

### No detecta códigos ArUco
- Verifica que los códigos estén bien iluminados
- Asegúrate de que estén completamente visibles
- Imprime los códigos en papel blanco
- Mantén la cámara estable

### Error en cálculos
- Verifica que las dimensiones sean mayores a 0
- Asegúrate de estar autenticado
- Revisa la consola del navegador para errores

## 🔄 Actualizaciones Recientes

### v2.0 - Medición Automática
- ✅ Detección de códigos ArUco
- ✅ Interfaz de cámara integrada
- ✅ Cálculo automático de dimensiones
- ✅ Modo manual alternativo
- ✅ Mejoras en la UI/UX 