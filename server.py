from flask import Flask, request, jsonify, render_template
from database import init_db, fetch_hosts, sync_inventory, get_scan_trends, fetch_top_ports
from prometheus_client import Counter, generate_latest, CollectorRegistry, Gauge
import json
import logging
import nmap

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    filename="server_logs.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Clé API pour sécuriser l'accès
API_TOKEN = "my_secret_api_token"

# Initialisation des métriques Prometheus
registry = CollectorRegistry()
scan_requests_total = Counter(
    "scan_requests_total", "Nombre total de requêtes de scan", registry=registry
)
hosts_up_total = Gauge(
    "hosts_up_total", 'Nombre total d\'hôtes en état "up"', registry=registry
)
hosts_down_total = Gauge(
    "hosts_down_total", 'Nombre total d\'hôtes en état "down"', registry=registry
)

# Fonction utilitaire pour vérifier le token
def authenticate(request):
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_TOKEN}":
        logging.warning("Échec de l'authentification avec le token.")
        return False
    return True

# Fonction pour effectuer un scan réseau
def perform_scan(network_range, port_argument):
    """
    Effectue un scan réseau en utilisant nmap.
    """
    try:
        # Initialiser le scanner Nmap
        nm = nmap.PortScanner()

        # Lancer le scan
        scan_results = nm.scan(hosts=network_range, arguments=f"-sS {port_argument}")

        # Parser les résultats du scan
        hosts = []
        for host in nm.all_hosts():
            state = nm[host].state()
            hostname = nm[host].hostname()
            ports = []
            if "tcp" in nm[host]:
                for port, port_data in nm[host]["tcp"].items():
                    ports.append(f"{port}/{port_data['name']}")
            hosts.append({
                "ip": host,
                "hostname": hostname or "Unknown",
                "state": state,
                "ports": ports,
            })

        return hosts
    except Exception as e:
        logging.error(f"Erreur lors du scan Nmap : {e}")
        raise RuntimeError(f"Impossible de réaliser le scan : {e}")

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

        # Synchroniser les résultats des scans
        sync_inventory(data.get("hosts", []))

        # Mise à jour des métriques
        scan_requests_total.inc()
        hosts_up = len([host for host in data.get("hosts", []) if host.get("state") == "up"])
        hosts_down = len([host for host in data.get("hosts", []) if host.get("state") == "down"])
        hosts_up_total.set(hosts_up)
        hosts_down_total.set(hosts_down)

        logging.info("Données synchronisées et sauvegardées avec succès.")
        return jsonify({"message": "Données reçues et sauvegardées avec succès!", "status": "success"}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la réception des données : {e}")
        return jsonify({"message": "Erreur lors de la réception des données", "status": "error"}), 500

# Route pour afficher les métriques Prometheus
@app.route("/metrics", methods=["GET"])
def metrics():
    try:
        logging.info("Requête GET sur la route /metrics")
        return generate_latest(registry), 200, {"Content-Type": "text/plain; charset=utf-8"}
    except Exception as e:
        logging.error(f"Erreur lors de la génération des métriques : {e}")
        return jsonify({"message": "Erreur lors de la génération des métriques", "status": "error"}), 500

# Route pour lancer un scan avec des options personnalisées
@app.route("/scan", methods=["POST"])
def scan():
    try:
        # Récupérer les informations du formulaire
        network_range = request.form.get("network_range")
        ports = request.form.get("ports", "22,80,443").replace(" ", "")

        if not network_range:
            return render_template("error.html", message="Plage IP non spécifiée.")

        # Préparer l'argument des ports
        port_argument = f"-p {ports}"

        logging.info(f"Scan lancé sur {network_range} avec les ports {ports}")

        # Lancer le scan
        scan_results = perform_scan(network_range, port_argument)

        logging.info(f"Résultats du scan : {scan_results}")

        # Synchroniser l'inventaire
        sync_inventory(scan_results)

        return render_template("results.html", hosts=scan_results, network_range=network_range)
    except Exception as e:
        logging.error(f"Erreur lors du scan : {e}")
        return render_template("error.html", message=f"Erreur : {str(e)}")

# Route pour afficher les données enregistrées
@app.route("/view-data", methods=["GET"])
def view_data():
    try:
        state_filter = request.args.get("state")
        ip_filter = request.args.get("ip")

        rows = fetch_hosts()
        if state_filter:
            rows = [row for row in rows if row["state"] == state_filter]
        if ip_filter:
            rows = [row for row in rows if row["ip"].startswith(ip_filter)]

        # Calcul des métriques pour les graphiques
        total_up = len([row for row in rows if row["state"] == "up"])
        total_down = len([row for row in rows if row["state"] == "down"])
        ip_distribution = {}
        for row in rows:
            ip_prefix = ".".join(row["ip"].split(".")[:3])
            ip_distribution[ip_prefix] = ip_distribution.get(ip_prefix, 0) + 1

        # Récupération des ports les plus utilisés
        top_ports = fetch_top_ports(limit=5)
        port_labels = [f"{item['port']} ({item['service']})" for item in top_ports]
        port_data = [item['count'] for item in top_ports]

        logging.info(f"Données récupérées pour le tableau: {rows}")
        logging.info(f"Distribution IP : {ip_distribution}")
        logging.info(f"Ports les plus utilisés : {top_ports}")

        return render_template(
            "view_data.html",
            rows=rows,
            total_up=json.dumps(total_up),
            total_down=json.dumps(total_down),
            ip_labels_json=json.dumps(list(ip_distribution.keys())),
            ip_data_json=json.dumps(list(ip_distribution.values())),
            port_labels_json=json.dumps(port_labels),
            port_data_json=json.dumps(port_data),
            state_filter=state_filter,
            ip_filter=ip_filter,
        )
    except Exception as e:
        logging.error(f"Erreur lors de la génération des données pour /view-data : {e}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500

if __name__ == "__main__":
    init_db()
    logging.info("Serveur Flask démarré.")
    app.run(debug=True, host="0.0.0.0", port=5000)
