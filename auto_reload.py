import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart()

    def restart(self):
        if self.process:
            print("Redémarrage de l'application...")
            self.process.terminate()
            self.process.wait()
        self.process = subprocess.Popen(self.command, shell=True)

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.html', '.css', '.js', '.sql')):
            print(f"Fichier modifié : {event.src_path}. Redémarrage...")
            self.restart()

if __name__ == "__main__":
    path = "."  # Répertoire à surveiller
    command = "python server.py"  # Commande pour démarrer l'application

    event_handler = RestartHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    print("Surveillance des modifications de fichiers. Appuyez sur Ctrl+C pour arrêter.")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
