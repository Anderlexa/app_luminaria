// --- Variables globales y estado de la cámara ---
let faceio;
let usuarioAutenticado = false;
let stream = null;
let video = null;
let canvas = null;
let ctx = null;
let modoCamara = true; // true = cámara, false = manual
let intervaloMedicion = null; // Para medición en tiempo real
let distanciaGuardada = null; // Para guardar la distancia medida

// --- Inicialización al cargar la página ---
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM cargado, inicializando...");
  
  // Inicializa elementos de cámara
  video = document.getElementById('video');
  canvas = document.getElementById('canvas');
  ctx = canvas.getContext('2d');
  
  // Inicializa FaceIO con manejo de errores
  try {
    if (typeof faceIO !== 'undefined') {
      faceio = new faceIO("fioab695", {
        container: "#faceio-modal-container"
      });
      console.log("FaceIO inicializado correctamente");
    } else {
      console.error("FaceIO no está disponible");
      mostrarStatus("Error: FaceIO no se cargó correctamente", "error");
    }
  } catch (error) {
    console.error("Error al inicializar FaceIO:", error);
    mostrarStatus("Error al inicializar FaceIO", "error");
  }
});

// --- Funciones de autenticación facial ---
window.enrollUser = async function () {
  try {
    console.log("Iniciando registro facial...");
    
    if (!faceio) {
      throw new Error("FaceIO no está inicializado");
    }
    
    const userInfo = await faceio.enroll({
      locale: "auto",
      payload: {
        email: "demo@luminaria.com",
        nombre: "Usuario Luminaria"
      }
    });
    console.log("Usuario registrado:", userInfo);
    alert("✅ Registro exitoso. Ahora puedes iniciar sesión con tu rostro.");
  } catch (error) {
    console.error("Error detallado al registrar:", error);
    
    // Mensajes de error más específicos
    let mensajeError = "❌ No se pudo registrar el rostro.";
    
    if (error.message.includes("camera")) {
      mensajeError = "❌ Error de cámara. Verifica que la cámara esté disponible y los permisos estén habilitados.";
    } else if (error.message.includes("network")) {
      mensajeError = "❌ Error de conexión. Verifica tu conexión a internet.";
    } else if (error.message.includes("face")) {
      mensajeError = "❌ No se detectó un rostro válido. Asegúrate de estar bien iluminado y mirando a la cámara.";
    } else if (error.message.includes("FaceIO")) {
      mensajeError = "❌ Error de FaceIO. Verifica la configuración.";
    }
    
    alert(mensajeError);
    console.error("Error completo:", error);
  }
};

window.authenticateUser = async function () {
  try {
    console.log("Iniciando autenticación facial...");
    
    if (!faceio) {
      throw new Error("FaceIO no está inicializado");
    }
    
    const userData = await faceio.authenticate({
      locale: "auto"
    });
    console.log("Usuario autenticado:", userData);
    usuarioAutenticado = true;
    document.getElementById("authStatus").innerText = "Autenticado con rostro ✅";
    document.getElementById("btnLogin").style.display = "none";
    document.getElementById("btnLogout").style.display = "block";
  } catch (error) {
    console.error("Error detallado de autenticación:", error);
    
    let mensajeError = "❌ Falló la autenticación facial.";
    
    if (error.message.includes("camera")) {
      mensajeError = "❌ Error de cámara. Verifica que la cámara esté disponible.";
    } else if (error.message.includes("face")) {
      mensajeError = "❌ No se detectó un rostro válido. Asegúrate de estar bien iluminado.";
    } else if (error.message.includes("not found")) {
      mensajeError = "❌ Rostro no registrado. Primero debes registrar tu rostro.";
    }
    
    alert(mensajeError);
    console.error("Error completo:", error);
  }
};

window.logoutUser = function () {
  usuarioAutenticado = false;
  document.getElementById("authStatus").innerText = "";
  document.getElementById("btnLogin").style.display = "block";
  document.getElementById("btnLogout").style.display = "none";
  if (typeof faceio !== "undefined" && faceio._faceioModal) {
    faceio._faceioModal.close();
  }
  faceio = new faceIO("fioa2e2c", {
    container: "#faceio-modal-container"
  });
  alert("👋 Has cerrado sesión correctamente.");
};

