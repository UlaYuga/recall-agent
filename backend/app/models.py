from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class CampaignStatus(str, Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    generating = "generating"
    generation_failed = "generation_failed"
    ready = "ready"
    ready_blocked_delivery = "ready_blocked_delivery"
    delivered = "delivered"
    converted = "converted"


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(index=True, unique=True)  # canonical seed ID: p_001, p_002, …
    external_id: str = Field(index=True)
    first_name: str
    preferred_language: str = "en"
    market_language: str = ""
    country: str = ""
    currency: str = ""
    registered_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    last_deposit_at: Optional[datetime] = None
    total_deposits_count: int = 0
    total_deposits_amount: float = 0.0
    favorite_vertical: Optional[str] = None
    favorite_game_category: Optional[str] = None
    favorite_game_label: Optional[str] = None
    biggest_win_amount: Optional[float] = None
    biggest_win_currency: Optional[str] = None
    biggest_win_at: Optional[datetime] = None
    ltv_segment: str = ""
    tags: Optional[str] = None            # JSON list, e.g. '["high_value_dormant"]'
    preferred_channels: Optional[str] = None  # JSON list, e.g. '["telegram","email"]'
    # identifiers (flattened from seed JSON identifiers object)
    external_crm_id: Optional[str] = None
    email: Optional[str] = None
    phone_e164: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    push_token: Optional[str] = None
    # consent (flattened from seed JSON consent object)
    consent_marketing_communications: bool = False
    consent_marketing_email: bool = False
    consent_marketing_sms: bool = False
    consent_whatsapp_business: bool = False
    consent_push_notifications: bool = False
    consent_video_personalization: bool = False
    consent_data_processing: bool = False


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(index=True, unique=True)  # e.g. evt_0001
    player_id: str = Field(index=True)
    event_type: str
    event_at: datetime
    vertical: Optional[str] = None
    game_category: Optional[str] = None
    game_label: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    # Named metadata_json to avoid conflict with SQLAlchemy's declarative .metadata attribute
    metadata_json: Optional[str] = None  # JSON dict stored as text


class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: str = Field(index=True, unique=True)
    player_id: str = Field(index=True)
    cohort: str = ""
    status: CampaignStatus = CampaignStatus.draft
    risk_score: float = 0.0
    reasoning_json: Optional[str] = None
    offer_json: Optional[str] = None
    script_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class VideoAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: str = Field(index=True)
    runway_task_id: Optional[str] = None
    video_url: Optional[str] = None
    poster_url: Optional[str] = None
    duration_sec: Optional[float] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Delivery(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: str = Field(index=True)
    channel: str
    status: str = "pending"
    recipient: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Tracking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: str = Field(index=True)
    event_type: str  # landing_loaded / video_play / video_50_percent / cta_click / deposit_submit
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunwayTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, unique=True)
    campaign_id: str = Field(index=True)
    scene_id: Optional[str] = None
    kind: str  # text_to_image / image_to_video / tts
    model: Optional[str] = None
    status: str = "pending"
    failure_code: Optional[str] = None
    retry_count: int = 0
    output_url: Optional[str] = None
    credits_estimated: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
