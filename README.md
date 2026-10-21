# portailMDE

Portail de mise en relation des entreprises d'une pépinière d'entreprises : annuaire (trombinoscope) des personnes et des entreprises, chat, événements, formations, actualités.

## Stack

- Backend : Python, FastAPI, SQLAlchemy 2, Alembic
- Frontend : React, Vite, Tailwind CSS
- Base de données : PostgreSQL
- Conteneurisation : Docker Compose

> Refonte de `portfolio-MDE_dashboard`. L'ancien code reste disponible dans l'historique git.

## Démarrage (Docker)

```bash
cp .env.example .env        # puis adapter les secrets
make up                     # base, API, front, Mailpit
make seed                   # données de démonstration (optionnel)
```

| Service  | URL                           |
| -------- | ----------------------------- |
| Front    | http://localhost:5290         |
| API      | http://localhost:8000         |
| Doc API  | http://localhost:8000/docs    |
| Mailpit  | http://localhost:8025         |

Les migrations Alembic sont appliquées au démarrage de l'API.

## Commandes utiles

| Commande    | Effet                                   |
| ----------- | --------------------------------------- |
| `make up`   | Construit et lance la stack             |
| `make down` | Arrête la stack                         |
| `make logs` | Suit les logs                           |
| `make test` | Tests backend (pytest)                  |
| `make e2e`  | Tests de bout en bout (Playwright)      |

## Production

Voir l'en-tête de `docker-compose.prod.yml` :

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Modèle de données](docs/data-model.md)
- [Déploiement sur vlldnt.fr](docs/deployment.md)
- [Contribuer](CONTRIBUTING.md)
