import requests
import os
import zipfile
import shutil

# Configuration
GITHUB_API_URL = "https://api.github.com/repos/TerenceRiss/SeahawksNester/releases/latest"
DOWNLOAD_DIR = "./downloads"
EXTRACT_DIR = "./latest_version"
CURRENT_VERSION_FILE = "./current_version.txt"

def get_latest_release():
    """
    Récupère les informations de la dernière release sur GitHub.
    """
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        release_info = response.json()
        return {
            "version": release_info["tag_name"],
            "download_url": release_info["assets"][0]["browser_download_url"]
        }
    except Exception as e:
        print(f"Erreur lors de la récupération de la dernière release : {e}")
        return None

def download_file(url, output_path):
    """
    Télécharge un fichier à partir de l'URL spécifiée.
    """
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
        print(f"Fichier téléchargé : {output_path}")
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")

def extract_zip(zip_path, extract_to):
    """
    Extrait un fichier ZIP vers un répertoire donné.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Fichiers extraits dans : {extract_to}")
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")

def check_and_update():
    """
    Vérifie la version actuelle et télécharge la dernière version si nécessaire.
    """
    if not os.path.exists(CURRENT_VERSION_FILE):
        with open(CURRENT_VERSION_FILE, "w") as f:
            f.write("0.0.0")

    with open(CURRENT_VERSION_FILE, "r") as f:
        current_version = f.read().strip()

    latest_release = get_latest_release()
    if not latest_release:
        return

    latest_version = latest_release["version"]
    download_url = latest_release["download_url"]

    if current_version == latest_version:
        print("L'application est déjà à jour.")
        return

    print(f"Nouvelle version détectée : {latest_version}. Téléchargement en cours...")

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    zip_path = os.path.join(DOWNLOAD_DIR, "latest_version.zip")
    download_file(download_url, zip_path)

    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)

    extract_zip(zip_path, EXTRACT_DIR)

    with open(CURRENT_VERSION_FILE, "w") as f:
        f.write(latest_version)

    print(f"Mise à jour terminée vers la version {latest_version}.")

if __name__ == "__main__":
    check_and_update()
