# backend/src/shared_kernel/domain/ports.py

from abc import ABC, abstractmethod


class SMSGatewayPort(ABC):
    """
    Port d'architecture hexagonale pour l'envoi de SMS transactionnels critiques.
    Permet d'abstraire le fournisseur réel (Africa's Talking, Twilio, passerelle locale).
    """

    @abstractmethod
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Envoie un SMS au numéro indiqué. Retourne True en cas de succès."""
        pass
