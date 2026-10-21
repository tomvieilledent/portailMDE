#!/bin/sh
# Applique les migrations Alembic avant de lancer la commande du conteneur.
set -e
alembic upgrade head
exec "$@"
