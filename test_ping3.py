from ping3 import ping

target = "8.8.8.8"  # Adresse Google DNS
try:
    latency = ping(target, timeout=2)
    if latency is not None:
        print(f"Latence vers {target}: {latency * 1000:.2f} ms")
    else:
        print(f"Impossible de joindre {target}")
except Exception as e:
    print(f"Erreur lors de l'exécution de ping : {e}")
