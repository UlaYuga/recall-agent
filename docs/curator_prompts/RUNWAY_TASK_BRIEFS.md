# Runway Task Readiness Brief

## Current Runway Snapshot

- Existing files under `backend/app/runway/`: `client.py`, `tts.py`, `video_pipeline.py`.
- All three current Runway files are placeholders:
  - `backend/app/runway/client.py` defines a protocol and a `RunwayVideoProvider` stub that raises `NotImplementedError`.
  - `backend/app/runway/tts.py` exposes `synthesize_voiceover()` and raises `NotImplementedError`.
  - `backend/app/runway/video_pipeline.py` exposes `stitch_video()` and raises `NotImplementedError`.
- Missing modules expected by XLSX/research but not present yet: `schemas.py`, `prompt_safety.py`, `visual_hints.py`, `credit_estimator.py`, `task_store.py`, `stitcher.py`, `runway_smoke.py`.
- `backend/app/api/video.py` currently has only `POST /generate` returning `{"status": "queued"}`. There is no status route, no `{campaign_id}` path shape, and no background orchestration.
- `backend/app/models.py` has `CampaignStatus.rendering`, but research/handoff/spec also reference `generating`, `generation_failed`, and `ready_blocked_delivery`. No `RunwayTask` model exists yet.
- `.env.example` uses `RUNWAYML_API_SECRET`, matching Runway SDK/research conventions after T-00b reconciliation.
- XLSX assumes `backend/app/runway/video_pipeline.py` will orchestrate generation, but repo reality currently has no real client, no prompt safety, no estimator, no task persistence, no stitcher, and no `/video` integration.
- Seed-path reality already changed: future seed work must use `backend/seeds/`, not `backend/seed/`.

## Shared Runway Constraints

- API key must stay in local `.env` or deployment secrets only.
- Use env name `RUNWAYML_API_SECRET`.
- Repo mismatch resolved by T-00b: future prompts should keep `.env.example`, config and docs aligned on `RUNWAYML_API_SECRET`.
- Every Runway request must send `X-Runway-Version: 2024-11-06`.
- Python SDK for implementation is `runwayml`.
- Keep the integration isolated under `backend/app/runway`.
- Do not call Runway directly from UI or API routes.
- API routes should call the Runway module/pipeline layer, not the SDK.
- Store task IDs, failure codes, retries, timing, status, and credits where applicable.
- Never commit generated media unless it is explicitly selected as a final demo artifact.
- Use Runway only for approved campaigns after human approval, not before approval.

## Models And Credit Rules

- Final hero video model: `gen4.5`.
- Smoke/test clip model: `gen4_turbo`.
- Images/start frames model: `gen4_image_turbo`.
- TTS model: `eleven_multilingual_v2`.
- Costs:
  - `gen4.5`: 12 credits/sec.
  - `gen4_turbo`: 5 credits/sec.
  - `gen4_image_turbo`: 2 credits/image.
  - `eleven_multilingual_v2`: 1 credit per 50 chars.
- Hero estimate from XLSX/research: `4*10*12 + 4*2 + 18 = 506`.
- 50K hackathon credits are sufficient for MVP, but future prompts must require estimator usage before any batch generation.
- T-17 should preserve both estimated cost before generation and actual/observed cost where available after completion.

## Prompt Safety Policy

- Forbidden in visual prompts: real casino, provider, operator, sportsbook, or game-brand names such as `Pragmatic Play`, `NetEnt`, `Bet365`, and similar real entities.
- Forbidden in visual prompts: real faces, people, celebrities, likenesses, and logos.
- Gambling-specific risky terms must be sanitized into abstract safe motion-graphics language before sending any Runway request.
- Safety failures must not be retried as-is.
- Prompt safety must run before every Runway image/video call, and any text passed into TTS that could trigger moderation should also be normalized before request creation.
- `B-04` is the source for `GAME_VISUAL_HINTS`; T-16 depends on `B-04`.
- T-16 must not invent new visual mappings if `B-04` is incomplete; it should either block or use only accepted mappings already delivered by `B-04`.
- Required mode note for later prompts: `VISUAL_MODE: igaming_safe | generic_subscription`.

## Retry And Failure Policy

- `SAFETY.INPUT.*`, `SAFETY.OUTPUT.*`, and other safety/moderation failures: do not retry as-is; rewrite or sanitize first.
- `INPUT_PREPROCESSING.SAFETY.TEXT`: do not retry as-is; replace with a safe template first.
- `INTERNAL`, `INPUT_PREPROCESSING.INTERNAL`, or null/internal-ish failures: retry up to 2 times with backoff.
- `429` or throttling: exponential backoff and keep task observable as queued/throttled.
- Invalid asset/input such as `ASSET.INVALID`: do not retry without preprocessing or fixing the asset first.
- Log task ID, failure code, retry count, timing, and final status for every failed or retried task.
- Research baseline backoff ladder to preserve in future prompts: `15s`, `45s`, `120s`.

