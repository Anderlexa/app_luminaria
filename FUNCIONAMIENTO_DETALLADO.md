# 📋 FUNCIONAMIENTO DETALLADO - CALCULADORA DE LUMINARIAS

## 🎯 **DESCRIPCIÓN GENERAL**

La **Calculadora de Luminarias** es una aplicación web que permite calcular automáticamente el número y distribución de luminarias necesarias para iluminar un espacio. La aplicación utiliza códigos ArUco para medir distancias de forma automática y precisa mediante visión por computadora.

---

## 🏗️ **ARQUITECTURA DEL SISTEMA**

### **Backend (Python/Flask)**
- **Framework**: Flask
- **Procesamiento de Imágenes**: OpenCV
- **Cálculos Numéricos**: NumPy
- **Autenticación**: FaceIO SDK

### **Frontend (HTML/CSS/JavaScript)**
- **Interfaz**: HTML5 + CSS3
- **Interactividad**: JavaScript vanilla
- **Acceso a Cámara**: WebRTC API
- **Autenticación**: FaceIO SDK

---

## 🔧 **COMPONENTES PRINCIPALES**

### **1. ARCHIVOS PRINCIPALES**

#### **`app.py` - Servidor Principal**
- **Función**: Servidor Flask que maneja todas las rutas y lógica del backend
- **Endpoints principales**:
  - `/` - Página principal
  - `/detectar_aruco` - Procesamiento de imágenes y detección de ArUcos
  - `/calcular_luminarias` - Cálculo de luminarias
  - `/configuracion` - Cambio de configuración velocidad/precisión

#### **`calcular_luminarias.py` - Lógica de Cálculo**
- **Función**: Contiene las fórmulas y algoritmos para calcular luminarias
- **Métodos principales**:
  - `calcular_luminarias(area, luxes_requeridos, flujo_luminoso, factor_mantenimiento)`
  - `distribuir_luminarias(num_luminarias, area)`

#### **`config_optimizacion.py` - Configuración de Rendimiento**
- **Función**: Define configuraciones para optimizar velocidad vs precisión
- **Configuraciones**:
  - `CONFIG_VELOCIDAD`: Parámetros para máxima velocidad
  - `CONFIG_PRECISION`: Parámetros para máxima precisión

### **2. ARCHIVOS DE INTERFAZ**

#### **`templates/index.html` - Interfaz Principal**
- **Secciones principales**:
  - Medición automática con cámara
  - Medición manual (alternativa)
  - Autenticación facial
  - Resultados y visualización

#### **`static/script.js` - Lógica del Frontend**
- **Funciones principales**:
  - `activarCamara()` - Acceso a la cámara web
  - `detectarArUco()` - Envío de imágenes al backend
  - `calcularLuminarias()` - Cálculo de luminarias
  - `toggleVisualization()` - Mostrar/ocultar visualización

#### **`static/style.css` - Estilos Visuales**
- **Diseño responsive** para diferentes dispositivos
- **Temas visuales** para una experiencia de usuario moderna

---

## 📷 **SISTEMA DE MEDICIÓN AUTOMÁTICA**

### **1. DETECCIÓN DE ARUCOS**

#### **Proceso de Detección**
```python
def mejorar_deteccion_aruco(imagen):
    # 1. Preprocesamiento de imagen
    gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    gray_suavizada = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 2. Configuración de parámetros ArUco
    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters_create()
    
    # 3. Detección de marcadores
    corners, ids, rejected = cv2.aruco.detectMarkers(
        gray_suavizada, aruco_dict, parameters=parameters
    )
    
    # 4. Refinamiento de esquinas subpíxel
    corners_refinados = detectar_esquinas_subpixel(gray_suavizada, corners)
    
    return corners_refinados, ids
```

#### **Refinamiento de Esquinas Subpíxel**
```python
def detectar_esquinas_subpixel(imagen_gray, corners):
    # Doble iteración para máxima precisión
    # Primera iteración: ventana 7x7
    # Segunda iteración: ventana 5x5
    # Criterio de terminación: 0.00001
    # Máximo 100 iteraciones
```

