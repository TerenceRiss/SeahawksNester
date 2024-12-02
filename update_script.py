import requests
import os
import zipfile
import shutil

# Configuration
GITHUB_API_URL = "https://api.github.com/repos/TerenceRiss/SeahawksNester/releases/latest"
DOWNLOAD_PATH = "update.zip"
INSTALL_DIR = "C:/path/to/your/app"  # Remplacez par le chemin de votre application

def get_latest_release():
    """Récupérer l'URL de téléchargement de la dernière release."""
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        release_data = response.json()
        download_url = release_data['assets'][0]['browser_download_url']
        print(f"Nouvelle version trouvée : {release_data['tag_name']}")
        return download_url
    except Exception as e:
        print(f"Erreur lors de la récupération de la version : {e}")
        return None

def download_and_install():
    """Télécharger et installer la dernière version."""
    url = get_latest_release()
    if not url:
        print("Aucune mise a jour disponnible.")
        return
    
    print(f"Téléchargement de la dernière version depuis : {url}")
    response = requests.get(url, stream=True)
    with open(DOWNLOAD_PATH, "wb") as file:
        shutil.copyfileobj(response.raw, file)
    print("Téléchargement terminé.")

    # Extraction
    with zipfile.ZipFile(DOWNLOAD_PATH, "r") as zip_ref:
        zip_ref.extractall("update_temp")
    
    # Remplacement des fichiers existants
    for item in os.listdir("update_temp"):
        s = os.path.join("update_temp", item)
        d = os.path.join(INSTALL_DIR, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    
    print("Mise à jour terminée. Redémarrez l'application.")
    os.remove(DOWNLOAD_PATH)
    shutil.rmtree("update_temp")

if __name__ == "__main__":
    download_and_install()
