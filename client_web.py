from flask import Flask, render_template, request
import nmap
import json
import requests
from ping3 import ping

app = Flask(__name__)

API_TOKEN = "my_secret_api_token"
SERVER_URL = "http://127.0.0.1:5000/receive-data"

def measure_latency():
    """Mesurer la latence WAN en pingant une cible externe."""
    target = "8.8.8.8"  # Adresse cible pour le test de latence
    try:
        latency = ping(target, timeout=2)
        if latency is not None:
            latency_ms = round(latency * 1000, 2)  # Conversion en millisecondes
            return latency_ms
        else:
            return None
    except Exception as e:
        print(f"Erreur lors de la mesure de latence : {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    network_range = request.form.get('network_range')
    if not network_range:
        return render_template('error.html', message="Veuillez entrer une plage IP.")

    try:
        # Lancer le scan
        nm = nmap.PortScanner()
        scan_result = nm.scan(hosts=network_range, arguments='-sS -p 22,80,443,3389')  # Scan rapide sur ports spécifiques
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
                "ports": ports
            })

        # Mesurer la latence WAN
        latency = measure_latency()

        # Sauvegarder les résultats localement
        results = {"hosts": hosts, "latency_ms": latency}
        with open("scan_results_web.json", "w") as f:
            json.dump(results, f, indent=4)

        # Envoyer les résultats au serveur principal
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.post(SERVER_URL, json=results, headers=headers)
        if response.status_code != 200:
            return render_template('error.html', message="Erreur lors de l'envoi au serveur.")

        # Passer les résultats au template
        return render_template(
            'results.html',
            hosts=hosts,
            network_range=network_range,
            latency_ms=latency
        )
    except Exception as e:
        return render_template('error.html', message=str(e))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
