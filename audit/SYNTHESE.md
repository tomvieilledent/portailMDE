# Synthèse des audits

## Tour 1 — Globale 53/100 — Refusé
| Thème | Note | Critiques | Majeurs | Mineurs |
|---|---|---|---|---|
| Sécurité (35 %) | 55 | 0 | 3 | 5 |
| Accessibilité (25 %) | 39 | 0 | 4 | 7 |
| Qualité/RGPD (20 %) | 63 | 0 | 3 | 3 |
| Performance (20 %) | 58 | 0 | 3 | 4 |

Priorités pour le prochain tour :
1. Sécurité : rate limiting auth, restriction de lecture des profils, validation http/https des URLs libres.
2. Accessibilité : lien d'évitement, titres de page/focus au changement de route, piège de focus Modal/tiroir, contrastes slate-400.
3. RGPD/performance : mentions légales + anonymisation/export des données ; gzip nginx, lazy loading des routes, requêtes agrégées du chat.

## Tour 2 — Globale 93/100 — Validé
| Thème | Note | Critiques | Majeurs | Mineurs |
|---|---|---|---|---|
| Sécurité (35 %) | 94 | 0 | 0 | 2 |
| Accessibilité (25 %) | 88 | 0 | 0 | 4 |
| Qualité/RGPD (20 %) | 97 | 0 | 0 | 1 |
| Performance (20 %) | 94 | 0 | 0 | 2 |

Priorités pour le prochain tour :
1. Sécurité : en-têtes de sécurité répétés dans les locations nginx /uploads et /assets ; JWT localStorage/jeton WS (refonte auth, à arbitrer).
2. Accessibilité : piège de focus du tiroir mobile, titres/focus des pages hors layout ou à h1 dynamique, horodatage 11 px.
3. Qualité/performance : anonymisation des messages d'un compte supprimé ; lazy loading des images de listes, limite des conversations en SQL.

## Tour 3 — Globale 98/100 — Validé
| Thème | Note | Critiques | Majeurs | Mineurs |
|---|---|---|---|---|
| Sécurité (35 %) | 97 | 0 | 0 | 1 |
| Accessibilité (25 %) | 97 | 0 | 0 | 1 |
| Qualité/RGPD (20 %) | 100 | 0 | 0 | 0 |
| Performance (20 %) | 97 | 0 | 0 | 1 |

Priorités pour le prochain tour :
1. Sécurité : JWT en localStorage / jeton WS dans l'URL (au minimum filtrer la query string des logs d'accès).
2. Accessibilité : `useDocumentTitle('Page introuvable')` dans NotFoundPage.
3. Performance : pagination par curseur des conversations si le volume grandit.
