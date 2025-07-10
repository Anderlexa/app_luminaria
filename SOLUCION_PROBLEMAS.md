# 🔧 Solución de Problemas - FaceIO y Cámara

## 🚨 Problemas Reportados
1. **Error al registrar rostro**: "No se pudo registrar el rostro"
2. **Error de cámara**: "Error al acceder a la cámara. Verifica los permisos"

## 🔍 Diagnóstico Paso a Paso

### 1. Verificar la Aplicación
- Abre tu navegador y ve a: `http://localhost:5000`
- La aplicación debe estar ejecutándose sin errores

### 2. Probar FaceIO (Nuevo)
- Ve a: `http://localhost:5000/test_faceio`
- Esta página te permitirá probar FaceIO de forma aislada
- Haz clic en "🔐 Probar Registro" y observa los mensajes detallados

### 3. Verificar Consola del Navegador
1. Abre las herramientas de desarrollador (F12)
2. Ve a la pestaña "Consola"
3. Busca mensajes de error específicos

### 4. Probar Cámara Básica
En la consola del navegador, ejecuta:
```javascript
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => { 
    console.log("✅ Cámara OK!"); 
    stream.getTracks().forEach(track => track.stop());
  })
  .catch(err => { 
    console.error("❌ Error cámara:", err); 
  });
```

## 🛠️ Soluciones por Tipo de Error

### Error de FaceIO

#### Problema: "FaceIO no está disponible"
**Solución:**
- Verifica tu conexión a internet
- El script de FaceIO debe cargar desde: `https://cdn.faceio.net/fio.js`

#### Problema: "Error de cámara" en FaceIO
**Solución:**
- Asegúrate de que la cámara no esté siendo usada por otra aplicación
- Verifica que Opera GX tenga permisos de cámara
- Ve a Configuración > Sitios web > Cámara y permite el acceso

#### Problema: "No se detectó un rostro válido"
**Solución:**
- Asegúrate de estar bien iluminado
- Mira directamente a la cámara
- Mantén una distancia de 30-60 cm de la cámara
- Evita sombras en tu rostro

### Error de Cámara para ArUco

#### Problema: "Permisos de cámara denegados"
**Solución:**
1. En Opera GX, haz clic en el ícono de cámara en la barra de direcciones
2. Selecciona "Permitir"
3. O ve a Configuración > Sitios web > Cámara > localhost:5000 > Permitir

#### Problema: "No se encontró ninguna cámara"
**Solución:**
- Verifica que tu cámara esté conectada y funcionando
- Prueba la cámara en otra aplicación
- Reinicia el navegador

#### Problema: "La cámara está siendo usada por otra aplicación"
**Solución:**
- Cierra otras aplicaciones que usen la cámara (Zoom, Teams, etc.)
- Reinicia el navegador

## 🔧 Mejoras Implementadas

### 1. Mejor Manejo de Errores
- Mensajes de error más específicos y útiles
- Logs detallados en la consola del navegador
- Diferentes mensajes según el tipo de error

### 2. Verificación de Dependencias
- Verifica que FaceIO esté cargado antes de usarlo
- Verifica que getUserMedia esté disponible
- Manejo de errores de inicialización

### 3. Página de Prueba
- Nueva página `/test_faceio` para probar FaceIO de forma aislada
- Pruebas individuales de registro, autenticación y cámara
- Logs detallados de cada operación

## 📋 Pasos de Verificación

### Para FaceIO:
1. ✅ Ve a `http://localhost:5000/test_faceio`
2. ✅ Haz clic en "🔐 Probar Registro"
3. ✅ Si funciona, el problema está en la página principal
4. ✅ Si no funciona, revisa los mensajes de error

### Para Cámara ArUco:
1. ✅ Ve a `http://localhost:5000`
2. ✅ Haz clic en "📷 Activar Cámara"
3. ✅ Si pide permisos, acepta
4. ✅ Si da error, revisa la consola del navegador

## 🆘 Si Nada Funciona

### Opción 1: Cambiar Navegador
- Prueba con Chrome o Firefox
- Algunos navegadores tienen mejor soporte para getUserMedia

### Opción 2: Verificar ID de FaceIO
- El ID actual es: `"fioa2e2c"`
- Si no funciona, puedes crear uno nuevo en: https://faceio.net/
- Reemplaza el ID en `script.js` línea 15

### Opción 3: Usar Solo Medición Manual
- Si FaceIO no funciona, puedes usar solo la medición manual
- Haz clic en "🔄 Cambiar a Medición Manual"
- Ingresa las dimensiones manualmente

## 📞 Información de Debug

Si sigues teniendo problemas, proporciona:
1. **Mensajes exactos de error** de la consola del navegador
2. **URL** desde donde accedes a la aplicación
3. **Navegador y versión** que estás usando
4. **Sistema operativo** (Windows 10 en tu caso)

---

**Nota:** La aplicación está configurada para funcionar en `localhost`, lo cual debería permitir acceso a la cámara sin problemas de HTTPS. 