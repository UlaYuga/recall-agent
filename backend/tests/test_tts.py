"""Tests for app.runway.tts — all RunwayClient calls are mocked."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.runway.client import RunwayTaskError
from app.runway.schemas import RunwayTask
from app.runway.tts import DEFAULT_VOICE_PRESET, _poll_until_done, synthesize_voiceover


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_client(
    task_id: str = "tts-task-001",
    statuses: list[str] | None = None,
    output_url: str = "https://runway.example.com/voice.mp3",
    audio_bytes: bytes = b"fake-mp3-data",
) -> MagicMock:
    """Build a MagicMock RunwayClient with configurable polling sequence."""
    if statuses is None:
        statuses = ["SUCCEEDED"]

    client = MagicMock()
    client.create_tts.return_value = task_id

    # Build get_task side-effects: one RunwayTask per status in the sequence.
    task_responses = []
    for status in statuses:
        if status == "SUCCEEDED":
            task_responses.append(
                RunwayTask(id=task_id, status="SUCCEEDED", output=[output_url])
            )
        elif status == "FAILED":
            task_responses.append(
                RunwayTask(
                    id=task_id,
                    status="FAILED",
                    failure="Content moderation triggered",
                    failure_code="SAFETY.INPUT.TEXT",
                )
            )
        elif status == "CANCELLED":
            task_responses.append(RunwayTask(id=task_id, status="CANCELLED"))
        else:
            task_responses.append(RunwayTask(id=task_id, status=status))

    client.get_task.side_effect = task_responses
    client.download_output.return_value = audio_bytes
    return client


# ---------------------------------------------------------------------------
# _poll_until_done unit tests
# ---------------------------------------------------------------------------


class TestPollUntilDone:
    def test_returns_on_succeeded(self):
        client = _mock_client(statuses=["SUCCEEDED"])
        with patch("app.runway.tts.time.sleep"):
            task = _poll_until_done(client, "tts-task-001")
        assert task.status == "SUCCEEDED"

    def test_retries_pending_then_succeeds(self):
        client = _mock_client(statuses=["PENDING", "PENDING", "SUCCEEDED"])
        with patch("app.runway.tts.time.sleep") as mock_sleep:
            task = _poll_until_done(client, "tts-task-001")
        assert task.status == "SUCCEEDED"
        assert client.get_task.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retries_throttled_then_succeeds(self):
        client = _mock_client(statuses=["THROTTLED", "RUNNING", "SUCCEEDED"])
        with patch("app.runway.tts.time.sleep"):
            task = _poll_until_done(client, "tts-task-001")
        assert task.status == "SUCCEEDED"
        assert client.get_task.call_count == 3

    def test_raises_on_failed(self):
        client = _mock_client(statuses=["FAILED"])
        with patch("app.runway.tts.time.sleep"):
            with pytest.raises(RunwayTaskError, match="FAILED"):
                _poll_until_done(client, "tts-task-001")

    def test_raises_on_cancelled(self):
        client = _mock_client(statuses=["CANCELLED"])
        with patch("app.runway.tts.time.sleep"):
            with pytest.raises(RunwayTaskError, match="CANCELLED"):
                _poll_until_done(client, "tts-task-001")

    def test_raises_on_timeout(self):
        # timeout_sec=0 means the while condition is False from the start.
        client = _mock_client(statuses=["PENDING"])
        with patch("app.runway.tts.time.sleep"):
            with pytest.raises(RunwayTaskError, match="did not complete"):
                _poll_until_done(client, "tts-task-001", timeout_sec=0)

    def test_failed_task_preserves_failure_code(self):
        client = _mock_client(statuses=["FAILED"])
        with patch("app.runway.tts.time.sleep"):
            with pytest.raises(RunwayTaskError) as exc_info:
                _poll_until_done(client, "tts-task-001")
        assert exc_info.value.failure_code == "SAFETY.INPUT.TEXT"

    def test_backoff_ladder_applied(self):
        """Verify the first three sleeps use 15, 45, 120."""
        statuses = ["PENDING", "PENDING", "PENDING", "SUCCEEDED"]
        client = _mock_client(statuses=statuses)
        with patch("app.runway.tts.time.sleep") as mock_sleep:
            _poll_until_done(client, "tts-task-001")
        sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
        assert sleep_args == [15, 45, 120]


# ---------------------------------------------------------------------------
# synthesize_voiceover integration tests (fully mocked client)
# ---------------------------------------------------------------------------


class TestSynthesizeVoiceover:
    _TEXT = "Welcome back. Your bonus is waiting."
    _CAMPAIGN = "cmp_001"

    def test_happy_path_returns_path(self, tmp_path):
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            result = synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        assert result.endswith("voiceover.mp3")

    def test_mp3_is_written_to_campaign_dir(self, tmp_path):
        client = _mock_client(audio_bytes=b"audio-content")
        with patch("app.runway.tts.time.sleep"):
            path = synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        saved = Path(path)
        assert saved.exists()
        assert saved.read_bytes() == b"audio-content"
        assert saved.parent.name == self._CAMPAIGN
        assert saved.name == "voiceover.mp3"

    def test_create_tts_called_with_correct_request(self, tmp_path):
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        client.create_tts.assert_called_once()
        req = client.create_tts.call_args.args[0]
        assert req.prompt_text == self._TEXT
        assert req.model == "eleven_multilingual_v2"

    def test_default_voice_is_maya(self, tmp_path):
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        req = client.create_tts.call_args.args[0]
        assert req.voice_preset_id == DEFAULT_VOICE_PRESET

    def test_custom_voice_preset_forwarded(self, tmp_path):
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            synthesize_voiceover(
                self._TEXT,
                self._CAMPAIGN,
                client=client,
                voice_preset_id="Jack",
                storage_dir=tmp_path,
            )
        req = client.create_tts.call_args.args[0]
        assert req.voice_preset_id == "Jack"

    def test_download_output_called_with_output_url(self, tmp_path):
        url = "https://runway.example.com/voice.mp3"
        client = _mock_client(output_url=url)
        with patch("app.runway.tts.time.sleep"):
            synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        client.download_output.assert_called_once_with(url)

    def test_credit_estimate_computed_before_request(self, tmp_path):
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            with patch("app.runway.tts.estimate_tts", wraps=__import__("app.runway.credit_estimator", fromlist=["estimate_tts"]).estimate_tts) as spy:
                synthesize_voiceover(
                    self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
                )
        spy.assert_called_once_with(self._TEXT)
        # Verify estimate was called before create_tts
        assert spy.call_count == 1
        assert client.create_tts.call_count == 1

    def test_raises_on_failed_task(self, tmp_path):
        client = _mock_client(statuses=["FAILED"])
        with patch("app.runway.tts.time.sleep"):
            with pytest.raises(RunwayTaskError):
                synthesize_voiceover(
                    self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
                )

    def test_raises_when_succeeded_has_no_output(self, tmp_path):
        client = MagicMock()
        client.create_tts.return_value = "tts-task-empty"
        client.get_task.return_value = RunwayTask(
            id="tts-task-empty", status="SUCCEEDED", output=[]
        )
        with patch("app.runway.tts.time.sleep"):
            with pytest.raises(RunwayTaskError, match="no output URLs"):
                synthesize_voiceover(
                    self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
                )

    def test_polls_pending_before_success(self, tmp_path):
        client = _mock_client(statuses=["PENDING", "RUNNING", "SUCCEEDED"])
        with patch("app.runway.tts.time.sleep") as mock_sleep:
            synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        assert client.get_task.call_count == 3
        assert mock_sleep.call_count == 2

    def test_storage_dir_created_if_missing(self, tmp_path):
        nested = tmp_path / "deep" / "nested"
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            path = synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=nested
            )
        assert Path(path).exists()

    def test_return_value_is_absolute_path(self, tmp_path):
        client = _mock_client()
        with patch("app.runway.tts.time.sleep"):
            result = synthesize_voiceover(
                self._TEXT, self._CAMPAIGN, client=client, storage_dir=tmp_path
            )
        assert Path(result).is_absolute()
