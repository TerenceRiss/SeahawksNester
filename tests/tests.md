# 📌 Documentation des Tests Unitaires

## **1️⃣ Introduction aux Tests**
Les tests unitaires permettent de **valider le bon fonctionnement** des différentes fonctionnalités du projet **Seahawks Nester**. Ils garantissent que le code fonctionne comme prévu et permettent d'éviter les régressions.

**Outils utilisés :**
- `pytest` → Framework de test en Python
- `requests` → Bibliothèque HTTP pour tester les API
- `jwt` → Pour la génération et la validation des tokens JWT

---

## **2️⃣ Structure du Dossier `tests/`**
Le dossier `tests/` contient plusieurs fichiers, chacun testant une fonctionnalité spécifique.

```
tests/
│── test_login.py               # Tests de l'authentification
│── test_register.py            # Tests de l'inscription
│── test_protected_routes.py    # Tests des routes protégées
│── test_receive_data.py        # Tests de la réception des scans
│── test_scan.py                # Tests de la route de scan
│── test_metrics.py             # Tests des métriques Prometheus
```

---

## **3️⃣ Explication des Fichiers de Test**

### **📌 `test_login.py` - Tests de connexion utilisateur**
- ✅ `test_login_success` → Vérifie qu'un utilisateur peut se connecter avec les bons identifiants
- ✅ `test_login_invalid_credentials` → Vérifie qu'un utilisateur ne peut pas se connecter avec un mauvais mot de passe

### **📌 `test_register.py` - Tests d'inscription utilisateur**
- ✅ `test_register_success` → Vérifie qu'un nouvel utilisateur peut s'inscrire
- ✅ `test_register_existing_user` → Vérifie qu'on ne peut pas s'inscrire avec un username déjà existant

### **📌 `test_protected_routes.py` - Tests des routes sécurisées**
- ✅ `test_protected_route_without_token` → Vérifie qu'une route protégée refuse l'accès sans token JWT
- ✅ `test_protected_route_with_invalid_token` → Vérifie que l'accès est refusé avec un token invalide
- ✅ `test_protected_route_with_valid_token` → Vérifie que l'accès est autorisé avec un token valide

### **📌 `test_receive_data.py` - Tests de la réception des résultats de scan**
- ✅ `test_receive_data_without_token` → Vérifie que `/receive-data` est bien protégée
- ✅ `test_receive_data_with_valid_token` → Vérifie que les données de scan sont bien reçues avec un token valide

### **📌 `test_scan.py` - Tests de la route de scan réseau**
- ✅ `test_scan_protected_route` → Vérifie que `/scan` est bien protégée et retourne 401 Unauthorized

### **📌 `test_metrics.py` - Tests de la route Prometheus**
- ✅ `test_metrics_access` → Vérifie que la route `/metrics` est accessible et retourne des données au format Prometheus

---

## **4️⃣ Exécution des Tests**

### **📌 Exécuter tous les tests**
```bash
pytest tests/
```

### **📌 Exécuter un test spécifique**
```bash
pytest tests/test_register.py
```

### **📌 Exécuter un test en mode verbeux (plus de détails)**
```bash
pytest -v tests/
```

### **📌 Générer un rapport HTML des tests**
```bash
pytest --html=report.html --self-contained-html
```

---

## **5️⃣ Interprétation des Résultats**
Lorsque les tests sont exécutés, `pytest` affiche un rapport :

✅ **Test réussi :**
```
tests/test_login.py ..    [PASS]
tests/test_register.py ..  [PASS]
```
❌ **Test échoué :**
```
tests/test_scan.py F
FAILED tests/test_scan.py::test_scan_protected_route - assert 405 == 401
```
📌 **Que faire en cas d’erreur ?**
- **401 Unauthorized** → Vérifier si la route est bien protégée avec JWT.
- **405 Method Not Allowed** → Vérifier si la bonne méthode HTTP (GET/POST) est utilisée.
- **400 Bad Request** → Vérifier si les données envoyées sont valides.

---

## **6️⃣ Conclusion**
Cette documentation détaille tous les tests unitaires mis en place pour **garantir la sécurité et la fiabilité** du projet **Seahawks Nester**. 🚀

**Commandes à retenir :**
```bash
pytest tests/  # Exécuter tous les tests
pytest tests/test_register.py  # Exécuter un test spécifique
```
✅ **Avec cette suite de tests, nous avons une couverture complète du projet !** 🎯

