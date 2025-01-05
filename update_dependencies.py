import subprocess

def update_requirements():
    print("Updating requirements...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"])

if __name__ == "__main__":
    update_requirements()
