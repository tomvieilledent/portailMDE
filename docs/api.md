# API

Préfixe `/api/v1`. Documentation interactive (OpenAPI) : `http://localhost:8000/docs`.
Authentification : en-tête `Authorization: Bearer <access_token>`.

| Domaine         | Routes principales                                                                 |
| --------------- | ---------------------------------------------------------------------------------- |
| `auth`          | `POST /auth/login`, `/refresh`, `/logout`, `/forgot-password`, `/reset-password`   |
| `users`         | `GET/POST /users`, `GET/PATCH /users/me`, `/users/{id}` (+ `deactivate`, `reactivate`, `role`, `company-admin`, avatar, carte de visite) |
| `companies`     | `GET/POST /companies`, `GET /companies/me`, `/companies/{id}` (+ membres, logo, activation) |
| `directory`     | `GET /directory/people`, `GET /directory/companies`                                |
| `chat`          | `/conversations` (+ participants, `read`, `messages`), `DELETE /messages/{id}`, `GET /messages/{id}/file` |
| `events`        | `/events`, `GET /events/export.ics`, invitations (`/events/{id}/invitations`, `/invitations/me`, `respond`, `read`) |
| `trainings`     | `/trainings` (+ sessions, intérêt, documents, image), `/training-sessions` (+ inscriptions) |
| `news`          | `/news` (+ `sync`, `saved`, `save`), `/content/{key}` (contenu de la page d'accueil) |
| `notifications` | `GET /notifications`, `unread-count`, `read-all`, `broadcast`, `{id}/read`          |
| WebSocket       | Temps réel (messages, notifications) : voir `backend/app/api/v1/ws.py`              |

Les listes paginées renvoient un objet `Page` (éléments et total). Les erreurs suivent le format défini dans `backend/app/core/errors.py`.
