# Explication détaillée du backend — préparation review technique

But de ce document : pouvoir répondre à **n'importe quelle** question sur le backend. On va du plus concret (chaque fichier) au plus général (l'architecture).

---

## 0. Vue d'ensemble en une phrase

Le backend est une **API Flask** organisée en **couches** : les requêtes HTTP/WebSocket arrivent dans les **resources**, qui appellent des **services**, qui appellent des **facades**, qui parlent à la **base de données** via l'**ORM SQLAlchemy**. Chaque couche a une seule responsabilité.

```
Client (React)
   │  HTTP REST  /  WebSocket
   ▼
[ api/resources ]   ← reçoit la requête, vérifie le JWT, valide les entrées
   ▼
[ services (layer.py) ]   ← logique métier, interface stable
   ▼
[ persistence/facades ]   ← toutes les requêtes SQL, renvoie des dict
   ▼
[ persistence/models (ORM) ]   ← description des tables SQLAlchemy
   ▼
Base de données (SQLite / PostgreSQL)
```

---

## 1. Le dossier `api/resources` — c'est quoi ?

C'est la **porte d'entrée HTTP** de l'application. Chaque fichier regroupe les *endpoints* (URL) d'un thème. Avec **Flask-RESTful**, on écrit une **classe par ressource** et **une méthode par verbe HTTP** :

```python
class UserListResource(Resource):
    @jwt_required()
    def get(self):   # GET /users
        ...
    @jwt_required()
    def post(self):  # POST /users
        ...
```

Rôle d'une resource :
1. **Lire la requête** (`request.get_json()`, `request.args`, `request.files`).
2. **Vérifier l'authentification** (`@jwt_required()`) et **les droits** (`_can(user, 'manage_...')`).
3. **Valider** les données (souvent via le modèle de domaine).
4. **Déléguer** au service / à la facade.
5. **Renvoyer** un dict + un code HTTP (Flask-RESTful le transforme en JSON).

Fichiers présents : `auth`, `user`, `company`, `training`, `training_session`, `conversation`, `message`, `notification`, `news`, `event`, `invitation`, `formation_user`, `content`, `contact`, `export`, `_helpers`.
Les URL sont branchées dans `api/app.py` avec `api.add_resource(UserListResource, '/users')`.

