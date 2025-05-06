from flask import Flask, jsonify
import json
import os
from scraper import main

app = Flask(__name__)


app.json.sort_keys = False  # Pour garder l'ordre des clés dans le JSON
app.json.ensure_ascii = False  # Pour garder les caractères spéciaux (accents, etc.)


# Route pour récupérer les données JSON
@app.route("/api/listes", methods=["GET"])
def get_listes():
    try:
        # Exécuter le script pour s'assurer que les données sont à jour
        print("Exécution du script de scraping...")
        main()

        # Charger le fichier JSON mis à jour
        with open("data/listes_choisir_offrir.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
