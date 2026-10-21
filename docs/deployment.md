# Déploiement sur vlldnt.fr

Le portail est publié sur `https://portail-mde.vlldnt.fr` par l'infra du domaine (dépôt `portfolio`, runtime `compose`).

## Fonctionnement

1. Un push sur `main` lance `.github/workflows/deploy.yml` : connexion SSH au VPS puis `deploy-project.sh portail-mde`.
2. Le script vérifie que le projet est `deployed: true` dans `portfolio/projects.yml`, clone le dépôt, puis lance
   `docker compose -f docker-compose.prod.yml --env-file /opt/vlldnt/config/portail-mde.env up -d --build`.
3. Le conteneur `web` n'écoute que sur `127.0.0.1:8087` ; le nginx du VPS (TLS wildcard) est le seul point d'entrée public.
4. La landing page `landing-page/` est publiée sous `https://vlldnt.fr/portail-mde`.

## Première mise en place (une seule fois)

- DNS OVH : enregistrement `A portail-mde` → `137.74.175.164`.
- VPS : créer `/opt/vlldnt/config/portail-mde.env` (chmod 600) à partir de `.env.prod.example`.
- GitHub : secrets `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `SSH_KNOWN_HOSTS` sur ce dépôt.
- `portfolio/projects.yml` : passer `portail-mde` à `deployed: true`, puis lancer le workflow *Sync projects*.

## Exploitation

- Santé : `bash /opt/vlldnt/scripts/healthcheck.sh`
- Retour arrière : `bash /opt/vlldnt/scripts/rollback.sh portail-mde`
- Les migrations Alembic sont appliquées au démarrage de l'API.
