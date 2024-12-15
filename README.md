# README - Seahawks Monitoring Project

## Présentation
Le projet **Seahawks Monitoring** est une application Python qui permet d'effectuer des scans réseau, de collecter des données sur les hôtes et les ports ouverts, et de visualiser les résultats via une interface web dynamique basée sur Flask. Cette application inclut des fonctionnalités comme la génération de graphiques, l'enregistrement des données dans une base SQLite, et la possibilité de gérer plusieurs clients.

---

## Initialisation du Projet

### Prérequis
Assurez-vous que les éléments suivants sont installés sur votre machine :

- **Python 3.8+**
- **pip** (installé avec Python)
- **Virtualenv** (optionnel mais recommandé)

### Cloner le projet
Exécutez la commande suivante pour cloner le dépôt GitHub :

```bash
git clone https://github.com/<utilisateur>/<nom_du_depot>.git
cd SeahawksMonitoring
```

---

## Installation des Dépendances

### Avec un environnement virtuel (recommandé)
1. Créez un environnement virtuel :
   ```bash
   python -m venv venv
   ```

2. Activez l'environnement virtuel :
   - Sous **Linux/macOS** :
     ```bash
     source venv/bin/activate
     ```
   - Sous **Windows** :
     ```bash
     .\venv\Scripts\activate
     ```

3. Installez les dépendances listées dans `requirements.txt` :
   ```bash
   pip install -r requirements.txt
   ```

### Sans environnement virtuel
Si vous ne souhaitez pas utiliser un environnement virtuel, installez directement les dépendances avec :

```bash
pip install -r requirements.txt
```

---

## Configuration de l'Application

1. **Initialisation de la base de données** :
   Lancez le fichier `server.py` pour initialiser automatiquement la base SQLite si elle n'existe pas :
   ```bash
   python server.py
   ```

2. **Variables d'environnement** :
   Vous pouvez définir une clé API dans une variable d'environnement pour protéger les appels API. Ajoutez cette ligne dans votre terminal ou fichier `.env` :
   ```bash
   export API_TOKEN=my_secret_api_token
   ```

---

## Lancer le Serveur
1. Assurez-vous d'être dans le répertoire principal du projet.
2. Exécutez le fichier `server.py` pour lancer l'application Flask :
   ```bash
   python server.py
   ```

3. Accédez à l'application via votre navigateur :
   - Adresse par défaut : [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Utilisation

### Interface Web
1. **Scan Réseau** :
   - Entrez une plage IP (par exemple, `192.168.1.0/24`) et les ports à scanner (par défaut : `22,80,443`).
   - Cliquez sur **Lancer le Scan**.

2. **Visualisation** :
   - Consultez les graphiques (hôtes UP/DOWN, distribution des IP, ports les plus utilisés).
   - Les données sont sauvegardées pour une consultation ultérieure.

3. **Métriques Prometheus** :
   - Accédez aux métriques Prometheus à l'adresse : [http://127.0.0.1:5000/metrics](http://127.0.0.1:5000/metrics).

---

## Fonctionnalités Complémentaires

### Dockerisation
Vous pouvez utiliser Docker pour exécuter l'application :

1. **Créez l'image Docker** :
   ```bash
   docker build -t seahawks-monitoring .
   ```

2. **Lancez le conteneur** :
   ```bash
   docker run -d -p 5000:5000 seahawks-monitoring
   ```

3. **Accédez à l'application** :
   - Adresse : [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Tests Unitaires
Exécutez les tests pour vérifier l'intégrité du projet :

```bash
pytest
```

---

## Structure du Projet
Voici l'arborescence principale du projet :

```
SeahawksMonitoring/
|— database.py       # Gestion de la base de données SQLite
|— server.py         # Serveur principal Flask
|— client_wab.py     #Client web pour tester le reseau 
|— templates/        # Modèles HTML pour Flask
|— static/           # Fichiers CSS/JS statiques
|— requirements.txt  # Liste des dépendances
|— README.md         # Documentation du projet
```

---

## Support et Maintenance
- **Documentation** : Consultez le fichier README ou ouvrez une issue sur GitHub.
- **Problèmes connus** :
   - Les scans peuvent être longs pour des plages IP étendues.
   - Les permissions peuvent poser problème sous certains systèmes.

**Contact** : [contact@seahawks-monitoring.com](mailto:rissterence55@gmail.com)

---

## Licence
Ce projet est sous licence MIT. Consultez le fichier LICENSE pour plus d'informations.