### **2. CÁLCULO DE DISTANCIA**

#### **Métodos de Medición Implementados**

##### **A. Método de Bordes Externos**
```python
def calcular_distancia_entre_bordes(corners1, corners2):
    # Encuentra los puntos más alejados entre marcadores
    edge1 = corners1[np.argmax(corners1[:, 0])]  # Punto más a la derecha
    edge2 = corners2[np.argmin(corners2[:, 0])]  # Punto más a la izquierda
    return np.linalg.norm(edge2 - edge1)
```

##### **B. Método Multipunto**
```python
def calcular_distancia_multipunto(corners1, corners2):
    # Calcula distancia usando múltiples puntos de referencia
    # Aplica filtrado MAD para eliminar outliers
    # Usa promedio ponderado para estabilidad
```

##### **C. Método de Centros**
```python
def calcular_distancia_entre_centros(corners1, corners2):
    # Calcula centro geométrico de cada marcador
    centro1 = np.mean(corners1, axis=0)
    centro2 = np.mean(corners2, axis=0)
    return np.linalg.norm(centro2 - centro1)
```

##### **D. Método con Corrección de Perspectiva**
```python
def calcular_distancia_con_correccion_perspectiva(corners1, corners2, imagen):
    # Aplica factor de corrección basado en distancia al centro
    # Reduce errores de distorsión de lente
```

##### **E. Método de Filtrado Temporal**
```python
def filtrar_mediciones_temporales(nueva_medicion):
    # Almacena mediciones en deque (ventana temporal)
    # Aplica filtrado MAD para outliers
    # Usa promedio ponderado con decaimiento exponencial
```

### **3. SELECCIÓN INTELIGENTE DE MÉTODO**

#### **Sistema de Confianza**
```python
def seleccionar_metodo_optimo(mediciones):
    # Evalúa confianza de cada método
    # Considera consistencia entre métodos
    # Selecciona método con mayor confianza
    # Fallback a método más estable si es necesario
```

---

## 🧮 **SISTEMA DE CÁLCULO DE LUMINARIAS**

### **1. FÓRMULAS PRINCIPALES**

#### **Número de Luminarias**
```
N = (E × A) / (Φ × FM × CU)

Donde:
- N = Número de luminarias
- E = Iluminancia requerida (500 lx)
- A = Área del local (m²)
- Φ = Flujo luminoso por luminaria (1600 lm)
- FM = Factor de mantenimiento (0.8)
- CU = Coeficiente de utilización (estimado)
```

#### **Distribución de Luminarias**
```python
def distribuir_luminarias(num_luminarias, area):
    # Calcula relación largo/ancho
    # Determina distribución óptima en filas y columnas
    # Ajusta para mantener simetría
```

### **2. CONSTANTES UTILIZADAS**
- **LUXES requeridos**: 500 lx
- **Flujo luminoso por luminaria**: 1600 lm
- **Factor de mantenimiento (FM)**: 0.8
- **Coeficiente de utilización**: Estimado según área

---

## 🎨 **SISTEMA DE VISUALIZACIÓN**

### **1. GENERACIÓN DE VISUALIZACIÓN**

#### **Proceso de Renderizado**
```python
def generar_visualizacion_medicion_optimizada(imagen, corners1, corners2, puntos_visualizacion, metodo_usado):
    # 1. Copia la imagen original
    # 2. Dibuja contornos de ArUcos (rojo y azul)
    # 3. Dibuja línea de medición según método usado:
    #    - Verde: entre centros
    #    - Naranja: multipunto
    #    - Púrpura: bordes externos
    # 4. Convierte a base64 con compresión JPEG
```

#### **Colores Utilizados**
- **🔴 Marcador ArUco 1**: Contorno rojo (`#ff0000`)
- **🔵 Marcador ArUco 2**: Contorno azul (`#0000ff`)
- **🟢 Línea entre centros**: Verde (`#00ff00`)
- **🟠 Líneas multipunto**: Naranja (`#ffa500`)
- **🟣 Línea bordes externos**: Púrpura (`#800080`)

