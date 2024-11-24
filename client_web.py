from flask import Flask, render_template, request
import nmap
import json
import requests

app = Flask(__name__)

API_TOKEN = "my_secret_api_token"
SERVER_URL = "http://127.0.0.1:5000/receive-data"

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
        scan_result = nm.scan(hosts=network_range, arguments='-sn')
        hosts = []

        for host in nm.all_hosts():
            state = nm[host].state()
            hostname = nm[host].hostname()
            hosts.append({
                "ip": host,
                "hostname": hostname or "Non défini",
                "state": state
            })

        # Envoyer au serveur principal
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.post(SERVER_URL, json=hosts, headers=headers)
        if response.status_code != 200:
            return render_template('error.html', message="Erreur lors de l'envoi au serveur.")

        # Passer les résultats au template
        return render_template('results.html', hosts=hosts, network_range=network_range)

    except Exception as e:
        return render_template('error.html', message=str(e))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

