from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from calcular_luminarias import calcular_y_generar_imagen
import os

app = Flask(__name__)
CORS(app)  # 👈 habilita CORS globalmente

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generar")
def generar():
    try:
        base = float(request.args.get("base", 0))
        altura = float(request.args.get("altura", 0))

        if base <= 0 or altura <= 0:
            return jsonify({"error": "Base y altura deben ser mayores que 0."})

        resultado = calcular_y_generar_imagen(base, altura)

        return jsonify({
            "area": resultado["area"],
            "nl": resultado["nl"],
            "x": resultado["x"],
            "y": resultado["y"],
            "total": resultado["total"],
            "image_url": url_for("static", filename=os.path.basename(resultado["image_path"]))
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