### **2. OPTIMIZACIÓN DE RENDIMIENTO**
- **Compresión JPEG**: 70% para máxima velocidad
- **Sin texto en imagen**: Solo elementos visuales
- **Una sola imagen**: No múltiples subplots
- **OpenCV en lugar de Matplotlib**: Mayor velocidad

---

## 🔐 **SISTEMA DE AUTENTICACIÓN**

### **1. INTEGRACIÓN FACEIO**
```javascript
// Inicialización
const faceio = new FaceIO("app_id");

// Registro de usuario
async function enrollUser() {
    try {
        const userInfo = await faceio.enroll({
            locale: "es",
            payload: { userId: "user123" }
        });
    } catch (error) {
        console.error("Error en registro:", error);
    }
}

// Autenticación
async function authenticateUser() {
    try {
        const userData = await faceio.authenticate({
            locale: "es"
        });
    } catch (error) {
        console.error("Error en autenticación:", error);
    }
}
```

### **2. FLUJO DE AUTENTICACIÓN**
1. **Registro**: Usuario registra su rostro
2. **Autenticación**: Usuario se autentica con rostro
3. **Sesión**: Mantiene sesión activa
4. **Cierre**: Usuario puede cerrar sesión

---

## ⚙️ **SISTEMA DE CONFIGURACIÓN**

### **1. MODOS DE OPERACIÓN**

#### **Modo Velocidad**
```python
CONFIG_VELOCIDAD = {
    'REDUCIR_IMAGEN': True,
    'MAX_WIDTH': 800,
    'MAX_HEIGHT': 600,
    'COMPRESION_JPEG': 80,
    'VENTANA_SUBPIXEL': (3, 3),
    'ITERACIONES_SUBPIXEL': 15,
    'PRECISION_SUBPIXEL': 0.001
}
```

#### **Modo Precisión**
```python
CONFIG_PRECISION = {
    'REDUCIR_IMAGEN': False,
    'MAX_WIDTH': 1920,
    'MAX_HEIGHT': 1080,
    'COMPRESION_JPEG': 95,
    'VENTANA_SUBPIXEL': (5, 5),
    'ITERACIONES_SUBPIXEL': 100,
    'PRECISION_SUBPIXEL': 0.00001
}
```

### **2. CAMBIO DINÁMICO**
```python
@app.route('/configuracion', methods=['POST'])
def cambiar_configuracion():
    tipo = request.json.get('tipo')
    cambiar_configuracion(tipo)
    return jsonify({'status': 'success'})
```

---

## 📱 **INTERFAZ DE USUARIO**

### **1. SECCIONES PRINCIPALES**

#### **A. Medición Automática**
- **Activación de cámara**: Botón para activar/desactivar
- **Configuración de ArUco**: Tamaño del lado en centímetros
- **Resultados en tiempo real**: Distancia, área, confianza
- **Información técnica**: Datos de debugging opcionales
- **Visualización**: Imagen con método de medición

#### **B. Medición Manual**
- **Campo de entrada**: Distancia manual en metros
- **Alternativa**: Cuando la cámara no está disponible

#### **C. Autenticación**
- **Registro**: Botón para registrar rostro
- **Login**: Botón para autenticarse
- **Logout**: Botón para cerrar sesión

#### **D. Resultados**
- **Área total**: Calculada automáticamente
- **Número de luminarias**: Total necesario
- **Distribución**: Luminarias en filas y columnas
- **Imagen de distribución**: Visualización gráfica

### **2. FLUJO DE USUARIO**

#### **Paso a Paso**
1. **Configuración inicial**:
   - Ingresar tamaño del lado del ArUco
   - Opcional: Registrar rostro para autenticación

2. **Medición**:
   - Activar cámara
   - Colocar dos ArUcos en el espacio
   - La aplicación detecta y mide automáticamente

3. **Cálculo**:
   - Presionar "Calcular"
   - Sistema calcula luminarias necesarias
   - Muestra resultados y distribución