// --- Activa la cámara y comienza medición en tiempo real ---
window.activarCamara = async function() {
  try {
    console.log("Solicitando acceso a la cámara...");
    mostrarStatus("Iniciando cámara...", "info");
    
    // Verificar si getUserMedia está disponible
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("getUserMedia no está disponible en este navegador");
    }
    
    // Solicitar acceso a la cámara con configuración más flexible
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: 'environment',
        width: { ideal: 1280, min: 640 },
        height: { ideal: 720, min: 480 }
      } 
    });
    
    console.log("Cámara obtenida exitosamente");
    
    if (!video) {
      throw new Error("Elemento video no encontrado");
    }
    
    video.srcObject = stream;
    video.style.display = 'block';
    
    // Esperar a que el video esté listo
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Timeout al cargar el video"));
      }, 10000); // 10 segundos de timeout
      
      video.addEventListener('loadedmetadata', function() {
        clearTimeout(timeout);
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        console.log(`Video configurado: ${video.videoWidth}x${video.videoHeight}`);
        resolve();
      });
      
      video.addEventListener('error', function() {
        clearTimeout(timeout);
        reject(new Error("Error al cargar el video"));
      });
    });
    
    // Mostrar botones correctamente
    document.getElementById('btnActivarCamara').style.display = 'none';
    document.getElementById('btnDetenerCamara').style.display = 'inline-block';
    mostrarStatus("Cámara activada. Medición en tiempo real...", "success");
    
    // Inicia medición en tiempo real cada 500 ms
    intervaloMedicion = setInterval(() => { medirEnTiempoReal(); }, 500);
    
  } catch (error) {
    console.error("Error detallado al acceder a la cámara:", error);
    
    let mensajeError = "Error al acceder a la cámara. Verifica los permisos.";
    
    if (error.name === 'NotAllowedError') {
      mensajeError = "❌ Permisos de cámara denegados. Por favor, permite el acceso a la cámara en tu navegador.";
    } else if (error.name === 'NotFoundError') {
      mensajeError = "❌ No se encontró ninguna cámara conectada.";
    } else if (error.name === 'NotReadableError') {
      mensajeError = "❌ La cámara está siendo usada por otra aplicación.";
    } else if (error.name === 'OverconstrainedError') {
      mensajeError = "❌ La cámara no soporta la resolución solicitada.";
    } else if (error.message.includes("getUserMedia")) {
      mensajeError = "❌ Tu navegador no soporta acceso a la cámara.";
    } else if (error.message.includes("Timeout")) {
      mensajeError = "❌ Tiempo de espera agotado al cargar la cámara.";
    }
    
    mostrarStatus(mensajeError, "error");
    console.error("Error completo:", error);
    
    // Asegurar que los botones estén en el estado correcto
    document.getElementById('btnActivarCamara').style.display = 'inline-block';
    document.getElementById('btnDetenerCamara').style.display = 'none';
  }
};

// 📸 Capturar y medir
window.capturarYMedir = function() {
  if (!stream) {
    mostrarStatus("Primero activa la cámara.", "error");
    return;
  }
  
  try {
    mostrarStatus("Capturando imagen y detectando códigos ArUco...", "info");
    
    // Dibujar el frame actual en el canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convertir canvas a base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    
    // Obtener el tamaño real del lado del marcador ingresado por el usuario
    const tamanoLadoCm = parseFloat(document.getElementById('tamanoLado').value) || 5;
    const tamanoLado = tamanoLadoCm / 100.0;
    
    // Enviar al servidor para detección de ArUco
    detectarArUco(imageData, tamanoLado);
    
  } catch (error) {
    console.error('Error al capturar:', error);
    mostrarStatus("Error al capturar la imagen.", "error");
  }
};

// ⏹️ Detener cámara
window.detenerCamara = function() {
  console.log("Deteniendo cámara...");
  
  // Detener medición en tiempo real primero
  if (intervaloMedicion) {
    clearInterval(intervaloMedicion);
    intervaloMedicion = null;
  }
  
  // Detener el stream de la cámara
  if (stream) {
    stream.getTracks().forEach(track => {
      track.stop();
      console.log("Track detenido:", track.kind);
    });
    stream = null;
  }
  
  // Ocultar elementos de video
  if (video) {
    video.srcObject = null;
    video.style.display = 'none';
  }
  
  if (canvas) {
    canvas.style.display = 'none';
  }
  
  // Restaurar botones al estado inicial
  document.getElementById('btnActivarCamara').style.display = 'inline-block';
  document.getElementById('btnDetenerCamara').style.display = 'none';
  
  mostrarStatus("Cámara detenida.", "info");
  console.log("Cámara detenida correctamente");
};

// --- Captura y envía un frame cada 500 ms para medición en tiempo real ---
function medirEnTiempoReal() {
  if (!stream) return;
  try {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    // Convierte el tamaño del lado de cm a metros
    const tamanoLadoCm = parseFloat(document.getElementById('tamanoLado').value) || 5;
    const tamanoLado = tamanoLadoCm / 100.0;
    detectarArUcoTiempoReal(imageData, tamanoLado);
  } catch (error) {
    mostrarStatus("Error en medición en tiempo real.", "error");
  }
}

