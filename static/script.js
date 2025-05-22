function calcularLuminarias() {
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
}