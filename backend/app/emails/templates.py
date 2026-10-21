"""Gabarits d'emails en français (texte + HTML)."""

from html import escape


def _layout(title: str, body_html: str) -> str:
    return (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">'
        f'<h2 style="color:#0f4c81">{escape(title)}</h2>{body_html}'
        '<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">'
        '<p style="font-size:12px;color:#6b7280">portailMDE — Maison de l\'Entreprise</p></div>'
    )


def reset_password(name: str, link: str, minutes: int) -> tuple[str, str, str]:
    """Retourne ``(sujet, texte, html)``."""
    subject = "Réinitialisation de votre mot de passe"
    text = (
        f"Bonjour {name},\n\nPour choisir un nouveau mot de passe, ouvrez ce lien "
        f"(valable {minutes} minutes) :\n{link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
    )
    html = _layout(
        subject,
        f"<p>Bonjour {escape(name)},</p>"
        f"<p>Pour choisir un nouveau mot de passe, cliquez sur le bouton ci-dessous "
        f"(valable {minutes} minutes).</p>"
        f'<p><a href="{escape(link)}" style="background:#0f4c81;color:#fff;padding:10px 18px;'
        'border-radius:6px;text-decoration:none">Choisir un mot de passe</a></p>'
        "<p>Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.</p>",
    )
    return subject, text, html


def welcome(name: str, link: str) -> tuple[str, str, str]:
    subject = "Bienvenue sur le portail de la Maison de l'Entreprise"
    text = (
        f"Bonjour {name},\n\nVotre compte a été créé. Connectez-vous ici : {link}\n"
        "Votre mot de passe temporaire vous a été communiqué par votre administrateur."
    )
    html = _layout(
        subject,
        f"<p>Bonjour {escape(name)},</p><p>Votre compte a été créé.</p>"
        f'<p><a href="{escape(link)}">Accéder au portail</a></p>'
        "<p>Votre mot de passe temporaire vous a été communiqué par votre administrateur.</p>",
    )
    return subject, text, html


def invitation(name: str, inviter: str, label: str, link: str) -> tuple[str, str, str]:
    subject = f"Invitation : {label}"
    text = f"Bonjour {name},\n\n{inviter} vous invite : {label}.\nRépondre : {link}"
    html = _layout(
        subject,
        f"<p>Bonjour {escape(name)},</p><p>{escape(inviter)} vous invite : "
        f"<strong>{escape(label)}</strong>.</p>"
        f'<p><a href="{escape(link)}">Répondre à l\'invitation</a></p>',
    )
    return subject, text, html
