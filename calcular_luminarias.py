import numpy as np
import matplotlib.pyplot as plt
import os

def calcular_y_generar_imagen(distancia):
    # Parámetros
    LUXES = 500
    LUMEN = 1600
    FM = 0.8

    # Para un espacio cuadrado, base = altura = distancia
    base = distancia
    altura = distancia

    # Cálculos
    area = base * altura
    nl = (LUXES * area) / (LUMEN * FM)

    y = np.round(np.sqrt((altura * nl) / base)).astype(int)
    x = np.round((base * y) / altura).astype(int)
    total = x * y

    # Generar coordenadas
    x_coords = np.linspace(base/(2*x), base - base/(2*x), x)
    y_coords = np.linspace(altura/(2*y), altura - altura/(2*y), y)
    X, Y = np.meshgrid(x_coords, y_coords)

    # Crear imagen
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(0, base)
    ax.set_ylim(0, altura)
    ax.add_patch(plt.Rectangle((0, 0), base, altura, fill=False, linewidth=2))
    ax.plot(X, Y, 'ro')
    ax.set_title("Distribución de luminarias en el área")
    ax.set_xlabel("Distancia (m)")
    ax.set_ylabel("Distancia (m)")
    ax.grid(True)

    # Guardar imagen
    if not os.path.exists("static"):
        os.makedirs("static")
    filename = f"static/luminarias_{int(distancia*100)}cm.png"
    plt.savefig(filename)
    plt.close()

    return {
    "area": round(float(area), 2),
    "nl": round(float(nl), 2),
    "x": int(x),
    "y": int(y),
    "total": int(total),
    "image_path": filename
    }

