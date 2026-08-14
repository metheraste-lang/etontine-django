# E-Tontine Tchad — Projet Django

Squelette Django avec comptes utilisateurs, authentification et espace administrateur.

## Démarrage rapide

```bash
# 1. Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer la base de données
python manage.py makemigrations
python manage.py migrate

# 4. Créer un super-administrateur (accès à /admin/ et à l'espace admin)
python manage.py createsuperuser

# 5. Lancer le serveur
python manage.py runserver
```

Ensuite, ouvrez http://127.0.0.1:8000/

## Structure

- `etontine/` — configuration du projet (settings, urls)
- `comptes/` — application gérant les utilisateurs
  - `models.py` — modèle `Utilisateur` personnalisé (téléphone, rôle membre/administrateur)
  - `forms.py` — formulaire d'inscription
  - `views.py` — inscription, connexion, tableau de bord, espace admin
  - `admin.py` — intégration dans l'admin Django natif (`/admin/`)
- `templates/` — pages HTML (inscription, connexion, tableau de bord, espace admin)

## Rendre un utilisateur administrateur

Deux façons :
1. Via `/admin/` (connectez-vous avec le super-utilisateur), modifiez le champ **role** d'un utilisateur à `administrateur`.
2. Via le shell : `python manage.py shell`
   ```python
   from comptes.models import Utilisateur
   u = Utilisateur.objects.get(telephone="+235XXXXXXXX")
   u.role = Utilisateur.ROLE_ADMIN
   u.save()
   ```

## Prochaines étapes suggérées

- Ajouter les modèles `Tontine`, `Cycle`, `Cotisation`
- Intégrer Orange Money / Moov Money / Airtel Money (paiement mobile)
- Ajouter un système de niveaux/parrainage (comme dans votre version HTML/Firebase)
- Déployer (ex: Railway, Render, PythonAnywhere — plus adaptés à Django que GitHub Pages, qui ne supporte que le contenu statique)
