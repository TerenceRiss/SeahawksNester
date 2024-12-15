from flask import Flask, request, jsonify, render_template, session
from database import init_db, fetch_hosts, sync_inventory, get_scan_trends, fetch_top_ports
from prometheus_client import Counter, generate_latest, CollectorRegistry, Gauge
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import json
import logging
import nmap
import sqlite3
from functools import wraps

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)
app.config['SECRET_KEY'] = 'my_secret_key'

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

# Fonction utilitaire pour vérifier le token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token manquant !'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except Exception as e:
            return jsonify({'message': 'Token invalide !'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Fonction pour effectuer un scan réseau
def perform_scan(network_range, port_argument):
    try:
        nm = nmap.PortScanner()
        scan_results = nm.scan(hosts=network_range, arguments=f"-sS {port_argument}")
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

# Route pour l'inscription des utilisateurs
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Nom d'utilisateur et mot de passe requis"}), 400
    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect("seahawks.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return jsonify({"message": "Utilisateur enregistré avec succès"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Nom d'utilisateur déjà utilisé"}), 400
    finally:
        conn.close()

# Route pour la connexion des utilisateurs
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Nom d'utilisateur et mot de passe requis"}), 400
    conn = sqlite3.connect("seahawks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[0], password):
        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"token": token})
    return jsonify({"message": "Identifiants incorrects"}), 401

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

        # Récupération des tendances des scans
        scan_trends = get_scan_trends()
        timestamps = [trend["timestamp"] for trend in scan_trends]
        up_counts = [trend["up_count"] for trend in scan_trends]
        down_counts = [trend["down_count"] for trend in scan_trends]

        # Récupération des ports les plus utilisés
        top_ports = fetch_top_ports(limit=5)
        port_labels = [f"{item['port']} ({item['service']})" for item in top_ports]
        port_data = [item['count'] for item in top_ports]

        logging.info(f"Tendances : {scan_trends}")
        return render_template(
            "view_data.html",
            rows=rows,
            total_up=json.dumps(total_up),
            total_down=json.dumps(total_down),
            ip_labels_json=json.dumps(list(ip_distribution.keys())),
            ip_data_json=json.dumps(list(ip_distribution.values())),
            scan_trends_labels=json.dumps(timestamps),
            scan_trends_up=json.dumps(up_counts),
            scan_trends_down=json.dumps(down_counts),
            port_labels_json=json.dumps(port_labels),
            port_data_json=json.dumps(port_data),
            state_filter=state_filter,
            ip_filter=ip_filter,
        )
    except Exception as e:
        logging.error(f"Erreur lors de la génération des données pour /view-data : {e}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500
    
# Route protégée pour recevoir les données scannées
@app.route("/receive-data", methods=["POST"])
@token_required
def receive_data(current_user):
    try:
        data = request.get_json()
        logging.info(f"Données reçues par {current_user} : {data}")
        sync_inventory(data.get("hosts", []))
        scan_requests_total.inc()
        hosts_up = len([host for host in data.get("hosts", []) if host.get("state") == "up"])
        hosts_down = len([host for host in data.get("hosts", []) if host.get("state") == "down"])
        hosts_up_total.set(hosts_up)
        hosts_down_total.set(hosts_down)
        return jsonify({"message": "Données sauvegardées", "status": "success"}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la réception des données : {e}")
        return jsonify({"message": "Erreur interne du serveur"}), 500

if __name__ == "__main__":
    init_db()
    logging.info("Serveur Flask démarré.")
    app.run(debug=True, host="0.0.0.0", port=5000)