## T-15 Readiness Notes

- XLSX goal: Runway client + env validation.
- XLSX scope: `backend/app/runway/client.py` for SDK init, env validation, thin wrapper methods, version-header handling; `backend/app/runway/schemas.py` for normalized request/response shapes.
- XLSX deliverable: importable client with normalized errors.
- XLSX DoD: import works; missing key raises a clear `MissingApiKey`-style error.
- XLSX verification: `python -c "from backend.app.runway.client import client; print(client.health_check())"`.
- Dependency gate: `T-02`.
- Current repo reality: `backend/app/runway/client.py` is still a placeholder stub and `schemas.py` does not exist.
- Future prompt adjustment: keep this as a thin SDK wrapper only. No business logic, no campaign orchestration, no prompt policy, no cost estimation in T-15.
- Env validation behavior should explicitly check `RUNWAYML_API_SECRET` and fail early with a clear typed/normalized error rather than lazy failing on first API call.
- Future prompt should preserve the `.env.example` naming decision: `RUNWAYML_API_SECRET`.

## T-16 Readiness Notes

- XLSX goal: `prompt_safety` + visual hint mappings.
- XLSX scope: `backend/app/runway/prompt_safety.py`, `backend/app/runway/visual_hints.py`.
- XLSX deliverable: pre-flight sanitizer for all Runway prompts.
- XLSX DoD: `sanitize_visual_brief('Pragmatic Play slot with face')` returns a safe variant without brand/face terms.
- XLSX verification: `pytest -v tests/test_prompt_safety.py`.
- Dependency gate: `T-15` and `B-04`.
- Required sanitizer functions: `strip_forbidden(text)`, `sanitize_visual_brief(brief)`.
- Required mode note: `VISUAL_MODE: igaming_safe | generic_subscription`.
- Current repo reality: neither `prompt_safety.py` nor `visual_hints.py` exists yet.
- Future prompt must account for `B-04` output shape and must not fabricate `GAME_VISUAL_HINTS` coverage if `B-04` is not accepted yet.
- Safe-prompt direction already established in XLSX/research: abstract visual hints + Recall palette + cinematic motion + `no text` + `no logos`.

## T-17 Readiness Notes

- XLSX goal: Credit estimator + task store.
- XLSX scope: `backend/app/runway/credit_estimator.py`, `backend/app/runway/task_store.py`.
- XLSX deliverable: estimate before generation, status during generation, credits after generation.
- XLSX DoD: hero estimate `4*10*12 + 4*2 + 18 = 506` is computed correctly.
- XLSX verification: `pytest -v tests/test_credit_estimator.py`.
- Dependency gate: `T-15` and `T-03`.
- Required formulas:
  - video: rate-per-second by model, including `gen4.5` and `gen4_turbo`
  - image: `2` credits per `gen4_image_turbo` image
  - TTS: `ceil(chars / 50)`
  - campaign total: scenes + start frames + voiceover
- RunwayTask persistence expectations from research: persist `task_id`, `campaign_id`, optional `scene_id`, `kind`, `model`, `status`, `failure_code`, `output_url`, timestamps, retries, and `credits_estimated`.
- Current repo reality: no `RunwayTask` model exists in `backend/app/models.py`.
- T-03/model schema may change whether `task_store` gets a dedicated table or a temporary JSON-backed shape, so future prompts must inspect accepted T-03 output before locking persistence structure.

## T-18 Readiness Notes

- XLSX goal: Runway smoke test with 3 requests.
- XLSX scope: `scripts/runway_smoke.py`.
- XLSX deliverable: three smoke assets saved under `storage/smoke/`.
- XLSX DoD: all three files exist; mp4 plays; mp3 sounds valid.
- XLSX verification: `python scripts/runway_smoke.py && ls -la storage/smoke/`.
- Dependency gate: `T-15`, `T-16`, `T-17`.
- Smoke assets to require:
  - `storage/smoke/smoke_frame.jpg`
  - `storage/smoke/smoke_clip.mp4`
  - `storage/smoke/smoke_voice.mp3`
- Smoke models:
  - image: `gen4_image_turbo`
  - clip: `gen4_turbo`
  - TTS: `eleven_multilingual_v2`
- Must log task ID, status, time to complete, and credits for each smoke request.
- Must not run without explicit real API key availability.
- Future prompt should forbid hidden live calls in tests when the key is absent; it should fail clearly or require an explicit operator confirmation that a real key exists.

## T-19 Readiness Notes

