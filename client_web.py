from flask import Flask, render_template, request, redirect, url_for, session, flash
import nmap
import json
import requests
from ping3 import ping

app = Flask(__name__)
app.secret_key = "super_secret_key"

API_TOKEN = "my_secret_api_token"
SERVER_URL = "http://127.0.0.1:5000"
SCAN_URL = f"{SERVER_URL}/receive-data"
LOGIN_URL = f"{SERVER_URL}/login"
REGISTER_URL = f"{SERVER_URL}/register"
APP_VERSION = "1.0.0"


def measure_latency():
    """Mesurer la latence WAN en pingant une cible externe."""
    target = "8.8.8.8"  # Adresse cible pour le test de latence
    try:
        latency = ping(target, timeout=2)
        if latency is not None:
            latency_ms = round(latency * 1000, 2)  # Conversion en millisecondes
            return latency_ms
        else:
            return "Indisponible"
    except Exception as e:
        print(f"Erreur lors de la mesure de latence : {e}")
        return "Erreur"

@app.route('/')
def home():
    if 'token' in session:
        return redirect(url_for('scan_form'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Veuillez entrer un nom d'utilisateur et un mot de passe.", "error")
            return redirect(url_for('login'))

        # Appeler l'API de connexion
        try:
            response = requests.post(LOGIN_URL, json={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                session['token'] = data['token']
                session['username'] = username
                flash("Connexion réussie !", "success")
                return redirect(url_for('scan_form'))
            else:
                flash("Identifiants incorrects.", "error")
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erreur lors de la connexion : {e}", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Veuillez entrer un nom d'utilisateur et un mot de passe.", "error")
            return redirect(url_for('register'))

        # Appeler l'API d'enregistrement
        try:
            response = requests.post(REGISTER_URL, json={"username": username, "password": password})
            if response.status_code == 201:
                flash("Inscription réussie ! Veuillez vous connecter.", "success")
                return redirect(url_for('login'))
            else:
                flash("Nom d'utilisateur déjà utilisé.", "error")
                return redirect(url_for('register'))
        except Exception as e:
            flash(f"Erreur lors de l'inscription : {e}", "error")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('token', None)  # Supprimer le token de la session
    session.pop('username', None)  # Supprimer le nom d'utilisateur
    return redirect(url_for('login'))  # Rediriger vers la page de connexion

@app.route('/scan', methods=['GET', 'POST'])
def scan_form():
    if 'token' not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        network_range = request.form.get('network_range')
        ports = request.form.get('ports', '22,80,443,3389').replace(" ", "")  # Ports par défaut

        if not network_range:
            flash("Veuillez entrer une plage IP.", "error")
            return render_template('index.html')

        if not ports:
            flash("Veuillez spécifier les ports à scanner.", "error")
            return render_template('index.html')

        try:
            # Lancer le scan
            nm = nmap.PortScanner()
            scan_command = f"-sS -p {ports}"
            scan_result = nm.scan(hosts=network_range, arguments=scan_command)
            hosts = []
            for host in nm.all_hosts():
                state = nm[host].state()
                hostname = nm[host].hostname()
                ports_list = []
                if "tcp" in nm[host]:
                    for port, port_data in nm[host]["tcp"].items():
                        ports_list.append(f"{port}/{port_data['name']}")
                hosts.append({
                    "ip": host,
                    "hostname": hostname or "Unknown",
                    "state": state,
                    "ports": ports_list
                })

            # Mesurer la latence WAN
            latency = measure_latency()

            # Sauvegarder les résultats localement
            results = {"hosts": hosts, "latency_ms": latency}
            with open("scan_results_web.json", "w") as f:
                json.dump(results, f, indent=4)

            # Envoyer les résultats au serveur principal
            headers = {"x-access-token": session['token']}
            response = requests.post(SCAN_URL, json=results, headers=headers)
            if response.status_code != 200:
                flash("Erreur lors de l'envoi des résultats au serveur.", "error")
                return render_template('index.html')

            # Passer les résultats au template
            return render_template(
                'results.html',
                hosts=hosts,
                network_range=network_range,
                latency_ms=latency
            )
        except requests.exceptions.ConnectionError:
            flash("Impossible de se connecter au serveur.", "error")
            return render_template('index.html')
        except Exception as e:
            flash(f"Erreur pendant le scan : {e}", "error")
            return render_template('index.html')

    return render_template('index.html', app_version=APP_VERSION)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
