from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import time
import uuid


class EffectType(str, Enum):
    MOTION_GRAPHICS = "motion_graphics"
    UPSCALING = "upscaling"
    STYLE_TRANSFER = "style_transfer"
    COLOR_GRADING = "color_grading"
    BACKGROUND_REMOVAL = "background_removal"
    SLOW_MOTION = "slow_motion"
    STABILIZATION = "stabilization"
    AUTO_CAPTION = "auto_caption"


class AIModel(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    AUTO = "auto"


class VideoStatus(str, Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class VideoMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_name: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    status: VideoStatus = VideoStatus.UPLOADED
    ipfs_cid: Optional[str] = None
    ipfs_url: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    effects_applied: list[str] = Field(default_factory=list)


class EffectRequest(BaseModel):
    video_id: str
    effect_type: EffectType
    ai_model: AIModel = AIModel.AUTO
    parameters: dict = Field(default_factory=dict)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)


class EffectResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    effect_type: EffectType
    ai_model: AIModel
    status: VideoStatus
    output_video_id: Optional[str] = None
    ai_response: Optional[dict] = None
    processing_time_ms: Optional[float] = None
    created_at: float = Field(default_factory=time.time)


class PinRequest(BaseModel):
    video_id: str
    name: Optional[str] = None


class PinResponse(BaseModel):
    video_id: str
    ipfs_cid: str
    ipfs_url: str
    pinata_id: str
    size_bytes: int


class CheckoutRequest(BaseModel):
    plan: PlanTier
    success_url: str
    cancel_url: str


class PricingPlan(BaseModel):
    tier: PlanTier
    name: str
    price_inr: int
    price_display: str
    features: list[str]
    max_video_size_mb: int
    max_monthly_exports: int
    ai_models_available: list[str]


class SubscriptionStatus(BaseModel):
    tier: PlanTier
    active: bool
    exports_used: int
    exports_limit: int
    storage_used_mb: float
    storage_limit_mb: float


class TimelineTrack(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    start_time: float = 0.0
    end_time: Optional[float] = None
    effects: list[dict] = Field(default_factory=list)
    layer: int = 0


class ProjectData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tracks: list[TimelineTrack] = Field(default_factory=list)
    duration: float = 0.0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
