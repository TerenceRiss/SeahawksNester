import tkinter as tk
from tkinter import scrolledtext, messagebox
import nmap
import json
import requests

API_TOKEN = "my_secret_api_token"

def perform_scan():
    # Obtenir la plage IP de l'entrée utilisateur
    network_range = ip_entry.get()
    if not network_range:
        messagebox.showerror("Erreur", "Veuillez entrer une plage IP.")
        return

    try:
        # Initialiser le scanner Nmap
        nm = nmap.PortScanner()
        result_area.insert(tk.END, f"Scan en cours pour : {network_range}...\n")
        result_area.see(tk.END)
        scan_result = nm.scan(hosts=network_range, arguments='-sn')

        hosts = []
        for host in nm.all_hosts():
            state = nm[host].state()
            hostname = nm[host].hostname()
            hosts.append({
                "ip": host,
                "hostname": hostname,
                "state": state
            })
            result_area.insert(tk.END, f"Host : {host} ({hostname}) - State : {state}\n")
            result_area.see(tk.END)

        # Sauvegarder les résultats dans un fichier JSON
        with open("scan_results.json", "w") as f:
            json.dump(hosts, f, indent=4)

        result_area.insert(tk.END, "Résultats sauvegardés dans 'scan_results.json'.\n")

        # Envoyer les résultats au serveur
        send_to_server(hosts)
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur pendant le scan : {e}")

def send_to_server(data):
    server_url = "http://127.0.0.1:5000/receive-data"  # URL du serveur
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        result_area.insert(tk.END, "Envoi des données au serveur...\n")
        response = requests.post(server_url, json=data, headers=headers)
        if response.status_code == 200:
            result_area.insert(tk.END, f"Réponse du serveur : {response.json()}\n")
        elif response.status_code == 401:
            result_area.insert(tk.END, "Erreur : Non autorisé. Vérifiez le token.\n")
        else:
            result_area.insert(tk.END, f"Erreur lors de l'envoi des données : {response.status_code}\n")
    except Exception as e:
        result_area.insert(tk.END, f"Erreur lors de la connexion au serveur : {e}\n")

# Création de la fenêtre principale
root = tk.Tk()
root.title("Seahawks Harvester - Interface Graphique")

# Zone d'entrée pour la plage IP
tk.Label(root, text="Plage IP à scanner :").grid(row=0, column=0, padx=10, pady=5, sticky="w")
ip_entry = tk.Entry(root, width=30)
ip_entry.grid(row=0, column=1, padx=10, pady=5)

# Bouton pour lancer le scan
scan_button = tk.Button(root, text="Démarrer le Scan", command=perform_scan)
scan_button.grid(row=0, column=2, padx=10, pady=5)

# Zone de texte pour afficher les résultats
tk.Label(root, text="Résultats du scan :").grid(row=1, column=0, padx=10, pady=5, sticky="w")
result_area = scrolledtext.ScrolledText(root, width=80, height=20)
result_area.grid(row=2, column=0, columnspan=3, padx=10, pady=5)

# Lancer l'interface graphique
root.mainloop()
