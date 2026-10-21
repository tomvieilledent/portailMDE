"""Tests des téléversements : avatar, carte de visite, logo et stockage de fichiers."""

import io
from pathlib import Path

import pytest

from app.services import storage

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def files(content=PNG, name="photo.png"):
    """Construit le dictionnaire de fichier pour une requête multipart."""
    return {"file": (name, io.BytesIO(content), "application/octet-stream")}


def test_upload_avatar_and_serve(client, make_user, login, upload_dir):
    """Téléverse un avatar puis le sert."""
    make_user()
    headers = login()
    response = client.put("/api/v1/users/me/avatar", headers=headers, files=files())
    assert response.status_code == 200
    path = response.json()["avatar_path"]
    assert path.startswith("avatars/") and path.endswith(".png")
    assert (upload_dir / path).read_bytes() == PNG
    assert client.get(f"/uploads/{path}").content == PNG


def test_replacing_avatar_deletes_old_file(client, make_user, login, upload_dir):
    """Remplacer l'avatar supprime l'ancien fichier."""
    make_user()
    headers = login()
    first = client.put("/api/v1/users/me/avatar", headers=headers, files=files()).json()
    second = client.put("/api/v1/users/me/avatar", headers=headers, files=files()).json()
    assert first["avatar_path"] != second["avatar_path"]
    assert not (upload_dir / first["avatar_path"]).exists()


@pytest.mark.parametrize(
    ("content", "name", "status"),
    [
        (b"not an image", "fake.png", 400),
        (PNG, "script.exe", 400),
        (b"", "empty.png", 400),
        (PNG + b"0" * (5 * 1024 * 1024), "big.png", 413),
    ],
)
def test_rejects_bad_images(client, make_user, login, content, name, status):
    """Les images invalides, vides ou trop grandes sont rejetées."""
    make_user()
    response = client.put("/api/v1/users/me/avatar", headers=login(), files=files(content, name))
    assert response.status_code == status


def test_business_card(client, make_user, login):
    """Téléversement d'une carte de visite."""
    make_user()
    response = client.put("/api/v1/users/me/business-card", headers=login(), files=files())
    assert response.json()["business_card_path"].startswith("business-cards/")


def test_cannot_set_other_users_avatar(client, make_user, login):
    """Impossible de modifier l'avatar d'un autre utilisateur."""
    make_user()
    other = make_user("o@x.fr")
    response = client.put(f"/api/v1/users/{other.id}/avatar", headers=login(), files=files())
    assert response.status_code == 403


def test_company_logo_permissions(client, make_user, make_company, login):
    """Seul l'admin de l'entreprise peut changer son logo."""
    mine, other = make_company("Mine"), make_company("Other")
    make_user(company_id=mine.id, is_company_admin=True)
    headers = login()
    ok = client.put(f"/api/v1/companies/{mine.id}/logo", headers=headers, files=files())
    assert ok.json()["logo_path"].startswith("logos/")
    ko = client.put(f"/api/v1/companies/{other.id}/logo", headers=headers, files=files())
    assert ko.status_code == 403


def test_upload_requires_auth(client):
    """Le téléversement exige une authentification."""
    assert client.put("/api/v1/users/me/avatar", files=files()).status_code == 401


def test_delete_file_stays_inside_root(upload_dir):
    """La suppression de fichier reste confinée au dossier racine."""
    outside = Path(upload_dir).parent / "keep.txt"
    outside.write_text("x")
    storage.delete_file("../keep.txt")
    assert outside.exists()


def test_save_document(upload_dir):
    """Enregistrement d'un document PDF."""

    class Upload:
        """Faux fichier téléversé pour le test."""

        filename = "notes.pdf"
        file = io.BytesIO(b"%PDF-1.4")

    path, name = storage.save_document(Upload(), "documents")
    assert path.endswith(".pdf") and name == "notes.pdf"
