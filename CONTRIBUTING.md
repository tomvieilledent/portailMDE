# Contribuer

## Workflow

1. Une issue = une branche = une PR.
2. Nom de branche : `<type>/<n°issue>-<slug>` (ex. `feat/5-auth-jwt`).
3. Rebase sur `main` avant d'ouvrir la PR ; la PR référence l'issue (`Closes #n`).

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) : `<type>[scope][!]: <description>` à l'impératif.
Types : `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `style`, `build`, `ci`, `perf`, `revert`.
Un commit = un seul type de changement.

## Qualité

```bash
pip install pre-commit && pre-commit install --install-hooks -t pre-commit -t commit-msg
```

- Backend : ruff (lint + format), pytest.
- Frontend : ESLint, Prettier, Vitest.