- XLSX goal: `video_pipeline` orchestration.
- XLSX scope: `backend/app/runway/video_pipeline.py`.
- XLSX deliverable: async orchestration for 4 scenes plus TTS in parallel.
- XLSX DoD: on one approved campaign, the run completes in under 10 minutes and returns 4 mp4 clips plus 1 mp3.
- XLSX verification: `python -m backend.app.runway.video_pipeline cmp_001 -> успешно`.
- Dependency gate: `T-18`.
- Orchestration requirements:
  - 4 scenes
  - text/image to start frames
  - image-to-video generation
  - TTS in parallel
  - polling with backoff
  - campaign/video status updates
- Use the retry/failure policy defined above.
- Keep all Runway calls inside `backend/app/runway`.
- Current repo reality: `backend/app/runway/video_pipeline.py` is still a placeholder named like a stitch helper, so the future prompt should require replacing that stub with orchestration logic rather than layering orchestration elsewhere.
- Future prompt should also inspect current campaign status enums before assuming exact status names.

## T-20 Readiness Notes

- XLSX goal: ffmpeg stitching + voice overlay + poster.
- XLSX scope: `backend/app/runway/stitcher.py`.
- XLSX deliverable: final mp4 plus poster.
- XLSX DoD: final mp4 is roughly `30-45 sec`, roughly `10-15 MB`, poster is `1280x720`, and Telegram preview plays cleanly.
- XLSX verification: `ffprobe storage/cmp_001/video.mp4 -> duration 30-45, codec h264; file storage/cmp_001/poster.jpg`.
- Dependency gate: `T-19`.
- ffmpeg requirements:
  - concat 4 mp4 clips
  - scale to `1280x720`
  - `24fps`
  - voiceover overlay
  - fade in/out
  - H.264 `yuv420p` baseline
  - `-movflags +faststart`
  - poster at `1280x720`
- Telegram size check must stay under `50MB`.
- Current repo reality: no `stitcher.py` exists, and the current `video_pipeline.py` stub is only a placeholder `stitch_video()` function.

## T-21 Readiness Notes

- XLSX goal: `/video` API endpoints.
- XLSX scope: `backend/app/api/video.py`.
- XLSX deliverable: endpoints plus approval-flow integration.
- XLSX DoD: after approve in dashboard, campaign automatically moves through generating to ready.
- XLSX verification: `curl -X POST /approval/cmp_001/approve; sleep 60; curl /video/status/cmp_001 -> ready`.
- Dependency gate: `T-20` and `T-11`.
- Endpoints to require in future prompt:
  - `POST /video/generate` with body `{"campaign_id": "..."}`
  - `GET /video/status/{task_id}`
- Approval integration requirement: after approve, trigger pipeline through a background task.
- API route must call the Runway module or pipeline layer, not the SDK directly.
- Current repo reality: `backend/app/api/video.py` currently has only `POST /generate`, no path param, no status endpoint, and no background task.
- Future prompt should follow the resolved TECH_SPEC contract and not use XLSX campaign-id-based paths for polling.

## Verification And Safety Checklist

- Secret scan command:
  - `git grep -n "RUNWAYML_API_SECRET\\|TELEGRAM_BOT_TOKEN\\|ANTHROPIC_API_KEY\\|key_\\|\\.env" -- . ':!.env.example' || true`
- `.env` handling:
  - confirm `.env` is ignored
  - confirm only `.env.example` is committed
  - confirm future Runway env name is `RUNWAYML_API_SECRET`
- Storage/media git checks:
  - verify `storage/`, `*.mp4`, and `*.mp3` remain ignored
  - do not commit generated smoke/final media unless explicitly chosen as demo artifacts
- Prompt safety tests:
  - sanitize forbidden brand/face/logo input
  - ensure safety failures are not retried as-is
- Credit estimator tests:
  - verify `gen4.5`, `gen4_turbo`, image, and TTS formulas
  - verify `506` hero estimate
- Smoke test conditions:
  - run only with explicit real API key availability
  - capture three asset files plus task/status/timing/credit logs
- ffprobe/file size checks:
  - duration within `30-45 sec`
  - codec `h264`
  - poster exists
  - final size `<50MB`

## Future Prompt Checklist

- Dependencies accepted?
- Real key available?
- `B-04` available for visual hints?
- Model/schema ready?
- Prompt safety in place?
- Credit estimate required before generation?
- Retry policy included?
- Generated media ignored by git?
- Verification command and proof required?

## Open Questions

- `TECH_SPEC.md` still describes `POST /video/generate` plus `GET /video/status/{task_id}`, while XLSX requires campaign-id path params. Which contract should T-21 treat as final source of truth before implementation?
- Does accepted `T-03` introduce a dedicated `RunwayTask` table, or should T-17 temporarily persist task metadata in an existing campaign-linked structure until schema work is complete?
- What exact accepted output shape will `B-04` use for `GAME_VISUAL_HINTS`, and where will that artifact live for T-16 to import safely?
