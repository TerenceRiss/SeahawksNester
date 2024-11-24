import sqlite3

# Fonction pour initialiser la base de données
def init_db():
    conn = sqlite3.connect("seahawks.db")  # Crée un fichier SQLite nommé seahawks.db
    cursor = conn.cursor()

    # Crée une table pour stocker les données scannées
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            hostname TEXT,
            state TEXT
        )
    """)
    conn.commit()
    conn.close()

# Fonction pour insérer des données dans la table
def insert_data(scan_data):
    conn = sqlite3.connect("seahawks.db")
    cursor = conn.cursor()

    # Insérer chaque hôte scanné dans la table
    for host in scan_data:
        cursor.execute("""
            INSERT INTO scan_results (ip, hostname, state) 
            VALUES (?, ?, ?)
        """, (host["ip"], host["hostname"], host["state"]))
    
    conn.commit()
    conn.close()

# Fonction pour récupérer les données de la base
def fetch_data():
    conn = sqlite3.connect("seahawks.db")
    cursor = conn.cursor()

    # Récupérer toutes les données
    cursor.execute("SELECT * FROM scan_results")
    rows = cursor.fetchall()

    conn.close()
    return rows
