---
description: Boucle audit → réparation → ré-audit jusqu'à validation (max 4 tours)
---

Lance la boucle d'audit de portailMDE. Pour N = 1 à 4 :

1. En parallèle, appelle les agents `audit-a11y`, `audit-securite`, `audit-performance`, `audit-qualite` (chacun écrit son tour N dans `audit/<thème>.md`).
2. Appelle `valideur` : il écrit le tour N dans `audit/SYNTHESE.md`.
3. Verdict **Validé** → fin. **Arrêt** (tour 4) → fin et résume ce qui reste.
4. Sinon, en parallèle, appelle `fix-a11y`, `fix-securite`, `fix-performance`, `fix-qualite` pour les thèmes ayant des points « À corriger », puis reviens à l'étape 1 (ré-audit).

Règles : n'échange entre agents que via les fichiers `audit/` ; ne relis pas les rapports toi-même ; à la fin, donne uniquement la note globale par tour. Ne commite que si l'utilisateur le demande (au nom de l'utilisateur, Conventional Commits, sans trailer Co-Authored-By).
