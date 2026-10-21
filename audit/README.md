# Audits

Rapports courts, un fichier par thème, un bloc par tour (audit → note → à corriger → ré-audit).

| Fichier | Auteur | Lu par |
| --- | --- | --- |
| `a11y.md`, `securite.md`, `performance.md`, `qualite.md` | agents `audit-*` | agents `fix-*`, `valideur` |
| `SYNTHESE.md` | agent `valideur` | humain |

Lancer : `/audit-loop` (agents dans `.claude/agents/`). Seuils de validation : voir `.claude/agents/valideur.md`.
