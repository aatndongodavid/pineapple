# backend/src/monetization_context/domain/services/creative_review_service.py

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from monetization_context.infrastructure.persistence.models import AdCreativeModel, AdReviewEventModel
from monetization_context.domain.services.ad_policy_engine import AdPolicyEngine

logger = logging.getLogger("CreativeReviewService")


class CreativeReviewService:
    """
    Service de gestion de la modération des créations publicitaires.
    """

    def __init__(self, db: AsyncSession, auto_approve_safe: bool = False):
        self.db = db
        self.policy_engine = AdPolicyEngine()
        self.auto_approve_safe = auto_approve_safe

    async def submit_creative_for_review(
        self,
        campaign_id: uuid.UUID,
        headline: str,
        body_text: str,
        target_url: Optional[str] = None,
        image_url: Optional[str] = None,
        cta_text: str = "En savoir plus",
    ) -> Tuple[AdCreativeModel, bool, str]:
        """
        Soumet une création publicitaire à la modération.
        Exécute la vérification automatique des politiques (Gate R3, R6).
        Retourne (creative, is_approved_or_pending, message).
        """
        # 1. Validation de l'URL cible (Gate R6)
        url_ok, url_reason = self.policy_engine.validate_target_url(target_url)
        if not url_ok:
            creative = AdCreativeModel(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                headline=headline,
                body_text=body_text,
                image_url=image_url,
                target_url=target_url,
                cta_text=cta_text,
                review_status="REJECTED",
                rejection_reason=url_reason,
                is_active=False,
            )
            self.db.add(creative)
            
            review_event = AdReviewEventModel(
                id=uuid.uuid4(),
                creative_id=creative.id,
                previous_status="DRAFT",
                new_status="REJECTED",
                reason=url_reason,
            )
            self.db.add(review_event)
            await self.db.flush()
            return creative, False, f"Rejeté automatiquement : {url_reason}"

        # 2. Validation du contenu (mots-clés / catégories interdites) (Gate R3)
        content_ok, content_reason = self.policy_engine.evaluate_content(headline, body_text)
        if not content_ok:
            creative = AdCreativeModel(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                headline=headline,
                body_text=body_text,
                image_url=image_url,
                target_url=target_url,
                cta_text=cta_text,
                review_status="REJECTED",
                rejection_reason=content_reason,
                is_active=False,
            )
            self.db.add(creative)

            review_event = AdReviewEventModel(
                id=uuid.uuid4(),
                creative_id=creative.id,
                previous_status="DRAFT",
                new_status="REJECTED",
                reason=content_reason,
            )
            self.db.add(review_event)
            await self.db.flush()
            return creative, False, f"Rejeté automatiquement : {content_reason}"

        # 3. Validation automatique réussie -> PENDING_REVIEW (ou APPROVED si auto_approve_safe)
        initial_status = "APPROVED" if self.auto_approve_safe else "PENDING_REVIEW"
        creative = AdCreativeModel(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            headline=headline,
            body_text=body_text,
            image_url=image_url,
            target_url=target_url,
            cta_text=cta_text,
            review_status=initial_status,
            rejection_reason=None,
            is_active=(initial_status == "APPROVED"),
        )
        self.db.add(creative)

        review_event = AdReviewEventModel(
            id=uuid.uuid4(),
            creative_id=creative.id,
            previous_status="DRAFT",
            new_status=initial_status,
            reason="Validation automatique des politiques réussie",
        )
        self.db.add(review_event)
        await self.db.flush()
        return creative, True, f"Création soumise avec succès (Statut: {initial_status})"

    async def review_creative_by_admin(
        self,
        creative_id: uuid.UUID,
        reviewer_user_id: uuid.UUID,
        new_status: str,
        reason: Optional[str] = None,
    ) -> AdCreativeModel:
        """
        Modération manuelle par un administrateur / modérateur plateforme.
        new_status: 'APPROVED' ou 'REJECTED'
        """
        if new_status not in ["APPROVED", "REJECTED"]:
            raise ValueError("Le nouveau statut doit être 'APPROVED' ou 'REJECTED'.")

        creative = await self.db.get(AdCreativeModel, creative_id)
        if not creative:
            raise ValueError("Création introuvable.")

        old_status = creative.review_status
        creative.review_status = new_status
        creative.is_active = (new_status == "APPROVED")
        if new_status == "REJECTED":
            creative.rejection_reason = reason or "Non conforme aux directives éditoriales."

        event = AdReviewEventModel(
            id=uuid.uuid4(),
            creative_id=creative_id,
            reviewer_user_id=reviewer_user_id,
            previous_status=old_status,
            new_status=new_status,
            reason=reason or ("Approuvé par le modérateur" if new_status == "APPROVED" else creative.rejection_reason),
        )
        self.db.add(event)
        await self.db.flush()
        logger.info(f"Création {creative_id} modérée par {reviewer_user_id}: {old_status} -> {new_status}")
        return creative
