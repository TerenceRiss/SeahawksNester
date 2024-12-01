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
            FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
            FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE
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

    print(f"Scan inséré avec ID : {scan_id}")  # Log pour débogage
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

    print(f"Hôte inséré/mis à jour avec ID : {host_id}")  # Log pour débogage
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

    print(f"Résultat de scan inséré pour scan ID : {scan_id}, host ID : {host_id}")  # Log pour débogage

# Fonction pour synchroniser les résultats d'un scan
def sync_inventory(scan_results):
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

# Fonction pour récupérer tous les hôtes avec leurs derniers états
def fetch_hosts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Récupérer les données jointes des hôtes et leurs résultats
    cursor.execute("""
        SELECT h.id, h.ip, h.hostname, sr.state, sr.ports, s.timestamp
        FROM hosts h
        JOIN scan_results sr ON h.id = sr.host_id
        JOIN scans s ON sr.scan_id = s.id
        WHERE sr.id = (
            SELECT MAX(sr2.id)
            FROM scan_results sr2
            WHERE sr2.host_id = h.id
        )
    """)
    rows = cursor.fetchall()

    conn.close()

    print(f"{len(rows)} hôtes récupérés")  # Log pour débogage
    return [{"id": row[0], "ip": row[1], "hostname": row[2], "state": row[3], "ports": row[4], "last_scan": row[5]} for row in rows]

# Fonction pour compter le nombre total de scans
def count_total_scans():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Compter le nombre total de scans
    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]

    conn.close()

    print(f"Nombre total de scans : {total_scans}")  # Log pour débogage
    return total_scans

# Fonction pour récupérer les tendances des scans
def get_scan_trends():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Obtenir les données des tendances
    cursor.execute("""
        SELECT s.timestamp,
               SUM(CASE WHEN sr.state = 'up' THEN 1 ELSE 0 END) AS up_count,
               SUM(CASE WHEN sr.state = 'down' THEN 1 ELSE 0 END) AS down_count
        FROM scans s
        LEFT JOIN scan_results sr ON s.id = sr.scan_id
        GROUP BY s.id
        ORDER BY s.timestamp
    """)
    trends = cursor.fetchall()

    conn.close()

    print(f"{len(trends)} tendances récupérées")  # Log pour débogage
    return [{"timestamp": row[0], "up_count": row[1], "down_count": row[2]} for row in trends]
