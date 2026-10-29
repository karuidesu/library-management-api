# Agbale - Système de gestion de bibliothèque


> C'est un **outil de gestion interne** réservé aux bibliothécaires et aux administrateurs. Il ne s'agit **pas** d'un portail public destiné aux adhérents. Les adhérents de la bibliothèque sont enregistrés dans l'annuaire dont les emprunts physiques, les retours et les statuts de compte sont enregistrés, gérés et audités par le personnel autorisé de la bibliothèque.

---

## Table des matières
- [Fonctionnalités](#fonctionnalités)
- [Analyse et modélisation](#analyse-et-modélisation)
- [Structure du dépôt](#structure-du-dépôt)
- [Contrôle d'accès basé sur les rôles (RBAC)](#contrôle-daccès-basé-sur-les-rôles-rbac)
- [Installation](#installation)
- [Compte admin par défaut](#compte-admin-par-défaut)
- [Documentation de l'API](#documentation-de-lapi)
- [Tests et qualité de code](#tests-et-qualité-de-code)
- [Contribution](#contribution)
- [Licence MIT](#licence-mit)


---

## Fonctionnalités

- **Gestion du catalogue :** Suivi complet des livres physiques, validation de la clé de contrôle ISBN (10 et 13), catégories thématiques et suivi de l'état physique (Disponible, Emprunté, Endommagé, Perdu).
- **Circulation et suivi des emprunts :** Enregistrement des sorties (échéance par défaut à +14 jours), retours, détection automatique des retards et journal d'historique.
- **Annuaire des adhérents :** Répertoire centralisé des membres avec suivi des emprunts actifs et verrou de sécurité empêchant la suppression d'un membre ayant des livres en cours d'emprunt.
- **Statistiques et Décisionnel :** Indicateurs clés de performance (KPI) sur le tableau de bord de circulation, classement par popularité des catégories et rapports d'audit exportables en CSV.

---

## Analyse et modélisation

L'ensemble des exigences fonctionnelles, des diagrammes de modélisation et des récits utilisateurs (*user stories*) est documenté dans le dossier [`docs/`](./docs) :

- **[Document d'analyse fonctionnelle](./docs/analysis.md)**
- **Diagrammes :**
  - [Diagramme de cas d'utilisation (Bibliothécaire)](./docs/diagrams/images/use-case-diagram-Librarian.png)
  - [Diagramme de cas d'utilisation (Administrateur)](./docs/diagrams/images/use-case-diagram-Admin.png)
  - [Diagramme de classes](./docs/diagrams/images/class-diagram.png)
  - [Diagramme d'activité](./docs/diagrams/images/activity-diagram.png)
  - [Diagramme de séquence](./docs/diagrams/images/sequence-diagram.png)
  - [Diagramme de paquetages](./docs/diagrams/images/package-diagram.png)

---

## Structure du Dépôt

```
├── docs/
│   ├── analysis.md                 # Analyse fonctionnelle, specs
│   ├── backend.md                  # Documentation technique backend
│   └── diagrams/                   # Diagrammes UML
│
├── alembic/                        # Migrations de base de données et historique
├── app/
│   ├── api/v1/                     # Contrôleurs de routes versionnées
│   ├── core/                       # Configuration, sécurité, moteur de base de données
│   ├── crud/                       # Couche d'accès aux données
│   ├── models/                     # Modèles SQLAlchemy
│   ├── schemas/                    # Schémas Pydantic (validation et DTOs)
│   ├── services/                   # Logique métier des emprunts, retours et statistiques
│   └── main.py                     # Instance de l'application FastAPI et cycle de vie (lifespan)
├── tests/                          # Tests automatisés (19 tests)
├── .env.example                    # Variables d'environnement
├── .gitignore
├── alembic.ini                     # Configuration des migrations Alembic
├── main.py                         # Point d'entrée proxy / ASGI
├── pyproject.toml                  # Configuration des outils
├── requirements.txt                # Dépendances
├── run.py                          # Lancement du serveur
└── README.md                       # Documentation principale du projet
```

---

## Contrôle d'accès basé sur les rôles (RBAC)

Puisque cette plateforme est exclusivement opérée par le personnel de la bibliothèque, les droits d'accès sont appliqués selon les responsabilités opérationnelles :

| Groupe d'Endpoints | Chemin de la Ressource | Rôles Autorisés | Portée Fonctionnelle |
| :--- | :--- | :--- | :--- |
| **Authentification** | `POST /api/v1/auth/login` | Public | Connexion du personnel avec génération de jeton JWT Bearer |
| **Utilisateurs** | `GET /api/v1/users/me` | Authentifié | Consultation de son profil et du nombre de ses emprunts actifs |
| **Utilisateurs** | `GET /api/v1/users` | Admin, Bibliothécaire | Recherche, filtrage et pagination des adhérents et du personnel |
| **Utilisateurs** | `PUT /api/v1/users/{id}` | Admin, Bibliothécaire, Propriétaire | Mise à jour de profil |
| **Utilisateurs** | `DELETE /api/v1/users/{id}` | Administrateur | Suppression de compte |
| **Livres** | `GET /api/v1/books` | Public / Personnel | Recherche dans le catalogue avec filtres (titre, auteur, ISBN, genre) |
| **Livres** | `POST /api/v1/books` | Admin, Bibliothécaire | Ajout de livres|
| **Livres** | `PUT /api/v1/books/{id}` | Admin, Bibliothécaire | Mise à jour des informations d'un livre |
| **Livres** | `DELETE /api/v1/books/{id}` | Admin, Bibliothécaire | Suppression physique d'un livre |
| **Métadonnées** | `/api/v1/categories`, `/states` | Admin, Bibliothécaire | Gestion complète des catégories thématiques et des états physiques |
| **Circulation** | `POST /api/v1/loans/borrow` | Admin, Bibliothécaire | Enregistrement d'un emprunt |
| **Circulation** | `POST /api/v1/loans/return` | Admin, Bibliothécaire | Enregistrement d'un retour |
| **Statistiques** | `GET /api/v1/analytics/dashboard` | Admin, Bibliothécaire | KPI temps réel (Total livres, adhérents actifs, livres empruntés) |
| **Statistiques** | `GET /api/v1/analytics/categories`| Admin, Bibliothécaire | Répartition de la circulation par fréquence de catégorie |
| **Statistiques** | `GET /api/v1/analytics/reports` | Administrateur | Historique d'audit téléchargeable (export JSON ou fichier CSV) |

---

## Installation

1. **Activer l'environnement virtuel :**

   ```powershell
   .\libenv\Scripts\activate   # Windows
   # source libenv/bin/activate # Linux/macOS
   ```

2. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

3. **Appliquer les migrations de base de données :**
   ```powershell
   python -m alembic upgrade head
   ```

4. **Démarrer le serveur :**
   ```bash
   python run.py
   ```

## Compte admin par défaut
- **E-mail :** `admin@agbale.org`
- **Mot de passe :** `AdminPassword123!`

---

## Documentation de l'API

- **Swagger UI :** [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **Documentation ReDoc :** [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc)
- **Schéma OpenAPI :** [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)
- **Vérification Health Check :** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Tests et qualité de code

```powershell
python -m pytest tests -v
```

Standards PEP 8 avec `ruff` et `black` :
```powershell
python -m ruff check app tests
python -m black --check app tests
```


## Contribution

1. Forker le dépôt
2. Créer une branche dédiée pour vos modifications
3. Commiter vos changements
4. Ouvrir une *Pull Request*

## Licence MIT

Développé pour la gestion des bibliothèques associatives et communautaires.

### *_ARIGATO_*