// 🔄 Cambiar modo de medición
window.toggleMeasurementMode = function() {
  modoCamara = !modoCamara;
  
  const cameraSection = document.querySelector('.camera-section');
  const manualSection = document.querySelector('.manual-section');
  const toggleBtn = document.querySelector('.toggle-btn');
  
  if (modoCamara) {
    cameraSection.style.display = 'block';
    manualSection.style.display = 'none';
    toggleBtn.textContent = '🔄 Cambiar a Medición Manual';
    
    // Detener cámara si está activa
    if (stream) {
      detenerCamara();
    }
  } else {
    cameraSection.style.display = 'none';
    manualSection.style.display = 'block';
    toggleBtn.textContent = '📷 Cambiar a Medición con Cámara';
  }
};

// Detectar códigos ArUco en el servidor
async function detectarArUco(imageData, tamanoLado) {
  try {
    const response = await fetch('/detectar_aruco', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image: imageData,
        tamano_lado: tamanoLado
      })
    });
    
    const data = await response.json();
    
    if (data.error) {
      mostrarStatus(data.error, "error");
      return;
    }
    
    if (data.success) {
      // Mostrar resultados
      document.getElementById('baseDetectada').textContent = data.base;
      document.getElementById('alturaDetectada').textContent = data.altura;
      document.getElementById('areaDetectada').textContent = data.area;
      
      document.getElementById('measurementResults').style.display = 'block';
      
      // Llenar campos manuales automáticamente
      document.getElementById('base').value = data.base;
      document.getElementById('altura').value = data.altura;
      
      mostrarStatus(`Medición exitosa: ${data.base}m x ${data.altura}m = ${data.area}m²`, "success");
      
      // Detener cámara después de medición exitosa
      setTimeout(() => {
        detenerCamara();
      }, 2000);
    }
    
  } catch (error) {
    console.error('Error al detectar ArUco:', error);
    mostrarStatus("Error al procesar la imagen en el servidor.", "error");
  }
}

// --- Envía el frame al backend y actualiza los resultados en la web ---
async function detectarArUcoTiempoReal(imageData, tamanoLado) {
  try {
    const response = await fetch('/detectar_aruco', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: imageData, tamano_lado: tamanoLado })
    });
    const data = await response.json();
    if (data.error) {
      mostrarStatus(data.error, "error");
      document.getElementById('measurementResults').style.display = 'none';
      return;
    }
    if (data.success) {
      // Guardar la distancia medida
      distanciaGuardada = data.distancia;
      
      // Mostrar resultados
      document.getElementById('distanciaDetectada').textContent = data.distancia;
      document.getElementById('areaDetectada').textContent = data.area;
      document.getElementById('measurementResults').style.display = 'block';
      
      // Llenar campo manual automáticamente
      document.getElementById('distancia').value = data.distancia;
      
      mostrarStatus(`Distancia medida: ${data.distancia} m | Área: ${data.area} m²`, "success");
      
      // Detener cámara automáticamente después de 2 segundos
      setTimeout(() => {
        detenerCamara();
        mostrarStatus("Medición completada. Cámara cerrada automáticamente.", "success");
      }, 2000);
    }
  } catch (error) {
    mostrarStatus("Error al procesar la imagen en el servidor.", "error");
  }
}

// --- Muestra mensajes de estado en la interfaz ---
function mostrarStatus(mensaje, tipo) {
  const statusElement = document.getElementById('cameraStatus');
  statusElement.textContent = mensaje;
  statusElement.className = `status-message ${tipo}`;
}

// 💡 Calcular luminarias
window.calcularLuminarias = function () {
  if (!usuarioAutenticado) {
    alert("❌ Debes autenticarte con tu rostro antes de usar la calculadora.");
    return;
  }

  let distancia;
  
  if (modoCamara) {
    // Usar distancia detectada por cámara
    if (!distanciaGuardada) {
      alert("Primero debes medir la distancia con la cámara.");
      return;
    }
    distancia = distanciaGuardada;
  } else {
    // Usar distancia manual
    distancia = parseFloat(document.getElementById('distancia').value);
  }

  if (isNaN(distancia) || distancia <= 0) {
    alert("Por favor, ingresa una distancia válida mayor que 0.");
    return;
  }

  fetch(`/generar?distancia=${distancia}`)
    .then(res => res.json())
    .then(data => {
      if (data.error) throw new Error(data.error);

      document.getElementById('area').innerText = data.area;
      document.getElementById('nl').innerText = data.nl;
      document.getElementById('x').innerText = data.x;
      document.getElementById('y').innerText = data.y;
      document.getElementById('totalDistribuido').innerText = data.total;
      document.getElementById('imagenDistribucion').innerHTML = `
        <img src="${data.image_url}" alt="Distribución de luminarias" />
      `;
      document.getElementById('resultado').classList.remove("hidden");
    })
    .catch(err => {
      document.getElementById('resultado').classList.remove("hidden");
      document.getElementById('imagenDistribucion').innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    });
};
