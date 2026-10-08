# backend/src/notification_context/domain/services/template_renderer.py

from typing import Dict, Any, Tuple


DEFAULT_TEMPLATES = {
    "CLASS_ANNOUNCEMENT_PUBLISHED": {
        "fr": {
            "subject": "Nouvelle annonce : {{ title }}",
            "body": "Une nouvelle annonce a été publiée dans votre classe : {{ title }}.\nConnectez-vous à Pineapple OS pour consulter l'intégralité.",
        },
        "en": {
            "subject": "New announcement: {{ title }}",
            "body": "A new announcement was posted in your class: {{ title }}.\nLog in to Pineapple OS to view details.",
        }
    },
    "COURSE_CANCELLED": {
        "fr": {
            "subject": "Alerte cours annulé : {{ target_date }}",
            "body": "Le cours prévu le {{ target_date }} a été annulé. Motif : {{ reason }}",
        },
        "en": {
            "subject": "Course cancelled alert: {{ target_date }}",
            "body": "The course scheduled on {{ target_date }} has been cancelled. Reason: {{ reason }}",
        }
    },
    "SECURITY_ALERT": {
        "fr": {
            "subject": "Alerte de sécurité Pineapple OS",
            "body": "Une connexion/action sensible ({{ alert_type }}) a été détectée depuis l'IP {{ ip_address }}.",
        },
        "en": {
            "subject": "Pineapple OS Security Alert",
            "body": "A sensitive security action ({{ alert_type }}) was detected from IP {{ ip_address }}.",
        }
    },
    "INVOICE_DUE": {
        "fr": {
            "subject": "Facture à échéance - {{ amount_xaf }} FCFA",
            "body": "Rappel : votre facture de {{ amount_xaf }} FCFA arrive à échéance le {{ due_date }}.",
        },
        "en": {
            "subject": "Invoice Due - {{ amount_xaf }} FCFA",
            "body": "Reminder: your invoice of {{ amount_xaf }} FCFA is due on {{ due_date }}.",
        }
    },
}


class TemplateRenderer:
    """
    Rend le sujet et le corps d'une notification à partir des gabarits localisés (fr/en).
    """

    @staticmethod
    def render(event_type: str, language: str, payload: Dict[str, Any]) -> Tuple[str, str]:
        lang = "fr" if language not in ("fr", "en") else language
        tmpl_group = DEFAULT_TEMPLATES.get(event_type, {}).get(lang)

        if not tmpl_group:
            title = payload.get("title", f"Notification {event_type}")
            body = payload.get("reason") or payload.get("message") or f"Détails de l'événement {event_type}"
            return title, body

        subject_template = tmpl_group["subject"]
        body_template = tmpl_group["body"]

        subject = subject_template
        body = body_template

        for k, v in payload.items():
            placeholder = "{{" + f" {k} " + "}}"
            placeholder_no_space = "{{" + k + "}}"
            subject = subject.replace(placeholder, str(v)).replace(placeholder_no_space, str(v))
            body = body.replace(placeholder, str(v)).replace(placeholder_no_space, str(v))

        return subject, body
