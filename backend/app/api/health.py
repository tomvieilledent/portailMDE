"""Route de santé utilisée par la supervision et les healthchecks."""

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    """Indique que l'API répond."""
    return {"status": "ok"}
