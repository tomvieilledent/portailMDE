# Portfolio-MDE Dashboard

> Tableau de bord de gestion pour la **Maison De l'économie** (pépinière/incubateur d'entreprises) : gestion des utilisateurs, des entreprises hébergées, des formations, de l'actualité et messagerie temps réel.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-REST%20API-black)
![React](https://img.shields.io/badge/React-18-61DAFB)
![Vite](https://img.shields.io/badge/Vite-4-646CFF)
![Tests](https://img.shields.io/badge/tests-268%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Présentation

**Objectif** — Fournir à la *Maison De l'économie* un outil unique pour piloter son activité au quotidien : suivi des entreprises hébergées, gestion des formations et des sessions, diffusion d'actualités, notifications et communication interne en temps réel.

**Problème résolu** — Les MDE jonglent souvent entre tableurs, e-mails et outils dispersés pour suivre leurs entreprises accompagnées et animer leurs formations. Ce projet centralise tout dans une seule application web, avec une gestion fine des droits et une messagerie intégrée.

**Public cible**
- Administrateurs et personnel (staff) de la Maison De l'Entreprise
- Formateurs animant des sessions
- Dirigeants des entreprises hébergées / accompagnées

---

## Fonctionnalités

- **Authentification & sécurité** — connexion JWT, déconnexion (blocklist de jetons), réinitialisation de mot de passe.
- **Gestion des utilisateurs** — création, rôles, rôle *Staff* avec droits granulaires, protection des super-admins.
- **Entreprises hébergées** — fiches entreprises, statut d'hébergement, gestion de « Mon entreprise ».
- **Formations & sessions** — catalogue de formations, sessions programmées, inscriptions (enrollments).
- **Agenda / Événements** — création d'événements, visibilité restreinte aux invités.
- **Actualités** — publication d'actualités + synchronisation automatique de flux RSS d'actualité économique française (job horaire).
- **Notifications** — système de notifications utilisateur.
- **Messagerie temps réel (chat)** — conversations individuelles et **groupes multi-utilisateurs nommés** (façon WhatsApp) via Socket.IO.
- **Invitations** — accès aux événements et sessions programmées réservé aux invités.
- **Exports** — export de données.
- **Documentation API** — Swagger UI intégré.

> _Captures d'écran / GIF : à ajouter dans `docs/` puis référencer ici._

---

## Technologies utilisées

### Backend
- **Langage** : Python 3.12
- **Framework** : Flask (REST API via Flask-RESTful) + Flask-SocketIO (temps réel)
- **ORM / DB** : SQLAlchemy, SQLite (dev) / PostgreSQL (prod via `psycopg2-binary`), migrations Alembic
- **Auth** : Flask-JWT-Extended, Flask-Bcrypt
- **Autres** : APScheduler (jobs planifiés), feedparser (flux RSS), Flask-Cors, python-dotenv, email-validator
- **Serveur prod** : gunicorn

### Frontend
- **Langage** : JavaScript (ES modules)
- **Framework** : React 18
- **Build** : Vite 4
- **Style** : Tailwind CSS 3, PostCSS, autoprefixer
- **UI / temps réel** : lucide-react (icônes), socket.io-client
- Client API maison (`src/lib/api.js`, sans axios)

---

## Installation

### Prérequis
- Python **3.12+**
- Node.js **18+** et npm
- (Optionnel) PostgreSQL pour un déploiement de production

### 1. Cloner le dépôt
```bash
git clone https://github.com/tomvieilledent/portfolio-MDE_dashboard.git
cd portfolio-MDE_dashboard
```

### 2. Installer le backend
```bash
python -m venv .venv
source .venv/bin/activate         # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Installer le frontend
```bash
cd frontend
npm install
cd ..
```

### 4. Variables d'environnement (optionnel)
Créer un fichier `.env` à la racine si besoin :
```bash
DATABASE_URL=sqlite:///data.db      # ou postgresql://user:pass@host:5432/dbname
JWT_SECRET_KEY=change-me-in-production
```
> Sans configuration, l'application utilise `data.db` (SQLite) et une clé JWT par défaut (à ne **pas** utiliser en production).

---

## Utilisation

### Lancer le backend (API + Socket.IO) sur le port 8000
> ⚠️ Toujours lancer depuis la **racine du dépôt** (imports absolus `backend.*`), et via `backend.api.run` pour que les websockets fonctionnent.
```bash
source .venv/bin/activate
python -m backend.api.run
```

- API & Swagger UI : http://localhost:8000/ (aussi `/docs`, `/swagger`)
- Spécification OpenAPI : http://localhost:8000/openapi.json
- Health check : http://localhost:8000/status

### Créer le super administrateur par défaut
```bash
python create_super_admin.py       # admin@admin.com / admin
```
Jeux de données de démonstration : `python seed_demo.py` ou `python seed_accounts.py`.

### Lancer le frontend (Vite) sur le port 3000
```bash
cd frontend
npm run dev
```
Build de production : `npm run build` — prévisualisation : `npm run preview`.

---

## Structure du projet

```
portfolio-MDE_dashboard/
├── backend/
│   ├── api/
│   │   ├── resources/       # Endpoints REST (flask_restful, routing, auth)
│   │   ├── socket_events/   # Événements Socket.IO (chat temps réel)
│   │   ├── run.py           # Entrée serveur (socketio.run)
│   │   └── app.py           # Création de l'app Flask
│   ├── models/              # Modèles de domaine (validation, non-ORM)
│   ├── persistence/
│   │   ├── models.py        # Tables SQLAlchemy (ORM)
│   │   └── services/
│   │       ├── layer.py     # Services (fines enveloppes métier)
│   │       └── facades/     # Toute la logique d'accès à la DB (CRUD SQL)
│   ├── services/            # Jobs transverses (sync news RSS…)
│   └── uploads/             # Fichiers téléversés
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── pages/       # Pages (Dashboard, Users, Trainings, Companies…)
│       │   └── modals/      # Modales (formulaires événements/sessions…)
│       ├── context/         # Contextes React
│       ├── lib/             # Client API (api.js) + socket (socket.js)
│       └── css/
├── alembic/                 # Migrations de base de données
├── tests/                   # Suite pytest
├── create_super_admin.py
├── requirements.txt
└── CLAUDE.md                # Guide d'architecture détaillé
```

**Architecture en couches (backend)** — chaque couche ne parle qu'à celle du dessous :
```
Requête HTTP → Resource → Service → Facade → Modèles ORM
```

---

## Tests

Suite **pytest** (268 tests). Toujours depuis la racine du dépôt :
```bash
source .venv/bin/activate
pytest                                    # suite complète
pytest tests/test_facades.py              # un fichier
pytest tests/test_facades.py::test_name   # un test
pytest -k "conversation"                  # par mot-clé
```
Les tests utilisent une base SQLite temporaire isolée (voir `tests/conftest.py`).

---

## Déploiement

- **Backend** : servi via **gunicorn** (worker compatible eventlet/gevent pour Socket.IO) ; base de données **PostgreSQL** en production (`DATABASE_URL`). Appliquer les migrations avec `alembic upgrade head`.
- **Frontend** : `npm run build` génère un bundle statique (`frontend/dist/`) déployable sur tout hébergement statique (Netlify, Vercel, Nginx…).
- Définir impérativement `JWT_SECRET_KEY` et une `DATABASE_URL` de production.

> Le contrat d'événements du chat est documenté dans `CHAT_GUIDE.md`.

---

## Contribution

1. Créer une branche à partir de `dev` (ne pas travailler directement sur `main`).
2. Respecter l'**architecture en couches** : les accès DB vivent uniquement dans les *facades* ; les *services* restent fins ; la validation d'entrée passe par les modèles de domaine.
3. Ajouter/mettre à jour les tests pytest ; la suite doit rester verte.
4. Ouvrir une Pull Request vers `dev` avec une description claire.

**Conventions**
- Messages de commit descriptifs, préfixés par type : `feat:`, `fix:`, `refactor:`, `docs:`…
- Imports Python absolus enracinés sur `backend.*` (toujours exécuter depuis la racine).
- IDs sous forme d'UUID (chaînes) ; suppression douce (`is_active`, `deactivate_by`, `delete_by`).

---

## Licence

Distribué sous licence **MIT**. (Ajouter un fichier `LICENSE` à la racine si absent.)

---

## Auteurs

Projet développé par :
- Tom Vieilledent
- Nabil Zinini
- Florian Roosebeke
(Holberton School).

- Dépôt GitHub : https://github.com/tomvieilledent/portfolio-MDE_dashboard
- Contact : `12160@holbertonstudents.com`
