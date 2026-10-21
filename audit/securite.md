# Audit Sécurité

## Tour 1 — note : 55/100
À corriger :
- [majeur] backend/app/api/v1/auth.py:20 — aucune limitation de débit sur login, forgot-password, reset-password (force brute, spam d'emails) → rate limiting par IP/email (ex. slowapi ou nginx limit_req) et verrouillage temporaire
- [majeur] backend/app/api/v1/users.py:66 — tout utilisateur authentifié lit le profil complet d'un autre (email, téléphone, rôle, permissions, is_active) → réserver à MANAGE_USERS/soi-même/admin d'entreprise, ou renvoyer le schéma public de l'annuaire
- [majeur] backend/app/schemas/company.py:33, training.py:75, news.py:30 (+ rendu href dans CompanyPage.jsx:51, TrainingPage.jsx:61, NewsPage.jsx:68) — URLs libres non validées : `javascript:` possible (XSS stocké) → valider http/https côté schémas (HttpUrl ou validateur) et filtrer au rendu
- [mineur] backend/app/services/auth.py:141 et users.py:change_password — changement/réinitialisation du mot de passe ne révoque pas les jetons refresh/access existants → invalider les sessions (champ token_version ou révocation par utilisateur)
- [mineur] frontend/nginx.conf:38 — pas de Content-Security-Policy ni de HSTS, Permissions-Policy absente → ajouter CSP stricte, HSTS (derrière TLS), Permissions-Policy
- [mineur] frontend/src/lib/tokens.js:26 et api/v1/ws.py:17 — JWT en localStorage (exposé en cas de XSS) et jeton WebSocket dans l'URL (journaux) → cookie HttpOnly ou jeton WS à usage unique/éphémère ; ne pas logger la query string
- [mineur] backend/app/services/storage.py:72 — documents (pdf, office, txt, csv) acceptés sur la seule extension, sans contrôle du contenu, servis publiquement (trainings) → vérifier signatures, forcer Content-Disposition: attachment sur /uploads
- [mineur] backend/app/api/v1/ws.py:27 — pas de contrôle d'Origin ni de limite de taille/débit des messages WebSocket → vérifier Origin et borner receive_text
Corrigé depuis le tour précédent : sans objet (premier tour). Points sains : Argon2, secret JWT refusé en production, rotation/révocation des refresh, anti-timing au login, uploads à nom aléatoire avec magic bytes pour images, pièces jointes de chat authentifiées, ORM sans SQL brut, `npm audit` : 0 vulnérabilité (pip-audit non disponible).
Corrections appliquées : rate limiting auth (IP + verrou par email, 429), GET /users/{id} restreint, URLs http(s) validées + safeHref au rendu, sessions révoquées via empreinte du mot de passe (change/reset), CSP/HSTS/Permissions-Policy (script de thème externalisé), signatures des documents + attachment/nosniff sur /uploads, Origin + taille/débit WebSocket.
Non corrigé : JWT en localStorage / jeton WS dans l'URL — passage aux cookies HttpOnly ou jeton WS éphémère = refonte d'architecture auth (backend + frontend), hors périmètre d'un correctif minimal.

## Tour 2 — note : 94/100
À corriger :
- [mineur] frontend/nginx.conf:20,28 — les `add_header` des blocs `location /uploads/` et `/assets/` annulent l'héritage des en-têtes de sécurité du bloc `server` (CSP, HSTS, nosniff, X-Frame-Options absents sur ces réponses) → répéter les en-têtes dans ces locations (ou un `include` commun)
- [mineur] frontend/src/lib/tokens.js:26 et api/v1/ws.py:17 — JWT en localStorage et jeton WebSocket dans l'URL (reporté au tour 1, refonte auth) → cookie HttpOnly ou jeton WS éphémère ; atténué par la CSP stricte, à ne pas logger la query string
Corrigé depuis le tour précédent : rate limiting auth (IP + verrou par email, 429), GET /users/{id} restreint, URLs http(s) validées (HttpUrlStr + safeHref), sessions révoquées au changement/reset de mot de passe, CSP/HSTS/Permissions-Policy, signatures des documents + attachment/nosniff sur /uploads, Origin + taille/débit WebSocket. Aucune régression trouvée ; `npm audit` : 0 vulnérabilité. Note : limiteur en mémoire, valable pour un seul worker (documenté).
