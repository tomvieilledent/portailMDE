# Modèle de données

PostgreSQL, clés primaires UUID, dates en `timestamptz`. Migrations : Alembic (`backend/alembic`).
Suppression logique (`deleted_at`) sur utilisateurs, entreprises, formations, événements et messages.

```mermaid
erDiagram
    companies ||--o{ users : "emploie"
    companies ||--o{ trainings : "propose"
    trainings ||--o{ training_sessions : "a"
    users ||--o{ training_enrollments : "s'inscrit"
    trainings ||--o{ training_enrollments : ""
    training_sessions ||--o{ training_enrollments : ""
    events ||--o{ invitations : ""
    training_sessions ||--o{ invitations : ""
    users ||--o{ invitations : "invite / invité"
    conversations ||--o{ conversation_participants : ""
    users ||--o{ conversation_participants : ""
    conversations ||--o{ messages : ""
    users ||--o{ messages : "écrit"
    users ||--o{ notifications : "reçoit"
    users ||--o{ saved_articles : "enregistre"
    news_articles ||--o{ saved_articles : ""
```

## Choix

- Rôle utilisateur : `super_admin`, `staff` (droits fins dans `permissions`), `member` ; `is_company_admin` pour l'administrateur d'une entreprise.
- Une invitation cible soit un événement, soit une session (contrainte `exactly_one_target`).
- Unicité de l'email insensible à la casse (index sur `lower(email)`).
- Non-lu du chat : `conversation_participants.last_read_at` (pas de drapeau par message).
- Favoris d'actualités : copie de l'article, conservée après purge de l'original.
- Contenu éditable (page d'accueil) : table clé/valeur JSONB `site_contents`.
