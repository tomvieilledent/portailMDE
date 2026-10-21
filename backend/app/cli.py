"""Commandes d'administration : ``python -m app.cli <commande>``."""

import argparse
import getpass
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import SessionLocal
from app.migration.legacy import LegacyImporter
from app.migration.seed import create_admin, seed_demo


def cmd_migrate_legacy(args) -> int:
    with SessionLocal() as session:
        importer = LegacyImporter(
            args.source, session, Path(args.uploads_dir) if args.uploads_dir else None
        )
        counts = importer.run()
    for label, count in sorted(counts.items()):
        print(f"{label}: {count}")
    return 0


def cmd_create_admin(args) -> int:
    password = args.password or getpass.getpass("Mot de passe : ")
    with SessionLocal() as session:
        try:
            user = create_admin(session, args.email, password, first_name=args.first_name)
        except AppError as exc:
            print(exc.message, file=sys.stderr)
            return 1
    print(f"Super administrateur créé : {user.email}")
    return 0


def cmd_seed_demo(args) -> int:
    if get_settings().environment == "production" and not args.force:
        print("Refusé en production (utilisez --force).", file=sys.stderr)
        return 1
    with SessionLocal() as session:
        result = seed_demo(session, args.password)
    print(result or "Données de démonstration déjà présentes.")
    if result:
        print(
            f"Comptes : admin@demo.fr, staff@demo.fr, lea@demo.fr… — mot de passe : {args.password}"
        )
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    legacy = sub.add_parser("migrate-legacy", help="Importer les données de l'ancienne application")
    legacy.add_argument(
        "--source", required=True, help="URL SQLAlchemy (ex. sqlite:////data/old.db)"
    )
    legacy.add_argument("--uploads-dir", help="Dossier uploads de l'ancienne application")
    legacy.set_defaults(func=cmd_migrate_legacy)

    admin = sub.add_parser("create-admin", help="Créer un super administrateur")
    admin.add_argument("--email", required=True)
    admin.add_argument("--first-name")
    admin.add_argument("--password", help="Demandé interactivement si absent")
    admin.set_defaults(func=cmd_create_admin)

    seed = sub.add_parser("seed-demo", help="Charger des données de démonstration")
    seed.add_argument("--password", default="demo-password-1")
    seed.add_argument("--force", action="store_true")
    seed.set_defaults(func=cmd_seed_demo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
