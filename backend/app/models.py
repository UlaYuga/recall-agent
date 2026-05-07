from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class CampaignStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"
    rendering = "rendering"
    ready = "ready"
    delivered = "delivered"
    converted = "converted"


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    name: str
    country: str
    currency: str
    preferred_language: str = "en"
    days_inactive: int
    total_deposits_amount: float = 0
    marketing_consent: bool = True
    video_personalization_consent: bool = True
    telegram_chat_id: str | None = None


class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(index=True)
    cohort: str
    status: CampaignStatus = CampaignStatus.draft
    script: str
    cta: str
    visual_prompt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrackingEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(index=True)
    event_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

