from __future__ import annotations

import os

import httpx
import runwayml

from app.runway.schemas import ImageToVideoRequest, RunwayTask, TTSRequest, TextToImageRequest


class RunwayConfigError(Exception):
    """RUNWAYML_API_SECRET is not set."""


class RunwayTaskError(Exception):
    """A Runway generation task finished in FAILED state."""

    def __init__(self, message: str, failure_code: str | None = None) -> None:
        super().__init__(message)
        self.failure_code = failure_code


class RunwayAPIError(Exception):
    """Runway SDK or network error unrelated to task failure."""


class RunwayClient:
    def __init__(self) -> None:
        if not os.environ.get("RUNWAYML_API_SECRET"):
            raise RunwayConfigError(
                "RUNWAYML_API_SECRET is not set. "
                "Add it to your .env file before initializing RunwayClient."
            )
        self._sdk = runwayml.RunwayML()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def create_image_to_video(self, request: ImageToVideoRequest) -> str:
        """Submit an image-to-video task. Returns the Runway task ID."""
        try:
            response = self._sdk.image_to_video.create(
                model=request.model,
                prompt_image=request.prompt_image,
                prompt_text=request.prompt_text or runwayml.omit,
                ratio=request.ratio,
                duration=request.duration,
            )
            return response.id
        except (runwayml.APIStatusError, runwayml.APIConnectionError, runwayml.APITimeoutError) as exc:
            raise RunwayAPIError(f"Runway API error: {exc}") from exc

    def create_text_to_image(self, request: TextToImageRequest) -> str:
        """Submit a text-to-image task. Returns the Runway task ID."""
        try:
            kwargs: dict = dict(
                model=request.model,
                prompt_text=request.prompt_text,
                ratio=request.ratio,
            )
            if request.reference_images:
                kwargs["reference_images"] = request.reference_images
            response = self._sdk.text_to_image.create(**kwargs)
            return response.id
        except (runwayml.APIStatusError, runwayml.APIConnectionError, runwayml.APITimeoutError) as exc:
            raise RunwayAPIError(f"Runway API error: {exc}") from exc

    def create_tts(self, request: TTSRequest) -> str:
        """Submit a text-to-speech task. Returns the Runway task ID."""
        try:
            response = self._sdk.text_to_speech.create(
                model=request.model,
                prompt_text=request.prompt_text,
                voice={"preset_id": request.voice_preset_id, "type": "runway-preset"},
            )
            return response.id
        except (runwayml.APIStatusError, runwayml.APIConnectionError, runwayml.APITimeoutError) as exc:
            raise RunwayAPIError(f"Runway API error: {exc}") from exc

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> RunwayTask:
        """Retrieve the current status of a Runway task."""
        try:
            raw = self._sdk.tasks.retrieve(task_id)
        except runwayml.TaskFailedError as exc:
            raise RunwayTaskError(str(exc)) from exc
        except (runwayml.APIStatusError, runwayml.APIConnectionError, runwayml.APITimeoutError) as exc:
            raise RunwayAPIError(f"Runway API error: {exc}") from exc

        return RunwayTask(
            id=raw.id,
            status=raw.status,
            output=getattr(raw, "output", None),
            failure=getattr(raw, "failure", None),
            failure_code=getattr(raw, "failure_code", None),
            progress=getattr(raw, "progress", None),
        )

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_output(self, output_url: str) -> bytes:
        """Download a task output from a Runway-signed URL."""
        try:
            response = httpx.get(output_url, follow_redirects=True, timeout=120)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as exc:
            raise RunwayAPIError(f"Failed to download Runway output: {exc}") from exc
