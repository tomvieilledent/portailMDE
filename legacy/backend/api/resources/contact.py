"""Public contact form endpoint — emails submissions to a configured inbox."""

from flask import request
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.services import mailer

# Subjects offered by the frontend contact form.
SUBJECT_LABELS = {
    'incubateur': 'Incubateur',
    'pepiniere': "Pépinière d'entreprises",
    'hotel': "Hôtel d'entreprises",
    'location': 'Location de bureaux',
    'autre': 'Autre demande',
}


class ContactResource(Resource):
    """Receive a contact-form submission and forward it by email."""

    def post(self):
        """Validate the contact form and email it to ``CONTACT_RECIPIENT``.

        Expected JSON body:
            name (str): Sender full name.
            email (str): Sender email address (used as Reply-To).
            subject (str): One of the predefined subject keys, or free text.
            message (str): Message body.
            phone (str | None): Optional phone number.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200 on success.
        """
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        subject = (data.get('subject') or '').strip()
        message = (data.get('message') or '').strip()
        phone = (data.get('phone') or '').strip()

        missing = [f for f, v in (('name', name), ('email', email),
                                  ('subject', subject), ('message', message)) if not v]
        if missing:
            return error_response(
                ERROR_CODES['VALIDATION_ERROR'],
                f"champs requis manquants: {', '.join(missing)}", 400)
        if '@' not in email or '.' not in email.split('@')[-1]:
            return error_response(ERROR_CODES['VALIDATION_ERROR'],
                                  'adresse email invalide', 400)

        recipient = mailer.contact_recipient()
        if not recipient:
            # No inbox configured yet — accept silently rather than 500.
            return {'msg': 'message reçu'}

        subject_label = SUBJECT_LABELS.get(subject, subject)
        mail_subject = f'[Contact MDE] {subject_label} — {name}'
        text_body = (
            f"Nouveau message depuis le formulaire de contact.\n\n"
            f"Nom     : {name}\n"
            f"Email   : {email}\n"
            f"Téléphone : {phone or '—'}\n"
            f"Sujet   : {subject_label}\n\n"
            f"Message :\n{message}\n"
        )
        html_body = (
            "<div style=\"font-family:Arial,sans-serif;color:#1f2937;line-height:1.6\">"
            "<h2 style=\"color:#1a3a2a\">Nouveau message de contact</h2>"
            f"<p><strong>Nom :</strong> {name}<br>"
            f"<strong>Email :</strong> {email}<br>"
            f"<strong>Téléphone :</strong> {phone or '—'}<br>"
            f"<strong>Sujet :</strong> {subject_label}</p>"
            f"<p style=\"white-space:pre-wrap;border-left:3px solid #1a3a2a;padding-left:12px\">"
            f"{message}</p></div>"
        )
        mailer.send_email(recipient, mail_subject, text_body,
                          html_body=html_body, reply_to=email)
        return {'msg': 'message envoyé'}
