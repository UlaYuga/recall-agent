from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ImageToVideoRequest:
    model: Literal["gen4.5", "gen4_turbo"]
    prompt_image: str
    prompt_text: str = ""
    ratio: str = "1280:720"
    duration: Literal[5, 10] = 10


@dataclass
class TextToImageRequest:
    model: Literal["gen4_image_turbo", "gen4_image"]
    prompt_text: str
    ratio: str = "1280:720"
    reference_images: list[dict] = field(default_factory=list)


@dataclass
class TTSRequest:
    prompt_text: str
    voice_preset_id: str = "Maya"
    model: Literal["eleven_multilingual_v2"] = "eleven_multilingual_v2"


@dataclass
class RunwayTask:
    id: str
    status: Literal["PENDING", "THROTTLED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"]
    output: list[str] | None = None
    failure: str | None = None
    failure_code: str | None = None
    progress: float | None = None
