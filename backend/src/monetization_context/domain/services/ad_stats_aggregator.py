# backend/src/monetization_context/domain/services/ad_stats_aggregator.py

import logging
import uuid
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from monetization_context.infrastructure.persistence.models import (
    AdStatsDailyModel, AdCampaignModel, AdCreativeModel, AdImpressionRawModel, AdEventModel
)

logger = logging.getLogger("AdStatsAggregatorService")


class AdStatsAggregatorService:
    """
    Service d'agrégation quotidienne des statistiques de diffusion (Gate R12).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def increment_daily_stat(
        self,
        campaign_id: uuid.UUID,
        creative_id: uuid.UUID,
        stat_date: str,
        impressions_delta: int = 0,
        clicks_delta: int = 0,
        spent_delta_xaf: int = 0,
    ) -> AdStatsDailyModel:
        """
        Incrémente atomiquement le registre journalier des statistiques pour un visuel et une date donnés.
        """
        stmt = select(AdStatsDailyModel).where(
            AdStatsDailyModel.campaign_id == campaign_id,
            AdStatsDailyModel.creative_id == creative_id,
            AdStatsDailyModel.stat_date == stat_date,
        )
        res = await self.db.execute(stmt)
        stat_record = res.scalars().first()

        if not stat_record:
            stat_record = AdStatsDailyModel(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                creative_id=creative_id,
                stat_date=stat_date,
                impressions_count=impressions_delta,
                clicks_count=clicks_delta,
                spent_xaf=spent_delta_xaf,
            )
            self.db.add(stat_record)
        else:
            stat_record.impressions_count += impressions_delta
            stat_record.clicks_count += clicks_delta
            stat_record.spent_xaf += spent_delta_xaf

        await self.db.flush()
        return stat_record

    async def get_campaign_stats(
        self,
        campaign_id: uuid.UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Récupère les statistiques agrégées pour une campagne donnée.
        """
        stmt = select(AdStatsDailyModel).where(AdStatsDailyModel.campaign_id == campaign_id)

        if start_date:
            stmt = stmt.where(AdStatsDailyModel.stat_date >= start_date)
        if end_date:
            stmt = stmt.where(AdStatsDailyModel.stat_date <= end_date)

        res = await self.db.execute(stmt)
        daily_records = res.scalars().all()

        total_impressions = sum(r.impressions_count for r in daily_records)
        total_clicks = sum(r.clicks_count for r in daily_records)
        total_spent_xaf = sum(r.spent_xaf for r in daily_records)

        ctr_percent = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0

        daily_breakdown = [
            {
                "stat_date": r.stat_date,
                "creative_id": str(r.creative_id),
                "impressions": r.impressions_count,
                "clicks": r.clicks_count,
                "spent_xaf": r.spent_xaf,
                "ctr_percent": round((r.clicks_count / r.impressions_count * 100), 2) if r.impressions_count > 0 else 0.0,
            }
            for r in daily_records
        ]

        return {
            "campaign_id": str(campaign_id),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_spent_xaf": total_spent_xaf,
            "ctr_percent": round(ctr_percent, 2),
            "daily_breakdown": daily_breakdown,
        }
