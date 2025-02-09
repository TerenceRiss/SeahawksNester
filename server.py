from flask import Flask, request, jsonify, render_template, session, make_response
from database import init_db, fetch_hosts, sync_inventory, get_scan_trends, fetch_top_ports
from prometheus_client import Counter, generate_latest, CollectorRegistry, Gauge
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import json
import logging
import nmap
import sqlite3
import csv
from io import StringIO
from reportlab.pdfgen import canvas
from functools import wraps
from io import BytesIO 

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
        page = int(request.args.get("page", 1))  # Page actuelle
        per_page = int(request.args.get("per_page", 10))  # Nombre d'éléments par page

        rows = fetch_hosts()
        if state_filter:
            rows = [row for row in rows if row["state"] == state_filter]
        if ip_filter:
            rows = [row for row in rows if row["ip"].startswith(ip_filter)]

        # Pagination
        total_items = len(rows)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_rows = rows[start:end]
        total_pages = (total_items + per_page - 1) // per_page

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
            rows=paginated_rows,
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
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )
    except Exception as e:
        logging.error(f"Erreur lors de la génération des données pour /view-data : {e}")
        return jsonify({"message": "Erreur interne du serveur", "details": str(e)}), 500

#route pour les metrics 
@app.route("/metrics", methods=["GET"])
def metrics():
    try:
        logging.info("Requête GET sur la route /metrics")
        return generate_latest(registry), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        logging.error(f"Erreur lors de la génération des métriques : {e}")
        return jsonify({"message": "Erreur lors de la génération des métriques", "status": "error"}), 500

# Route pour générer un fichier CSV
@app.route("/download-csv", methods=["GET"])
def download_csv():
    rows = fetch_hosts()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "IP", "Hostname", "State", "Ports", "Last Scan"])
    for row in rows:
        writer.writerow([row['id'], row['ip'], row['hostname'], row['state'], row['ports'], row['last_scan']])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=scan_results.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# Route pour générer un fichier PDF
@app.route("/download-pdf", methods=["GET"])
def download_pdf():
    rows = fetch_hosts()
    output = BytesIO()  # Utilisez BytesIO pour écrire des données binaires
    pdf = canvas.Canvas(output)
    pdf.drawString(100, 800, "Rapport des Scans")
    y = 750
    for row in rows:
        pdf.drawString(50, y, f"ID: {row['id']} IP: {row['ip']} State: {row['state']} Ports: {row['ports']}")
        y -= 20
        if y < 50:  # Si la page est pleine
            pdf.showPage()
            y = 750
    pdf.save()
    output.seek(0)  # Réinitialisez le pointeur pour commencer à lire depuis le début

    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=scan_results.pdf"
    response.headers["Content-type"] = "application/pdf"
    return response

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