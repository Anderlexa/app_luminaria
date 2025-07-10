// Espera a que cargue el DOM para evitar errores de sincronización
document.addEventListener("DOMContentLoaded", function () {
  let faceio = new faceIO("fioa2e2c", {
    container: "#faceio-modal-container"
  });

  let usuarioAutenticado = false;

  // 🔐 Registrar usuario con FaceIO
  window.enrollUser = async function () {
    try {
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
      console.error("Error al registrar:", error);
      alert("❌ No se pudo registrar el rostro.");
    }
  };

  // ✅ Autenticar usuario con FaceIO
  window.authenticateUser = async function () {
    try {
      const userData = await faceio.authenticate({
        locale: "auto"
      });
      console.log("Usuario autenticado:", userData);
      usuarioAutenticado = true;
      document.getElementById("authStatus").innerText = "Autenticado con rostro ✅";
      
      // Ocultar el botón de "Iniciar con Rostro" y mostrar "Cerrar sesión"
      document.getElementById("btnLogin").style.display = "none";
      document.getElementById("btnLogout").style.display = "block";
    } catch (error) {
      console.error("Error de autenticación:", error);
      alert("❌ Falló la autenticación facial.");
    }
  };
// 🚪 Cerrar sesión
window.logoutUser = function () {
  // Resetear el estado de autenticación
  usuarioAutenticado = false;

  // Limpiar mensaje de autenticación
  document.getElementById("authStatus").innerText = "";

  // Mostrar el botón de "Autenticar" y ocultar "Cerrar sesión"
  document.getElementById("btnLogin").style.display = "block";
  document.getElementById("btnLogout").style.display = "none";

  // Opcional: Si FaceIO no tiene un método de limpiar sesión, podemos simplemente 
  // cerrar cualquier modal o componente de FaceIO si está abierto
  if (typeof faceio !== "undefined" && faceio._faceioModal) {
    faceio._faceioModal.close(); // Esto cerrará el modal de FaceIO si está abierto
  }

  // Re-crear la instancia de faceio para que no queden "residuos" de la sesión anterior
  faceio = new faceIO("fioa4456", {
    container: "#faceio-modal-container"
  });

  alert("👋 Has cerrado sesión correctamente.");
};


  // 💡 Calcular luminarias si el usuario fue autenticado
  window.calcularLuminarias = function () {
    if (!usuarioAutenticado) {
      alert("❌ Debes autenticarte con tu rostro antes de usar la calculadora.");
      return;
    }

    const base = parseFloat(document.getElementById('base').value);
    const altura = parseFloat(document.getElementById('altura').value);

    if (isNaN(base) || isNaN(altura) || base <= 0 || altura <= 0) {
      alert("Por favor, ingresa valores válidos para base y altura.");
      return;
    }

    fetch(`/generar?base=${base}&altura=${altura}`)
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
});