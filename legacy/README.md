# Portfolio-MDE Dashboard

> Management dashboard for a **Maison De l'Entreprise** (French business incubator): manage users, hosted companies, trainings, news, and real-time messaging.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-REST%20API-black)
![React](https://img.shields.io/badge/React-18-61DAFB)
![Vite](https://img.shields.io/badge/Vite-4-646CFF)
![Tests](https://img.shields.io/badge/tests-268%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

> 🇫🇷 Une version française de ce document est disponible : [README.fr.md](./README.fr.md)

---

## Overview

**Goal** — Give a *Maison De l'Entreprise* (business incubator) a single tool to run its day-to-day activity: tracking hosted companies, managing trainings and sessions, publishing news, sending notifications, and communicating internally in real time.

**Problem it solves** — Incubators often juggle spreadsheets, emails, and scattered tools to follow the companies they support and run their training programs. This project centralizes everything in one web application, with fine-grained permissions and built-in messaging.

**Target audience**
- Administrators and staff of the Maison De l'Entreprise
- Trainers running sessions
- Executives of hosted / supported companies

---

## Features

- **Authentication & security** — JWT login, logout (token blocklist), password reset.
- **User management** — creation, roles, a *Staff* role with granular rights, super-admin protection.
- **Hosted companies** — company profiles, hosting status, "My company" management.
- **Trainings & sessions** — training catalog, scheduled sessions, enrollments.
- **Agenda / Events** — event creation with invitee-restricted visibility.
- **News** — news publishing + automatic sync of French business-news RSS feeds (hourly job).
- **Notifications** — user notification system.
- **Real-time chat** — one-to-one conversations and **named multi-user groups** (WhatsApp-like) over Socket.IO.
- **Invitations** — events and scheduled sessions restricted to invitees.
- **Exports** — data export.
- **API documentation** — built-in Swagger UI.

> _Screenshots / GIFs: add them under `docs/` and reference them here._

---

## Tech stack

### Backend
- **Language**: Python 3.12
- **Framework**: Flask (REST API via Flask-RESTful) + Flask-SocketIO (real-time)
- **ORM / DB**: SQLAlchemy, SQLite (dev) / PostgreSQL (prod via `psycopg2-binary`), Alembic migrations
- **Auth**: Flask-JWT-Extended, Flask-Bcrypt
- **Others**: APScheduler (scheduled jobs), feedparser (RSS feeds), Flask-Cors, python-dotenv, email-validator
- **Prod server**: gunicorn

### Frontend
- **Language**: JavaScript (ES modules)
- **Framework**: React 18
- **Build**: Vite 4
- **Styling**: Tailwind CSS 3, PostCSS, autoprefixer
- **UI / real-time**: lucide-react (icons), socket.io-client
- Custom API client (`src/lib/api.js`, no axios)

---

## Installation

### Prerequisites
- Python **3.12+**
- Node.js **18+** and npm
- (Optional) PostgreSQL for production

### 1. Clone the repository
```bash
git clone https://github.com/tomvieilledent/portfolio-MDE_dashboard.git
cd portfolio-MDE_dashboard
```

### 2. Install the backend
```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install the frontend
```bash
cd frontend
npm install
cd ..
```

### 4. Environment variables (optional)
Create a `.env` file at the repo root if needed:
```bash
DATABASE_URL=sqlite:///data.db      # or postgresql://user:pass@host:5432/dbname
JWT_SECRET_KEY=change-me-in-production
```
> Without configuration, the app falls back to `data.db` (SQLite) and a default JWT key (do **not** use in production).

---

## Usage

### Run the backend (API + Socket.IO) on port 8000
> ⚠️ Always run from the **repo root** (absolute `backend.*` imports), and via `backend.api.run` so websockets work.
```bash
source .venv/bin/activate
python -m backend.api.run
```

- API & Swagger UI: http://localhost:8000/ (also `/docs`, `/swagger`)
- OpenAPI spec: http://localhost:8000/openapi.json
- Health check: http://localhost:8000/status

### Create the default super admin
```bash
python create_super_admin.py       # admin@admin.com / admin
```
Demo data: `python seed_demo.py` or `python seed_accounts.py`.

### Run the frontend (Vite) on port 3000
```bash
cd frontend
npm run dev
```
Production build: `npm run build` — preview: `npm run preview`.

---

## Project structure

```
portfolio-MDE_dashboard/
├── backend/
│   ├── api/
│   │   ├── resources/       # REST endpoints (flask_restful, routing, auth)
│   │   ├── socket_events/   # Socket.IO events (real-time chat)
│   │   ├── run.py           # Server entrypoint (socketio.run)
│   │   └── app.py           # Flask app factory
│   ├── models/              # Domain models (validation, non-ORM)
│   ├── persistence/
│   │   ├── models.py        # SQLAlchemy tables (ORM)
│   │   └── services/
│   │       ├── layer.py     # Services (thin business wrappers)
│   │       └── facades/     # All DB access logic (SQL CRUD)
│   ├── services/            # Cross-cutting jobs (RSS news sync…)
│   └── uploads/             # Uploaded files
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── pages/       # Pages (Dashboard, Users, Trainings, Companies…)
│       │   └── modals/      # Modals (event/session forms…)
│       ├── context/         # React contexts
│       ├── lib/             # API client (api.js) + socket (socket.js)
│       └── css/
├── alembic/                 # Database migrations
├── tests/                   # pytest suite
├── create_super_admin.py
├── requirements.txt
└── CLAUDE.md                # Detailed architecture guide
```

**Layered architecture (backend)** — each layer only talks to the one below it:
```
HTTP request → Resource → Service → Facade → ORM models
```

---

## Tests

**pytest** suite (268 tests). Always run from the repo root:
```bash
source .venv/bin/activate
pytest                                    # full suite
pytest tests/test_facades.py              # one file
pytest tests/test_facades.py::test_name   # one test
pytest -k "conversation"                  # by keyword
```
Tests use an isolated temporary SQLite database (see `tests/conftest.py`).

---

## Deployment

- **Backend**: served with **gunicorn** (eventlet/gevent-compatible worker for Socket.IO); **PostgreSQL** in production (`DATABASE_URL`). Apply migrations with `alembic upgrade head`.
- **Frontend**: `npm run build` produces a static bundle (`frontend/dist/`) deployable to any static host (Netlify, Vercel, Nginx…).
- Always set a strong `JWT_SECRET_KEY` and a production `DATABASE_URL`.

> The chat event contract is documented in `CHAT_GUIDE.md`.

---

## Contributing

1. Branch off `dev` (do not work directly on `main`).
2. Respect the **layered architecture**: DB access lives only in *facades*; *services* stay thin; input validation goes through domain models.
3. Add/update pytest tests; the suite must stay green.
4. Open a Pull Request against `dev` with a clear description.

**Conventions**
- Descriptive, type-prefixed commit messages: `feat:`, `fix:`, `refactor:`, `docs:`…
- Absolute Python imports rooted at `backend.*` (always run from the repo root).
- String UUID IDs; soft-delete pattern (`is_active`, `deactivate_by`, `delete_by`).

---

## License

Released under the **MIT** license. (Add a `LICENSE` file at the root if missing.)

---

## Authors

Built by the 
- Tom Vieilledent
- Nabil Zinini
- Florian Roosebeke
(Holberton School).

- GitHub repository: https://github.com/tomvieilledent/portfolio-MDE_dashboard
- Contact: `12160@holbertonstudents.com`
