import sqlite3
from datetime import datetime

DB_NAME = "seahawks.db"

# Fonction pour initialiser la base de données
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table pour les scans
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table pour les hôtes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE NOT NULL,
            hostname TEXT
        )
    """)

    # Table pour les résultats des scans
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            host_id INTEGER,
            state TEXT,
            ports TEXT,
            FOREIGN KEY (scan_id) REFERENCES scans(id),
            FOREIGN KEY (host_id) REFERENCES hosts(id)
        )
    """)

    conn.commit()
    conn.close()

# Fonction pour insérer un nouveau scan
def insert_scan():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insérer un nouveau scan et retourner son ID
    cursor.execute("INSERT INTO scans (timestamp) VALUES (?)", (datetime.now(),))
    conn.commit()
    scan_id = cursor.lastrowid
    conn.close()
    return scan_id

# Fonction pour insérer ou mettre à jour un hôte
def insert_or_update_host(ip, hostname):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insérer ou mettre à jour un hôte
    cursor.execute("""
        INSERT INTO hosts (ip, hostname)
        VALUES (?, ?)
        ON CONFLICT(ip) DO UPDATE SET hostname=excluded.hostname
    """, (ip, hostname))
    conn.commit()

    # Récupérer l'ID de l'hôte
    cursor.execute("SELECT id FROM hosts WHERE ip = ?", (ip,))
    host_id = cursor.fetchone()[0]
    conn.close()
    return host_id

# Fonction pour insérer les résultats d'un scan
def insert_scan_result(scan_id, host_id, state, ports):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insérer un résultat de scan
    cursor.execute("""
        INSERT INTO scan_results (scan_id, host_id, state, ports)
        VALUES (?, ?, ?, ?)
    """, (scan_id, host_id, state, ports))
    conn.commit()
    conn.close()

# Fonction pour synchroniser les résultats d'un scan
def sync_inventory(scan_results):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insérer un nouveau scan
    scan_id = insert_scan()

    for result in scan_results:
        # Ajouter ou mettre à jour l'hôte
        host_id = insert_or_update_host(result["ip"], result.get("hostname", "Unknown"))

        # Insérer les résultats du scan
        insert_scan_result(
            scan_id=scan_id,
            host_id=host_id,
            state=result.get("state"),
            ports=", ".join(result.get("ports", []))
        )

    conn.close()

# Fonction pour récupérer tous les hôtes avec leurs derniers états
def fetch_hosts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Récupérer les données jointes des hôtes et leurs résultats
    cursor.execute("""
        SELECT h.ip, h.hostname, sr.state, sr.ports, s.timestamp
        FROM hosts h
        JOIN scan_results sr ON h.id = sr.host_id
        JOIN scans s ON sr.scan_id = s.id
    """)
    rows = cursor.fetchall()

    conn.close()
    return [{"ip": row[0], "hostname": row[1], "state": row[2], "ports": row[3], "last_scan": row[4]} for row in rows]