4. **Visualización** (opcional):
   - Mostrar proceso de medición
   - Ver método utilizado
   - Información técnica detallada

---

## 🔧 **OPTIMIZACIONES IMPLEMENTADAS**

### **1. RENDIMIENTO**
- **Reducción de imagen**: Para procesamiento más rápido
- **Compresión JPEG**: Balance calidad/velocidad
- **Parámetros ArUco optimizados**: Según modo seleccionado
- **OpenCV vs Matplotlib**: Mayor velocidad en visualización

### **2. PRECISIÓN**
- **Refinamiento subpíxel doble**: Máxima precisión en esquinas
- **Filtrado MAD**: Eliminación robusta de outliers
- **Múltiples métodos**: Selección inteligente del mejor
- **Corrección de perspectiva**: Reducción de errores de lente

### **3. ESTABILIDAD**
- **Filtrado temporal**: Promedio de múltiples mediciones
- **Sistema de confianza**: Evaluación de calidad
- **Fallback automático**: Método alternativo si falla el principal
- **Manejo de errores**: Robustez ante condiciones adversas

---

## 🚀 **DESPLIEGUE Y CONFIGURACIÓN**

### **1. REQUISITOS DEL SISTEMA**
```bash
# Dependencias Python
pip install -r requirements.txt

# Dependencias principales
flask==2.0.1
opencv-python==4.5.3.56
numpy==1.21.2
```

### **2. ARCHIVOS DE CONFIGURACIÓN**
- **`requirements.txt`**: Dependencias Python
- **`config_optimizacion.py`**: Configuración de rendimiento
- **`static/`**: Archivos estáticos (CSS, JS, imágenes)
- **`templates/`**: Plantillas HTML

### **3. EJECUCIÓN**
```bash
# Desarrollo local
python app.py

# Producción (con gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📊 **MÉTRICAS Y MONITOREO**

### **1. PRECISIÓN DE MEDICIÓN**
- **Error típico**: < 2% en condiciones normales
- **Confianza**: Sistema evalúa calidad de cada medición
- **Estabilidad**: Filtrado temporal reduce variabilidad

### **2. RENDIMIENTO**
- **Tiempo de procesamiento**: < 500ms (modo velocidad)
- **Tiempo de procesamiento**: < 2s (modo precisión)
- **Uso de memoria**: Optimizado para dispositivos móviles

### **3. USABILIDAD**
- **Interfaz responsive**: Funciona en móviles y desktop
- **Feedback visual**: Indicadores de estado en tiempo real
- **Manejo de errores**: Mensajes claros al usuario

---

## 🔮 **FUNCIONALIDADES FUTURAS**

### **1. MEJORAS PLANIFICADAS**
- **Calibración automática**: Sin necesidad de conocer tamaño de ArUco
- **Múltiples espacios**: Medición de áreas complejas
- **Exportación de resultados**: PDF, Excel, etc.
- **Historial de mediciones**: Base de datos de proyectos

### **2. INTEGRACIONES**
- **API REST**: Para integración con otros sistemas
- **Base de datos**: Almacenamiento persistente
- **Notificaciones**: Alertas y recordatorios
- **Colaboración**: Múltiples usuarios por proyecto

---

## 📝 **CONCLUSIÓN**

La **Calculadora de Luminarias** es una aplicación completa que combina:

- **Visión por computadora avanzada** para medición precisa
- **Algoritmos de cálculo optimizados** para luminarias
- **Interfaz de usuario intuitiva** y responsive
- **Sistema de autenticación biométrica** para seguridad
- **Optimización de rendimiento** para diferentes dispositivos

La aplicación está diseñada para ser **profesional, precisa y fácil de usar**, proporcionando una solución completa para el cálculo de iluminación en espacios arquitectónicos.

---

**👥 Autores**: Grupo 2 – Changoluisa, Sandoval, Mensias, Taipicaña, Hernandez  
**🎯 Versión**: Con medición automática desde bordes externos  
**📅 Última actualización**: Diciembre 2024
