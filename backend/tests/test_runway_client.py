"""Tests for app.runway.client — all Runway SDK calls are monkeypatched."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.runway.client import RunwayAPIError, RunwayClient, RunwayConfigError
from app.runway.schemas import ImageToVideoRequest, TTSRequest, TextToImageRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(monkeypatch) -> RunwayClient:
    """Return a RunwayClient with a mocked SDK and env key set."""
    monkeypatch.setenv("RUNWAYML_API_SECRET", "test-secret")
    mock_sdk = MagicMock()
    with patch("app.runway.client.runwayml.RunwayML", return_value=mock_sdk):
        client = RunwayClient()
    client._sdk = mock_sdk
    return client


# ---------------------------------------------------------------------------
# Env validation
# ---------------------------------------------------------------------------


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("RUNWAYML_API_SECRET", raising=False)
    with pytest.raises(RunwayConfigError, match="RUNWAYML_API_SECRET"):
        RunwayClient()


def test_present_api_key_initialises(monkeypatch):
    monkeypatch.setenv("RUNWAYML_API_SECRET", "test-secret")
    with patch("app.runway.client.runwayml.RunwayML") as mock_cls:
        mock_cls.return_value = MagicMock()
        client = RunwayClient()
    assert client._sdk is not None
    mock_cls.assert_called_once_with()


# ---------------------------------------------------------------------------
# create_image_to_video
# ---------------------------------------------------------------------------


def test_create_image_to_video_returns_task_id(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.image_to_video.create.return_value = SimpleNamespace(id="task-i2v-001")

    task_id = client.create_image_to_video(
        ImageToVideoRequest(
            model="gen4.5",
            prompt_image="https://example.com/frame.jpg",
            prompt_text="cinematic motion",
        )
    )

    assert task_id == "task-i2v-001"
    client._sdk.image_to_video.create.assert_called_once()


def test_create_image_to_video_sdk_error_raises_api_error(monkeypatch):
    import runwayml

    client = _make_client(monkeypatch)
    client._sdk.image_to_video.create.side_effect = runwayml.APIConnectionError(request=MagicMock())

    with pytest.raises(RunwayAPIError):
        client.create_image_to_video(
            ImageToVideoRequest(model="gen4_turbo", prompt_image="data:image/png;base64,abc")
        )


# ---------------------------------------------------------------------------
# create_text_to_image
# ---------------------------------------------------------------------------


def test_create_text_to_image_returns_task_id(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.text_to_image.create.return_value = SimpleNamespace(id="task-t2i-001")

    task_id = client.create_text_to_image(
        TextToImageRequest(
            model="gen4_image_turbo",
            prompt_text="abstract slot reels, deep purple, no text",
        )
    )

    assert task_id == "task-t2i-001"


def test_create_text_to_image_passes_reference_images(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.text_to_image.create.return_value = SimpleNamespace(id="task-t2i-002")
    refs = [{"uri": "https://example.com/palette.jpg", "tag": "brand_palette"}]

    client.create_text_to_image(
        TextToImageRequest(
            model="gen4_image_turbo",
            prompt_text="cinematic motion graphics",
            reference_images=refs,
        )
    )

    call_kwargs = client._sdk.text_to_image.create.call_args.kwargs
    assert call_kwargs["reference_images"] == refs


# ---------------------------------------------------------------------------
# create_tts
# ---------------------------------------------------------------------------


def test_create_tts_returns_task_id(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.text_to_speech.create.return_value = SimpleNamespace(id="task-tts-001")

    task_id = client.create_tts(
        TTSRequest(prompt_text="Welcome back, your bonus is waiting.")
    )

    assert task_id == "task-tts-001"
    call_kwargs = client._sdk.text_to_speech.create.call_args.kwargs
    assert call_kwargs["voice"]["type"] == "runway-preset"
    assert call_kwargs["voice"]["preset_id"] == "Maya"


def test_create_tts_custom_voice(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.text_to_speech.create.return_value = SimpleNamespace(id="task-tts-002")

    client.create_tts(TTSRequest(prompt_text="Hello.", voice_preset_id="Jack"))

    call_kwargs = client._sdk.text_to_speech.create.call_args.kwargs
    assert call_kwargs["voice"]["preset_id"] == "Jack"


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------


def test_get_task_succeeded(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.tasks.retrieve.return_value = SimpleNamespace(
        id="task-001",
        status="SUCCEEDED",
        output=["https://runway.example.com/out.mp4"],
        failure=None,
        failure_code=None,
        progress=None,
    )

    task = client.get_task("task-001")

    assert task.status == "SUCCEEDED"
    assert task.output == ["https://runway.example.com/out.mp4"]


def test_get_task_failed_normalizes_error(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.tasks.retrieve.return_value = SimpleNamespace(
        id="task-002",
        status="FAILED",
        output=None,
        failure="Content moderation triggered",
        failure_code="SAFETY.INPUT.TEXT",
        progress=None,
    )

    task = client.get_task("task-002")

    assert task.status == "FAILED"
    assert task.failure_code == "SAFETY.INPUT.TEXT"


def test_get_task_pending(monkeypatch):
    client = _make_client(monkeypatch)
    client._sdk.tasks.retrieve.return_value = SimpleNamespace(
        id="task-003",
        status="PENDING",
        output=None,
        failure=None,
        failure_code=None,
        progress=None,
    )

    task = client.get_task("task-003")

    assert task.status == "PENDING"
    assert task.output is None


def test_get_task_api_error_raises(monkeypatch):
    import runwayml

    client = _make_client(monkeypatch)
    client._sdk.tasks.retrieve.side_effect = runwayml.APIStatusError(
        "not found", response=MagicMock(status_code=404), body=None
    )

    with pytest.raises(RunwayAPIError):
        client.get_task("task-missing")


# ---------------------------------------------------------------------------
# download_output
# ---------------------------------------------------------------------------


def test_download_output_returns_bytes(monkeypatch):
    client = _make_client(monkeypatch)

    with patch("app.runway.client.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = b"binary-video-data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        data = client.download_output("https://runway.example.com/out.mp4")

    assert data == b"binary-video-data"
    mock_get.assert_called_once_with(
        "https://runway.example.com/out.mp4", follow_redirects=True, timeout=120
    )


def test_download_output_http_error_raises(monkeypatch):
    import httpx

    client = _make_client(monkeypatch)

    with patch("app.runway.client.httpx.get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("connection refused")

        with pytest.raises(RunwayAPIError, match="Failed to download"):
            client.download_output("https://runway.example.com/out.mp4")
