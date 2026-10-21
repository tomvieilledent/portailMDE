# Audit Performance

## Tour 1 — note : 58/100
À corriger :
- [majeur] frontend/nginx.conf:1 — aucune compression gzip/brotli (bundle JS 350 Ko, CSS 32 Ko servis bruts) → activer `gzip on` + `gzip_types` (js, css, json, svg)
- [majeur] frontend/src/App.jsx:8 — toutes les pages importées statiquement, un seul chunk JS, aucun lazy loading → `React.lazy` + `Suspense` par route (admin, messagerie, agenda, formations en priorité)
- [majeur] backend/app/services/chat.py:196 — `list_conversations` fait 3 requêtes par conversation (users, dernier message, non lus) et n'est pas paginée ; rappelée à chaque événement temps réel (`RealtimeEffects.jsx`) → requêtes agrégées (sous-requêtes/window), un seul chargement des utilisateurs, pagination
- [mineur] backend/app/services/events.py:40 — `list_events` sans limite ni période obligatoire → exiger/borner start-end ou paginer
- [mineur] frontend/nginx.conf:16 — `/uploads/` sans cache ni `expires` (noms aléatoires, donc cachables) → `expires 30d; add_header Cache-Control "public"` (catégories publiques)
- [mineur] frontend/src/components/ui/Avatar.jsx:16 — images (avatars, logos, formations) sans `loading="lazy"`/`decoding="async"` → ajouter l'attribut
- [mineur] backend/app/services/news.py:182 — une requête SELECT par entrée RSS pour dédoublonner → une requête `IN (urls)` par flux
Corrigé depuis le tour précédent : (premier tour)
Corrections appliquées : gzip + cache /uploads (nginx), lazy loading des routes, list_conversations en requêtes agrégées (plafond 200), list_events plafonné à 1000, lazy/async sur Avatar, dédoublonnage RSS en une requête IN.
Non corrigé : pagination applicative de list_conversations et obligation start/end de list_events (plafonds posés à la place, pour ne pas casser l'API/le frontend) ; lazy/async limité à Avatar (autres images non listées).

## Tour 2 — note : 94/100
À corriger :
- [mineur] frontend/src/features/trainings/TrainingsPage.jsx:127 et frontend/src/features/directory/CompaniesPage.jsx:17 — images de listes sans `loading="lazy"`/`decoding="async"` → ajouter l'attribut (idem TrainingPage.jsx:176, PersonModal.jsx:65, ProfilePage.jsx:114)
- [mineur] backend/app/services/chat.py:195 — le plafond de 200 est appliqué après chargement et tri de toutes les conversations en Python → trier/limiter en SQL (ou pagination) si le volume grandit
Corrigé depuis le tour précédent : gzip nginx, cache /uploads et /assets, lazy loading des routes (React.lazy + Suspense), list_conversations en requêtes agrégées (N+1 supprimé), list_events plafonné à 1000, lazy sur Avatar, dédoublonnage RSS en une requête IN.
Corrections appliquées : lazy/async sur les 5 images, tri et plafond des conversations en SQL.

## Tour 3 — note : 97/100
À corriger :
- [mineur] backend/app/services/chat.py:223 — conversations plafonnées à 200 sans pagination réelle (acceptable au volume actuel) → ajouter offset/curseur si le volume grandit
Corrigé depuis le tour précédent : lazy/async sur les 5 images restantes (TrainingsPage, TrainingPage, CompaniesPage, PersonModal, ProfilePage), tri et plafond des conversations en SQL (order_by coalesce + limit). Aucune régression constatée (nginx gzip/cache, lazy routes, listes paginées inchangés).
