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
