from flask import Flask, request, jsonify
from database import init_db, insert_data, fetch_data
from prometheus_client import Counter, generate_latest, CollectorRegistry, Gauge
import json
import logging

app = Flask(__name__)

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    filename="server_logs.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Clé API pour sécuriser l'accès
API_TOKEN = "my_secret_api_token"

# Initialisation des métriques Prometheus
registry = CollectorRegistry()
scan_requests_total = Counter('scan_requests_total', 'Nombre total de requêtes de scan', registry=registry)
hosts_up_total = Gauge('hosts_up_total', 'Nombre total d\'hôtes en état "up"', registry=registry)
hosts_down_total = Gauge('hosts_down_total', 'Nombre total d\'hôtes en état "down"', registry=registry)

# Fonction utilitaire pour vérifier le token
def authenticate(request):
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_TOKEN}":
        logging.warning("Échec de l'authentification avec le token.")
        return False
    return True

# Route pour vérifier si le serveur fonctionne
@app.route("/")
def home():
    logging.info("Requête GET sur la route /")
    return "Seahawks Nester Server is running!"

# Route pour recevoir les données scannées
@app.route("/receive-data", methods=["POST"])
def receive_data():
    if not authenticate(request):
        logging.warning("Requête non autorisée sur /receive-data.")
        return jsonify({"message": "Non autorisé", "status": "error"}), 401

    try:
        data = request.get_json()
        logging.info(f"Données reçues : {data}")
        insert_data(data)

        # Mise à jour des métriques
        scan_requests_total.inc()
        hosts_up = len([host for host in data if host.get("state") == "up"])
        hosts_down = len([host for host in data if host.get("state") == "down"])
        hosts_up_total.set(hosts_up)
        hosts_down_total.set(hosts_down)

        logging.info("Données sauvegardées avec succès dans la base.")
        return jsonify({"message": "Données reçues et sauvegardées avec succès!", "status": "success"}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la réception des données : {e}")
        return jsonify({"message": "Erreur lors de la réception des données", "status": "error"}), 500

# Route pour afficher les métriques Prometheus
@app.route("/metrics", methods=["GET"])
def metrics():
    try:
        logging.info("Requête GET sur la route /metrics")
        return generate_latest(registry), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        logging.error(f"Erreur lors de la génération des métriques : {e}")
        return jsonify({"message": "Erreur lors de la génération des métriques", "status": "error"}), 500

# Route pour afficher les données enregistrées
@app.route("/view-data", methods=["GET"])
def view_data():
    try:
        state_filter = request.args.get("state")
        ip_filter = request.args.get("ip")

        rows = fetch_data()
        if state_filter:
            rows = [row for row in rows if row[3] == state_filter]
        if ip_filter:
            rows = [row for row in rows if row[1].startswith(ip_filter)]

        # Calcul des métriques pour les graphiques
        total_up = len([row for row in rows if row[3] == "up"])
        total_down = len([row for row in rows if row[3] == "down"])
        ip_distribution = {}
        for row in rows:
            ip_prefix = ".".join(row[1].split(".")[:3])
            ip_distribution[ip_prefix] = ip_distribution.get(ip_prefix, 0) + 1

        logging.info("Données pour /view-data récupérées avec succès.")

        # Conversion des données pour Chart.js
        ip_labels_json = json.dumps(list(ip_distribution.keys()))
        ip_data_json = json.dumps(list(ip_distribution.values()))
        total_up_json = json.dumps(total_up)  # Conversion sécurisée
        print(f'total_up_json: {total_up_json}')
        total_down_json = json.dumps(total_down)  # Conversion sécurisée

        # Génération du HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <div class="container">
                <h1>Données scannées</h1>
                <form method="GET" action="/view-data" class="mb-4">
                    <div class="row g-3">
                        <div class="col">
                            <input type="text" name="ip" class="form-control" placeholder="Plage IP (ex: 192.168.0.)" value="{ip_filter or ''}">
                        </div>
                        <div class="col">
                            <select name="state" class="form-control">
                                <option value="">Tous les états</option>
                                <option value="up" {'selected' if state_filter == 'up' else ''}>Up</option>
                                <option value="down" {'selected' if state_filter == 'down' else ''}>Down</option>
                            </select>
                        </div>
                        <div class="col">
                            <button type="submit" class="btn btn-primary">Filtrer</button>
                        </div>
                    </div>
                </form>

                <!-- Graphiques -->
                <div class="row">
                    <div class="col-md-6">
                        <h3>Proportion d'hôtes Up vs Down</h3>
                        <canvas id="stateChart"></canvas>
                    </div>
                    <div class="col-md-6">
                        <h3>Répartition des plages IP</h3>
                        <canvas id="ipChart"></canvas>
                    </div>
                </div>

                <!-- Tableau des données -->
                <h2>Tableau des données</h2>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>IP</th>
                            <th>Hostname</th>
                            <th>State</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for row in rows:
            html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
        html += """
                    </tbody>
                </table>
            </div>

            <!-- Script pour les graphiques -->
            <script>
        """
        html+=f'const totalUp = {total_up_json};'  
        html+=f'const totalDown = {total_down_json};'  
        html+=f'const ipLabels = {ip_labels_json};'
        html+=f'const ipData = {ip_data_json};'
        html+="""
                // Graphique d'état
                const pieChart = document.getElementById('stateChart')
                console.log(pieChart)
                new Chart(pieChart, {
                    type: 'pie',
                    data: {
                        labels: ['Up', 'Down'],
                        datasets: [{
                            label: "Nombre d'hôtes",
                            data: [totalUp, totalDown],
                            backgroundColor: ['#36A2EB', '#FF6384'],
                        }]
                    }
                });

                // Graphique des plages IP
                new Chart(document.getElementById('ipChart'), {
                    type: 'bar',
                    data: {
                        labels: ipLabels,
                        datasets: [{
                            label: "Nombre d'hôtes par plage IP",
                            data: ipData,
                            backgroundColor: '#FFCE56',
                        }]
                    }
                });
            </script>
        </body>
        </html>
        """
        return html
    except Exception as e:
        logging.error(f"Erreur lors de la génération des données pour /view-data : {e}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500

if __name__ == "__main__":
    init_db()
    logging.info("Serveur Flask démarré.")
    app.run(debug=True, host="0.0.0.0", port=5000)