`_helpers.py` contient des fonctions partagées entre resources : `_request_payload()` (lit JSON **ou** multipart), `_can()` (vérifie une permission), `_cleanup_replaced_upload()` (supprime l'ancien fichier quand on en upload un nouveau).

---

## 2. `message.py` — attention, il y en a DEUX

C'est un piège classique en review. Il existe deux fichiers `message.py` dans deux couches différentes :

### a) `backend/models/message.py` — le **modèle de domaine**
Une classe `Message` qui ne fait **que de la validation métier**, sans base de données. Elle valide le contenu : chaîne, non vide, ≤ 5000 caractères.
```python
dm = DomainMessage()
dm.content = content   # lève une erreur si vide ou trop long
```
On l'utilise dans la resource **avant** de persister, pour rejeter proprement une donnée invalide (400).

### b) `backend/api/resources/message.py` — la **resource HTTP**
Les endpoints du chat côté REST : lister les messages d'une conversation, messages directs, marquer lus, compter les non-lus, supprimer un message, uploader une pièce jointe. Chaque méthode vérifie que l'appelant a le droit (ex. `is_participant` pour une conversation).

> **Point clé à dire en review** : le *modèle de domaine* valide, la *resource* orchestre la requête HTTP. Deux responsabilités différentes → deux fichiers.

---

## 3. `from __future__ import annotations` — les "future annotations"

Ligne qu'on voit en haut de certains fichiers (ex. `errors.py`).

- En Python, les **annotations de type** (`def f(x: int) -> str:`) sont normalement **évaluées** à l'exécution.
- Avec `from __future__ import annotations`, elles deviennent de **simples chaînes de caractères**, non évaluées (évaluation "paresseuse").

Deux bénéfices :
1. On peut écrire des types modernes (`dict[str, Any]`, `str | None`) même sur d'anciennes versions de Python sans erreur.
2. On peut référencer un type **pas encore défini** (référence en avant) sans planter.

C'est un `__future__` import : ça active en avance un comportement standardisé des versions récentes. Aucun impact à l'exécution, juste sur la façon dont Python lit les annotations.

---

## 4. Le fonctionnement de `jwt_helpers.py`

C'est un **décorateur maison** `@jwt_required()` qui protège les endpoints. Pourquoi ne pas utiliser celui de la librairie ? Pour renvoyer **nos** erreurs JSON normalisées au lieu du format par défaut.

```python
def jwt_required(refresh=False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request(refresh=refresh)   # vérifie le token
            except NoAuthorizationError as exc:
                return error_response(UNAUTHORIZED, ..., 401)   # pas de token
            except JWTExtendedException as exc:
                return error_response(INVALID_TOKEN, ..., 401)  # token invalide/expiré
            return fn(*args, **kwargs)   # token OK → on exécute la vraie méthode
        return wrapper
    return decorator
```

Le paramètre `refresh=True` sert à exiger un **refresh token** (pour `/auth/refresh`) au lieu d'un access token.
Deux cas d'échec sont attrapés : **absence** de token (`NoAuthorizationError` → 401 `UNAUTHORIZED`) et token **invalide/expiré** (`JWTExtendedException` → 401 `INVALID_TOKEN`).

> **Cas limite à connaître** : certaines erreurs **bas niveau** de la librairie PyJWT (ex. *signature invalide* si la clé secrète a changé) ne dérivent pas de `JWTExtendedException`. Si on ne les attrape pas explicitement, elles remontent jusqu'au gestionnaire global et donnent un **500** au lieu d'un 401 — un point d'amélioration possible (attraper aussi `jwt.exceptions.PyJWTError`).

Le décodage réel du token (signature, expiration) est fait par la librairie `flask-jwt-extended`, avec la clé secrète `JWT_SECRET_KEY`. Le décorateur ne fait qu'**envelopper** cette vérification pour uniformiser les réponses.

---

## 5. Le "monkey patching" (`run.py`)

```python
import eventlet
eventlet.monkey_patch()
```

**Monkey patching** = remplacer, à l'exécution, du code d'une librairie par un autre **sans modifier son fichier source**. Ici, `eventlet` **réécrit les modules standards** de Python (`socket`, `threading`, `time`…) pour les rendre **non bloquants / asynchrones**.

**Pourquoi ?** Le chat utilise des **WebSockets** (connexions longues, nombreuses, simultanées). Un serveur classique (un thread par connexion) ne tient pas. Eventlet permet de gérer des milliers de connexions sur un seul thread grâce à des "green threads" coopératifs.

**Pourquoi tout en haut, avant les autres imports ?** Parce qu'il faut patcher `socket`/`threading` **avant** que Flask/SQLAlchemy ne les importent. Si on patche trop tard, certains modules ont déjà chargé la version bloquante → comportement incohérent. C'est pour ça que `run.py` fait `eventlet.monkey_patch()` en toute première instruction.

---

## 6. `api/state.py` — l'état partagé en mémoire

Un petit module qui garde en **mémoire vive** deux choses partagées entre les requêtes et les sockets :

- **`BLOCKLIST`** : un `set` des `jti` (identifiants uniques) des tokens **révoqués** (déconnexion). À chaque requête, un callback JWT vérifie si le token est dans cette liste.
- **`ONLINE_USERS`** : un `dict` `user_id → nombre de connexions ouvertes`. Sert à la **présence** (qui est en ligne). On utilise un compteur (et pas un booléen) parce qu'un utilisateur peut être connecté depuis **plusieurs appareils/onglets** : on ne le passe hors ligne que quand sa **dernière** connexion tombe (`mark_online` / `mark_offline`).

> **Limite à mentionner** : en mémoire = perdu au redémarrage et non partagé entre plusieurs serveurs. En production on mettrait **Redis**. (C'est écrit dans le fichier.)

---

## 7. `api/test.html` — c'est quoi ?

Une **petite page HTML de test manuel** du WebSocket. Elle charge le client Socket.IO depuis un CDN et ouvre une connexion au serveur (`io("http://127.0.0.1:8000")`), puis logge "socket connecté".

C'était un **outil de développement** pour vérifier à la main que le serveur Socket.IO accepte les connexions, avant que le vrai frontend React n'existe. Ce n'est **pas** utilisé en production — juste un bac à sable. (À signaler comme fichier à supprimer/ignorer dans un vrai déploiement.)

---

## 8. Les uploads (`api/uploads.py`) — comment ça marche

Gère l'**enregistrement et la suppression de fichiers** sur le disque. Trois types d'upload, trois fonctions :

- `save_image_upload()` — images (jpg, png, gif, webp) : photos de profil, logos.
- `save_document_upload()` — documents (PDF, Office, txt…) : brochures de formation.
- `save_message_attachment()` — pièces jointes de chat (images + documents + zip).

**Le déroulé d'un upload** (ex. image) :
1. On reçoit un `FileStorage` depuis `request.files`.
2. On **assainit** le nom avec `secure_filename()` (empêche les `../` ou caractères dangereux).
3. On **vérifie l'extension** contre une **liste blanche** (`ALLOWED_IMAGE_EXTENSIONS`). Sinon → erreur.
4. On génère un **nom unique** : `uuid4().hex` + extension (pour les images) ; pour les documents/pièces jointes on garde le nom original **après** le UUID (`uuid__mon-fichier.pdf`) pour que le lien reste lisible.
5. On sauve dans `backend/uploads/<catégorie>/`.
6. On renvoie une **URL publique** `/uploads/<catégorie>/<nom>` (servie par la route `/uploads/<path>` de `app.py`).

`delete_uploaded_file()` supprime un fichier, mais **seulement** s'il est bien dans le dossier `uploads/` (vérification `resolve()` + `parents`) : c'est une protection contre la suppression d'un fichier arbitraire du système (path traversal).

> **Point sécurité à dire** : liste blanche d'extensions + `secure_filename` + UUID + confinement au dossier uploads.

---

## 9. Les services et les facades

C'est le cœur de l'architecture en couches. Deux niveaux :

### La couche **Facades** (`persistence/services/facades/`)
Une facade = **la seule couche qui parle à la base de données**. Une facade par entité (`UserFacade`, `MessageFacade`, `NotificationFacade`…). Elle contient toutes les requêtes SQLAlchemy (create, get, list, update, delete) et **renvoie des `dict`**, jamais des objets ORM.

Exemple (`NotificationFacade.create`) :
```python
def create(self, recipient_id, content, is_read=False, **kwargs):
    with session_scope() as db:              # ouvre une transaction
        n = ORMNotification(recipient_id=recipient_id, content=content.strip(), ...)
        db.add(n); db.flush(); db.refresh(n) # écrit et récupère l'id généré
        return self._to_dict(n)              # renvoie un dict, pas l'objet ORM
```

Chaque facade a une méthode privée `_to_dict()` qui transforme la ligne ORM en dictionnaire sérialisable en JSON.

**Pourquoi des facades (le pattern Facade) ?**
- **Isoler la base** : si on change la façon de stocker, seule la facade change.
- **Éviter les bugs de session** : en renvoyant des dict, on n'a pas d'objet ORM "détaché" d'une session fermée.
- **Sérialisation facile** : un dict part directement en JSON.

### La couche **Services** (`persistence/services/layer.py`)
Un service **enveloppe** une facade pour exposer une **interface métier stable** aux resources.
```python
class UserService:
    def __init__(self):
        self.facade = UserFacade()
    def login(self, email, password):
        if not self.facade.check_password(email, password):
            return None
        return self.facade.get_by_email(email)
```

Le service porte la **logique métier / cas d'usage** (ex. « se connecter » = vérifier le mot de passe **puis** renvoyer l'utilisateur). Les resources appellent le service (`service.login(...)`) et ne connaissent pas SQLAlchemy.

> **Honnêteté en review** : dans le projet, beaucoup de méthodes de service ne font que déléguer 1-pour-1 à la facade (`self.facade`), et certaines resources appellent même directement `service.facade.xxx`. C'est un point d'amélioration identifié : la couche service pourrait être enrichie ou allégée. Savoir le dire montre du recul.

---

## 10. `layer.py` — c'est quoi ?

C'est **le fichier qui contient tous les services** (`UserService`, `CompanyService`, `TrainingService`, `MessageService`, `ConversationService`, `NewsService`, `EventService`…). Le nom « layer » = **la couche service**. Il importe les facades et expose, pour chaque entité, une classe de service avec des méthodes métier. C'est l'interface que les resources utilisent.

---

## 11. `persistence/db.py` — expliqué

C'est la **configuration de la connexion** à la base. Trois objets clés :

```python
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db}")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, ...)
Base = declarative_base()
```

- **`engine`** : le "moteur" qui sait se connecter à la base (SQLite par défaut, PostgreSQL si `DATABASE_URL` est défini). Le driver PostgreSQL (`psycopg2`) est déjà dans les dépendances → passer de l'un à l'autre = juste changer la variable d'environnement.
- **`SessionLocal`** : une **fabrique de sessions**. Une session = une conversation transactionnelle avec la base (on ouvre, on fait des requêtes, on `commit` ou `rollback`, on ferme). Les facades créent une session par opération (via `session_scope()`).
- **`Base`** : la classe de base dont **héritent tous les modèles ORM**. Elle collecte les métadonnées (la description de toutes les tables).

Point important écrit dans le fichier : **db.py ne crée jamais les tables**. Le schéma appartient à **Alembic** (`alembic upgrade head`). db.py ne fait que la plomberie de connexion.

---

## 12. La différence "facade" / "model" / "models"

Trois notions qu'on confond facilement :

| Terme | Où | Rôle |
|-------|-----|------|
| **Modèle de domaine** (`backend/models/`) | `user.py`, `message.py`… | Classes Python **sans base de données**, qui **valident** les règles métier (email valide, mot de passe ≥ 8, contenu ≤ 5000). |
| **Modèle ORM** (`backend/persistence/models.py`) | une classe par table | Décrit les **tables SQL** (colonnes, types) pour SQLAlchemy et Alembic. C'est le mapping objet ↔ table. |
| **Facade** (`persistence/services/facades/`) | `user_facade_sql.py`… | Utilise les **modèles ORM** pour faire les **requêtes SQL** et renvoie des **dict**. |

Autrement dit :
- Le **modèle de domaine** dit *"cette donnée est-elle valide ?"*.
- Le **modèle ORM** dit *"à quoi ressemble la table ?"*.
- La **facade** dit *"comment je lis/écris cette table ?"*.

**Pourquoi séparer domaine et ORM ?** La validation métier ne dépend pas de la base. On valide l'objet de domaine **avant** de persister via la facade. Ça garde chaque responsabilité isolée et testable.

---

## 13. Le mailer, l'agenda_export et le news_sync (`backend/services/`)

Ce dossier contient les **services "techniques"** (différents des services métier de `layer.py`) : envoi d'e-mail et tâches de fond.

### `mailer.py` — envoi d'e-mails
Un wrapper autour de `smtplib` (bibliothèque standard, aucune dépendance). Configuré **entièrement par variables d'environnement** (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`…).
- `is_configured()` : y a-t-il un serveur SMTP ? Si non, `send_email()` est un **no-op** qui renvoie `False` (l'app continue de marcher en dev sans serveur mail).
- `send_email()` : construit un `EmailMessage` (texte + HTML), se connecte en SSL ou STARTTLS, s'authentifie, envoie. **Ne lève jamais d'exception** : en cas d'échec réseau, il logge et renvoie `False` pour ne pas casser la requête en cours.
- Utilisé par : la **réinitialisation de mot de passe** et le **formulaire de contact**.

### `news_sync.py` — veille économique automatique
Récupère des actualités depuis des **flux RSS** français (INPI, Journal Officiel, BOFiP, Douanes…).
- `sync_all()` : d'abord **purge** les news de plus de 30 jours (fenêtre glissante), puis parcourt chaque source.
- `_fetch_rss()` : télécharge le flux (`requests`), le parse (`feedparser`), et pour chaque article : ignore ceux **déjà en base** (`facade.url_exists`), sans titre ou sans résumé, ou dont l'URL est cassée (`_url_reachable` fait un HEAD HTTP). Sinon il crée la news via la facade.
- Déclenché **automatiquement chaque jour** par le scheduler (dans `app.py`) et manuellement via `POST /news/sync`.

### `agenda_export.py` — fiche d'agenda mensuelle
Génère une **page HTML imprimable** des événements et sessions **publics** du mois à venir, stockée dans `uploads/exports/`.
- `collect(year, month)` : rassemble les événements publics + les sessions de formation/atelier de ce mois, triés par date.
- Le logo Rodez est intégré en **base64** dans le HTML (fiche autonome, imprimable sans dépendance externe).
- Déclenché **automatiquement le 25 de chaque mois** par le scheduler (pour préparer le mois suivant) ou à la demande via `/exports/monthly`.

> **Le scheduler** (dans `app.py`) est un `APScheduler` : `news_sync` en tâche quotidienne, `agenda_export` en tâche mensuelle (cron le 25).

---

## 14. Postman — explication

**Postman** est un outil pour **tester une API HTTP à la main**, sans frontend. Dans le projet, le dossier `postman/` contient deux fichiers :

- **La collection** (`...collection.json`) : ~56 requêtes pré-écrites, rangées par dossier (Auth, Users, Companies, Trainings, Conversations, Messages, Notifications, News…). Chaque requête a sa méthode, son URL, son corps JSON d'exemple. On importe le fichier dans Postman et on peut cliquer sur "Send" pour appeler l'API.
- **L'environnement** (`...environment.json`) : des **variables** réutilisables — `baseUrl`, `accessToken`, `refreshToken`, `userId`, `companyId`, etc. Par exemple, après un login on stocke le token dans `{{accessToken}}` et toutes les requêtes protégées l'utilisent automatiquement dans leur en-tête `Authorization`.

**À quoi ça sert dans le projet :**
1. **Documenter** l'API de façon exécutable (un nouveau développeur importe la collection et comprend tous les endpoints).
2. **Tester manuellement** un scénario (register → login → créer une entreprise → …) sans écrire de code.
3. Vérifier les codes de retour et les erreurs.

C'est complémentaire de **Swagger UI** (`/docs`), qui documente aussi l'API mais est généré depuis la spec OpenAPI.

---

## 15. L'architecture globale — quel layer sert à quoi

L'application suit une **architecture en couches** (layered architecture). Chaque couche ne connaît que la couche juste en dessous.

Sur chaque flèche est indiqué **le type de donnée qui transite** entre deux couches.

```
        ┌───────────────────────────────────┐
        │   FRONTEND (React)                │
        └───────────────────────────────────┘
                  │            ▲
        JSON + JWT │            │ JSON + code HTTP
         (requête) ▼            │  (réponse)
        ┌───────────────────────────────────┐
        │   COUCHE API  (resources)         │
        └───────────────────────────────────┘
                  │            ▲
   arguments      │            │ dict
   Python (str…)  ▼            │
        ┌───────────────────────────────────┐
        │   COUCHE SERVICES  (layer.py)     │
        └───────────────────────────────────┘
                  │            ▲
   arguments      │            │ dict / list[dict]
   Python (str…)  ▼            │
        ┌───────────────────────────────────┐
        │   COUCHE FACADES                  │
        └───────────────────────────────────┘
                  │            ▲
   objets ORM     │            │ objets ORM
   + Query        ▼            │ (lignes mappées)
        ┌───────────────────────────────────┐
        │   COUCHE ORM  (models.py + db.py) │
        └───────────────────────────────────┘
                  │            ▲
   requête SQL    │            │ lignes / rowcount
                  ▼            │
        ┌───────────────────────────────────┐
        │   BASE DE DONNÉES  (SQLite/PG)    │
        └───────────────────────────────────┘
```

Lecture rapide (ce qui transite sur chaque flèche) :

| Entre… | …et… | Type de donnée |
|--------|------|----------------|
| Frontend | API | **JSON** (+ JWT) en requête / **JSON + code HTTP** en réponse |
| API | Services | **arguments Python** (descente) / **`dict`** (remontée) |
| Services | Facades | **arguments Python** (descente) / **`dict` / `list[dict]`** (remontée) |
| Facades | ORM | **objets ORM** + requêtes SQLAlchemy |
| ORM | Base | **requête SQL** (descente) / **lignes** (remontée) |

> ⚠️ Précision importante pour la review : le **JSON n'existe qu'entre le client et l'API**. Dès qu'on passe sous la couche API, ce sont des **objets Python** : des *arguments* qui descendent, des *`dict`* qui remontent. C'est la couche API (Flask-RESTful) qui fait la traduction **JSON ↔ dict Python** dans les deux sens. La facade, elle, fait la traduction **objet ORM ↔ `dict`**.

**Rôle de chaque couche, en une phrase :**
- **API / resources** : traduit une requête HTTP en appel métier (et gère sécurité + validation).
- **Services (layer.py)** : exprime les cas d'usage métier, indépendamment du transport HTTP.
- **Facades** : parlent SQL, isolent totalement la base du reste du code.
- **ORM / models + db.py** : décrivent les tables et la connexion.
- **Base de données** : stocke les données ; son schéma est versionné par Alembic.

**Le grand avantage** : on peut tester chaque couche séparément, changer de base sans toucher aux resources, et chaque fichier a une responsabilité unique.

---

## Questions pièges probables du jury (réponses courtes)

- **"Pourquoi une couche facade en plus des services ?"** → Isoler SQLAlchemy : le reste du code manipule des dict, jamais des objets ORM (évite les erreurs de session détachée, facilite le JSON).
- **"Pourquoi deux fichiers `message.py` ?"** → L'un est le modèle de **domaine** (validation), l'autre la **resource** HTTP. Responsabilités différentes.
- **"Que se passe-t-il si le token est invalide ?"** → `jwt_helpers` intercepte l'absence de token et les tokens invalides/expirés et renvoie un **401** JSON normalisé. (Cas limite : une *signature invalide* de PyJWT donne aujourd'hui un 500 — amélioration possible.)
- **"Pourquoi le monkey patch tout en haut ?"** → Pour patcher `socket`/`threading` **avant** que Flask ne les importe, sinon eventlet ne peut pas rendre les WebSockets asynchrones.
- **"Où sont créées les tables ?"** → Par **Alembic** (`alembic upgrade head`), pas par le code applicatif. `db.py` ne fait que la connexion.
- **"La présence/blocklist, ça scale ?"** → Non, c'est en mémoire (`state.py`). En prod → **Redis**.
