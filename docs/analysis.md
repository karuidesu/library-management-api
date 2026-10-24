## Contexte et justification

Pour toute bibliothèque, gérer efficacement les collections, les adhérents, la circulation des ouvrages et les permissions du personnel peut rapidement devenir complexe.

**Agbale** est un logiciel de gestion de bibliothèque conçu pour les associations à but non lucratif, les espaces de lecture communautaires et les bibliothèques. C'est un **outil d'administration et de gestion interne** réservé aux **Bibliothécaires** et aux **Administrateurs**. Les adhérents de la bibliothèque sont des entités répertoriées dans l'annuaire pour le compte desquelles les emprunts sont enregistrés, ils ne disposent pas d'identifiants d'accès direct ni de portail utilisateur.

---

## Analyse et modélisation

- **Méthodologies :** UML, BPMN 2.0
- **Outils de modélisation :** Draw.io, Camunda Modeler


### Diagrammes
- **[Diagramme de classes](./diagrams/images/class-diagram.png)**
- **[Diagramme d'activité](./diagrams/images/activity-diagram.png)**
- **[Diagramme de paquetages](./diagrams/images/package-diagram.png)**
- **[Diagramme de cas d'utilisation — Administrateur](./diagrams/images/use-case-diagram-Admin.png)**
- **[Diagramme de cas d'utilisation — Bibliothécaire](./diagrams/images/use-case-diagram-Librarian.png)**

### Fichiers sources modifiables (.drawio)
- **[Source du diagramme de classes](./diagrams/editable/class-diagram.drawio)**
- **[Source du diagramme d'activité](./diagrams/editable/activity-diagram.drawio)**
- **[Source du diagramme de séquence](./diagrams/editable/sequence-diagram.drawio)**
- **[Source des diagrammes de cas d'utilisation](./diagrams/editable/use-case-diagram.drawio)**
- **[Source du diagramme de paquetages](./diagrams/editable/package-diagram.drawio)**

---

## Acteurs et rôles

1. **Administrateur :**
   - Utilisateur interne authentifié disposant de l'intégralité des privilèges d'administration.
   - Gère les comptes du personnel, les attributions de rôles, la sécurité du système, les métadonnées du catalogue, les journaux d'audit et les statistiques décisionnelles.

2. **Bibliothécaire / Gestionnaire:**
   - Utilisateur opérationnel authentifié.
   - Gère les flux de travail quotidiens de la bibliothèque : fiches du catalogue, fiches d'adhérents de l'annuaire, transactions de prêt et de retour, ainsi que le suivi des retards.

3. **Adhérent / Membre :**
   - Lecteur ou emprunteur externe enregistré dans l'annuaire du système.
   - **NB :** Les adhérents ne se connectent pas au système, leurs données sont gérées par les bibliothécaires et les administrateurs pour garantir la traçabilité et la responsabilité des emprunts.

---

## Cas d'Utilisation

### Gestion du catalogue et des stocks
- **Ajouter un livre :** Enregistrer un nouvel ouvrage avec son titre, auteur, numéro ISBN unique, catégorie, nombre d'exemplaires et état physique.
- **Mettre à jour un livre :** Modifier les métadonnées, mettre à jour les éléments visuels de couverture (badges, emojis) ou réapprovisionner les exemplaires.
- **Supprimer / Archiver un livre :** Retirer de la circulation active les ouvrages obsolètes, endommagés ou perdus.
- **Rechercher et filtrer les livres :** Consulter les livres par titre, auteur, ISBN, catégorie ou statut de disponibilité.
- **Gérer les catégories et les états :** Configurer les classifications thématiques (ex. : Fiction, Sciences, Histoire) et les états physiques (Disponible, Emprunté, Endommagé, Perdu).

### Circulation (Prêts et retours)
- **Emprunter un livre :** Enregistrer le prêt d'un livre disponible au profit d'un adhérent inscrit, décrémenter le stock disponible, consigner la date limite de restitution et associer le bibliothécaire opérateur.
- **Restituer un livre :** Enregistrer le retour physique, évaluer l'état du livre, rétablir sa disponibilité dans l'inventaire et clôturer la transaction.
- **Suivre les emprunts en retard :** Identifier les transactions actives dont la date d'échéance est dépassée afin d'engager les relances auprès des adhérents.

### Annuaire des adhérents et gestion du personnel
- **Ajouter un adhérent :** Enregistrer un nouveau lecteur dans l'annuaire des membres.
- **Mettre à jour un adhérent :** Actualiser les données d'un adhérent.
- **Rechercher un adhérent :** Recherche rapide par nom ou e-mail pour consulter l'historique des emprunts et les prêts en cours.
- **Gérer les comptes du personnel :** Créer, modifier, activer ou désactiver les comptes Bibliothécaire et Administrateur, gérer les identifiants et les privilèges RBAC.

### Statistiques et rapports décisionnels
- **Consulter le tableau de bord :** Indicateurs de performance (KPI) en temps réel sur les volumes totaux du catalogue, les prêts en cours, les retards et la répartition par catégorie.
- **Générer des rapports d'audit :** Exporter l'historique complet des transactions de circulation et les listes d'emprunts en retard au format CSV à des fins de reporting et d'archivage.

### Métadonnées de l'organisation :

Point d'accès public (`/api/v1/system/info`) permettant à l'interface client d'afficher dynamiquement le nom de l'établissement (`ORGANIZATION_NAME`), le libellé de l'application et l'environnement d'exécution.

---

## Classes Principales du Domaine

### User
Représente à la fois les opérateurs du personnel (avec accès authentifié) et les adhérents répertoriés dans l'annuaire.
* **Attributs :**
  - `id` : Entier (clé primaire)
  - `name` : Chaîne de caractères
  - `email` : Chaîne de caractères (unique)
  - `hashedPassword` : Chaîne de caractères
  - `is_active` : Booléen
  - `role_id` : Entier (clé étrangère -> Role)
  - `last_access` : DateTime
  - `created_at` : DateTime
  - `updated_at` : DateTime
* **Responsabilités :**
  - Authentifier et autoriser les opérations du personnel (Administrateur / Bibliothécaire).
  - Intervenir en tant qu'emprunteur (`user_id`) ou en tant qu'opérateur de traitement (`handler_id`) dans les transactions.

### Role
Définit les niveaux de contrôle d'accès au système.
* **Attributs :**
  - `id` : Entier
  - `label` : Chaîne de caractères
* **Responsabilités :**
  - Appliquer le contrôle d'accès basé sur les rôles (RBAC) sur l'ensemble des points de terminaison de l'API.

### Book
* **Attributs :**
  - `id` : Entier
  - `title` : Chaîne de caractères
  - `author` : Chaîne de caractères
  - `isbn` : Chaîne de caractères (identifiant unique normalisé ISBN-10 / ISBN-13)
  - `category_id` : Entier (clé étrangère -> Category)
  - `state_id` : Entier (clé étrangère -> BookState)
  - `description` : Texte
  - `publication_year` : Entier
  - `copies` : Entier
  - `cover_color` : Chaîne de caractères
  - `cover_accent` : Chaîne de caractères
  - `cover_emoji` : Chaîne de caractères
  - `created_at` : DateTime
  - `updated_at` : DateTime

### Category
* **Attributs :**
  - `id` : Entier
  - `name` : Chaîne de caractères
  - `created_at` : DateTime
  - `updated_at` : DateTime

### BookState
* **Attributs :**
  - `id` : Entier
  - `name` : Chaîne de caractères
  - `created_at` : DateTime
  - `updated_at` : DateTime

### BorrowingTransaction
* **Attributs :**
  - `id` : Entier
  - `user_id` : Entier
  - `book_id` : Entier (clé étrangère -> Book)
  - `borrow_date` : DateTime
  - `return_due_date` : DateTime
  - `actual_return_date` : DateTime
  - `handler_id` : Entier
  - `created_at` : DateTime
  - `updated_at` : DateTime
* **Méthodes :**
  - `is_active` : Booléen
  - `is_overdue` : Booléen
  - `checkout()` : Initialiser la transaction et mettre à jour la disponibilité du livre.
  - `checkin()` : Finaliser la transaction et rétablir la disponibilité du livre.

---

## Processus Métier

### 1. Sortie d'un Livre
1. Le bibliothécaire s'authentifie sur l'application.
2. Le bibliothécaire recherche et sélectionne l'ouvrage demandé.
3. Le bibliothécaire sélectionne l'adhérent emprunteur dans l'annuaire des membres.
4. Le système calcule automatiquement la date limite de retour (délai standard de 14 jours par défaut).
5. Le système crée un enregistrement actif `BorrowingTransaction` consignant `borrow_date`, `return_due_date` et `handler_id`.
6. Le système met à jour l'état de l'ouvrage vers `BORROWED` (ou décrémente le stock disponible).

### 2. Restitution d'un Livre
1. Le bibliothécaire sélectionne l'emprunt actif via la recherche par livre ou par adhérent.
2. Le bibliothécaire inspecte l'état physique du livre restitué.
3. Le système enregistre `actual_return_date` et vérifie si le retour s'effectue dans les délais ou en retard.
4. Le bibliothécaire met à jour l'état de l'exemplaire (`AVAILABLE` ou `DAMAGED` si une réparation physique est requise).
5. La transaction est clôturée et archivée pour l'historique d'audit.
