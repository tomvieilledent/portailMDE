"""Configuration de la journalisation."""

import logging


def configure_logging(level: str) -> None:
    """Configure le niveau et le format des journaux."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
