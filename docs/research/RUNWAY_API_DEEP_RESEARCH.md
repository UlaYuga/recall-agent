# Recall - Runway API Deep Research

**Date:** 2026-05-07  
**Purpose:** Source-of-truth research pack for Recall implementation and PM/Delivery case packaging.  
**Primary sources:**  
- Runway API docs: https://docs.dev.runwayml.com/  
- Models: https://docs.dev.runwayml.com/guides/models/  
- Pricing: https://docs.dev.runwayml.com/guides/pricing/  
- Getting started / API usage: https://docs.dev.runwayml.com/guides/using-the-api/  
- Go-live checklist: https://docs.dev.runwayml.com/guides/go-live/  
- Task failures: https://docs.dev.runwayml.com/errors/task-failures/  
- Moderation: https://docs.dev.runwayml.com/api-details/moderation/  
- Runway Skills repo: https://github.com/runwayml/skills  

---

## 1. Executive summary for Recall

Runway API is not just a video endpoint for Recall. It is the media-generation layer of a CRM orchestration pipeline:

```text
CRM event -> cohort decision -> approved script -> Runway scenes + voiceover -> stitched asset -> delivery adapter -> landing tracking
```

The most important confirmed facts for Recall:

- Runway API exposes `gen4.5`, `gen4_turbo`, `gen4_aleph`, `gen4_image`, `gen4_image_turbo`, `eleven_multilingual_v2`, and real-time `gwm1_avatars`.
- `gen4.5` supports text-to-video and image-to-video.
- `gen4.5` costs 12 credits/sec.
- `gen4_turbo` costs 5 credits/sec and is the cheaper test/fallback model.
- `gen4_image_turbo` costs 2 credits/image and is ideal for fast reference/start-frame generation.
- `eleven_multilingual_v2` costs 1 credit per 50 characters.
- Credits cost $0.01 each in the developer portal, excluding tax.
- Runway moderation evaluates inputs and outputs; too many moderated requests can lead to suspension.
- `SAFETY.INPUT.*` failures should not be retried as-is.
- `INTERNAL` failures may be retried with delay.
- Runway recommends usage monitoring: error rate, request count, and throttled task count.
- API keys should be stored in environment variables or secret managers, not hard-coded.

The architecture in `01_tech_spec.md` is sound, with one strong recommendation: **keep Runway integration as an isolated provider module** with explicit retry policy, credit tracking, moderation-safe prompt generation, and local fallback assets.

---

## 2. What Runway means for the product

Recall should be described as:

> An event-driven CRM reactivation pipeline that uses Runway as the media generation engine for approved personalized video postcards.

Not:

> A tool that generates videos.

This distinction matters for PM/Delivery interviews. The business value is not the video alone. The value is that CRM teams can move from mass generic outreach to controlled personalized media campaigns with:

- data-driven player selection;
- deterministic cohort/risk logic;
- human approval;
- generated media;
- channel-specific delivery;
- tracking/write-back;
- ROI simulation.

Runway is the vendor dependency that makes the media layer feasible inside a three-day PoC.

---

## 3. Confirmed Runway API surface relevant to Recall

### 3.1 Base API facts

From the Runway docs and API examples:

```text
Base URL: https://api.dev.runwayml.com
Auth: Authorization: Bearer <RUNWAYML_API_SECRET>
Version header: X-Runway-Version: 2024-11-06
Python SDK: runwayml
Node SDK: @runwayml/sdk
```

Recall implementation decision:

- Use Python SDK in backend because the backend is FastAPI.
- Keep raw HTTP examples in docs for troubleshooting.
- Store `RUNWAYML_API_SECRET` in `.env`, never in code.
- Add `.env.example`, but never real keys.
- Add `git grep "key_"` to final pre-submission checklist.

### 3.2 Video models

| Model | Input | Output | Price | Recall use |
|---|---|---:|---:|---|
| `gen4.5` | Text or image | Video | 12 credits/sec | Main final motion graphics scenes |
| `gen4_turbo` | Image | Video | 5 credits/sec | Cheap smoke tests and fallback |
| `gen4_aleph` | Video + text/image | Video | 15 credits/sec | Not MVP; future video editing |
| `veo3` | Text or image | Video | 40 credits/sec | Not MVP; too expensive |
| `veo3.1` | Text or image | Video | 20-40 credits/sec depending audio | Not MVP |
| `veo3.1_fast` | Text or image | Video | 10-15 credits/sec depending audio | Optional fallback only |
| `gwm1_avatars` | Conversation | Video + audio | 2 upfront + 2/6 sec | Not MVP; avatars intentionally avoided |

Recall decision:

- Final output: `gen4.5`.
- Testing: `gen4_turbo` where possible.
- No real-time avatars.
- No realistic talking heads.
- No `gwm1_avatars` in MVP or public product framing.

### 3.3 Image models

| Model | Price | Recall use |
|---|---:|---|
| `gen4_image_turbo` | 2 credits/image | Fast start/reference frame generation |
| `gen4_image` | 5 credits 720p, 8 credits 1080p | Higher-quality hero frames if needed |
| `gemini_2.5_flash` | 5 credits/image | Optional alternate image model |
| `gpt_image_2` | 1-41 credits/image | Not MVP |
| `gemini_image3_pro` | 20-40 credits/image | Not MVP |

Recall decision:

- `gen4_image_turbo` is enough for start frames.
- If hero video looks cheap, spend on `gen4_image` for only 1-2 hero frames.
- Do not generate high-cost images for all 7 players unless video quality is otherwise blocked.

### 3.4 Audio models

| Model | Price | Recall use |
|---|---:|---|
| `eleven_multilingual_v2` | 1 credit / 50 chars | English MVP voiceover |
| `eleven_text_to_sound_v2` | 1 credit/sec or 2 credits no duration | Optional sound effect, not MVP |
| `eleven_voice_isolation` | 1 credit / 6 sec | Not MVP |
| `eleven_voice_dubbing` | 1 credit / 2 sec | Not MVP |
| `eleven_multilingual_sts_v2` | 1 credit / 3 sec | Not MVP |

Recall decision:

- Use `eleven_multilingual_v2`.
- Voiceover text: English-only for MVP reliability.
- Store `market_language` for player profiles, but do not generate multilingual voiceover during MVP.

---

## 4. Recommended Recall media pipeline

### 4.1 MVP pipeline

```text
Campaign approved
  -> script scenes already available
  -> generate or load start frame per scene
  -> create 3-4 video tasks via Runway
  -> create TTS task via Runway
  -> download outputs
  -> ffmpeg concat
  -> overlay voiceover
  -> export mp4 + poster
  -> mark campaign ready
```

### 4.2 Scene count

Spec says 3-5 scenes. For MVP reliability:

```text
Default: 4 scenes x 5 sec = 20 sec
Hero: 4 scenes x 10 sec = 40 sec
Fallback: 3 scenes x 5 sec = 15 sec
```

Do not force every video to 30-45 seconds if render queues or quality are bad.

Recommended acceptance:

- hero campaign: 30-40 seconds;
- additional gallery videos: 15-25 seconds acceptable;
- demo video can show the same workflow at shorter duration for speed.

### 4.3 Asset types

Each campaign should store:

```json
{
  "video_asset": {
    "video_url": "/storage/cmp_001/video.mp4",
    "poster_url": "/storage/cmp_001/poster.jpg",
    "voiceover_url": "/storage/cmp_001/voiceover.mp3",
    "duration_sec": 32,
    "size_bytes": 12000000,
    "runway_task_ids": ["task_1", "task_2", "task_3", "task_4", "tts_1"],
    "model": "gen4.5",
    "credit_estimate": 410
  }
}
```

### 4.4 Runway task tracking

Create `RunwayTask` table or JSON field:

```json
{
  "task_id": "uuid",
  "campaign_id": "cmp_001",
  "scene_id": "scene_2",
  "kind": "image_to_video|text_to_speech|text_to_image",
  "model": "gen4.5",
  "status": "PENDING|THROTTLED|RUNNING|SUCCEEDED|FAILED|CANCELLED",
  "failure_code": null,
  "output_url": null,
  "created_at": "...",
  "completed_at": "...",
  "credits_estimated": 120
}
```

Why this matters:

- PM/Delivery story improves: you are tracking vendor task observability.
- Debugging improves.
- Demo can show progress.
- Risk register becomes concrete.

---

## 5. Credit model for Recall

### 5.1 Credit facts

Runway pricing page states:

- Credits can be purchased at $0.01/credit.
- `gen4.5`: 12 credits/sec.
- `gen4_turbo`: 5 credits/sec.
- `gen4_image_turbo`: 2 credits/image.
- `gen4_image`: 5 credits 720p or 8 credits 1080p.
- `eleven_multilingual_v2`: 1 credit per 50 characters.

### 5.2 One hero video estimate

Assume:

- 4 scenes.
- 10 sec each.
- `gen4.5`.
- 4 start frames with `gen4_image_turbo`.
- 900-char voiceover.

```text
Video: 4 * 10 sec * 12 = 480 credits
Images: 4 * 2 = 8 credits
TTS: 900 / 50 = 18 credits
Total: 506 credits
Dollar value: ~$5.06
```

### 5.3 One gallery video estimate

Assume:

- 3 scenes.
- 5 sec each.
- `gen4.5`.
- 3 start frames.
- 500-char voiceover.

```text
Video: 3 * 5 sec * 12 = 180 credits
Images: 3 * 2 = 6 credits
TTS: 500 / 50 = 10 credits
Total: 196 credits
Dollar value: ~$1.96
```

### 5.4 Seven-video batch estimate

```text
1 hero video: ~506 credits
6 gallery videos: 6 * 196 = 1176 credits
Total final batch: ~1682 credits
5x iteration budget: ~8410 credits
10x iteration budget: ~16,820 credits
```

Conclusion:

50K credits are more than enough. The limiting resources are:

- render latency;
- prompt iteration time;
- ffmpeg reliability;
- QA attention;
- demo recording time.

### 5.5 Usage tracking rule

Add `CreditEstimateService` even if Runway API usage endpoint is not implemented on day 1.

Minimum implementation:

```python
def estimate_video_credits(model: str, duration_sec: int) -> int:
    rates = {"gen4.5": 12, "gen4_turbo": 5}
    return rates[model] * duration_sec

def estimate_tts_credits(chars: int) -> int:
    return math.ceil(chars / 50)
```

This is enough for dashboard and PM docs.

---

## 6. Failure handling policy

### 6.1 Failure classes

Runway task failure docs identify `failureCode` as the diagnostic field.

Recall should treat failures as:

| Failure code class | Meaning | Retry? | Recall action |
|---|---|---|---|
| `SAFETY.INPUT.*` | Prompt/input rejected | No | Rewrite prompt, sanitize visual brief |
| `SAFETY.OUTPUT.*` | Generated output rejected | No direct retry | Simplify prompt and regenerate |
| `INPUT_PREPROCESSING.SAFETY.TEXT` | Input text rejected | No | Replace text with safe template |
| `INPUT_PREPROCESSING.INTERNAL` | Moderation/preprocessing issue | Yes, delayed | Retry with backoff |
| `ASSET.INVALID` | Bad media dimensions/duration/type | No | Fix asset and rerun |
| `INTERNAL` / null | Internal processing issue | Yes, delayed | Retry with backoff |
| 429 / throttling | Rate or tier limit | Yes, delayed | Backoff and mark queued/throttled |

### 6.2 Retry policy

```text
Do not retry safety failures as-is.
Retry INTERNAL with delay.
Retry throttling with exponential backoff.
Do not retry invalid asset without preprocessing fix.
Limit retries to 2 per task in MVP.
```

### 6.3 Backoff strategy

```python
retry_delays = [15, 45, 120]
```

For MVP:

- first failure goes to dashboard;
- second failure marks scene failed;
- failed scene can use static fallback frame.

### 6.4 Fallback policy

Fallback ladder:

1. Retry same model for internal/throttle only.
2. Simplify prompt if moderation or bad output.
3. Use `gen4_turbo` shorter clip.
4. Use static image + pan/zoom via ffmpeg.
5. Use pre-rendered asset from `assets/demo_video/fallbacks`.

PM/Delivery wording:

> Recall treats media generation as an unreliable vendor process and wraps it with task observability, retry policy, fallback assets, and human review.

This is stronger than pretending generation is deterministic.

---

## 7. Moderation-safe prompting for iGaming

### 7.1 Why moderation matters

Runway moderation evaluates all request elements, including text prompts and media inputs. Moderated generations still cost credits, and repeated moderated requests can put the account at risk.

Recall should avoid gambling-heavy visual prompts.

### 7.2 Prompt rules

Allowed:

- abstract slot reels;
- abstract playing cards;
- abstract gift particles;
- neon UI panels;
- cinematic motion graphics;
- generic sports arena lights;
- coins as abstract particles;
- no text in generated video;
- no logos;
- no people;
- no real game/provider names.

Avoid:

- real casino brand names;
- real operator names;
- real slot provider names;
- celebrity faces;
- public figures;
- realistic human agents;
- explicit gambling slang;
- claims of guaranteed wins;
- large cash piles;
- screenshots of real games;
- prompts asking model to generate text inside video.

### 7.3 Recommended scene prompt templates

```python
SCENE_PROMPTS = {
    "intro": (
        "abstract entertainment dashboard lights, elegant deep blue and gold palette, "
        "soft bokeh, cinematic motion graphics, no text, no logos, no people"
    ),
    "personalized_hook": (
        "close-up abstract game symbols floating in warm light, smooth camera move, "
        "premium digital postcard style, no text, no logos, no people"
    ),
    "offer": (
        "shimmering particles forming an abstract gift shape, elegant brand palette, "
        "clean motion design, no text, no logos, no people"
    ),
    "cta": (
        "minimal glowing interface card, soft pulsing button shape without readable text, "
        "deep blue gradient, polished product animation, no logos"
    )
}
```

### 7.4 Important prompt correction

Current mini-prompts mention `slot reels`. That is probably okay but should be softened in EN submission mode.

Use two modes:

```python
VISUAL_MODE = "igaming_safe" | "generic_subscription"
```

`igaming_safe`:

- abstract game symbols;
- entertainment dashboard;
- reward card.

`generic_subscription`:

- product dashboard;
- personalized gift;
- return journey.

---

## 8. Implementation architecture for Runway module

### 8.1 Files

```text
backend/app/runway/
├── client.py
├── schemas.py
├── credit_estimator.py
├── prompt_safety.py
├── task_store.py
├── video_pipeline.py
├── tts.py
└── fallback_assets.py
```

### 8.2 `client.py`

Responsibilities:

- SDK client initialization;
- environment variable validation;
- create image-to-video task;
- create text-to-image task;
- create TTS task;
- get task status;
- download outputs;
- normalize SDK errors.

Do not put business logic here.

### 8.3 `video_pipeline.py`

Responsibilities:

- receive approved campaign;
- create scene tasks;
- poll tasks;
- call TTS;
- download assets;
- call ffmpeg;
- update campaign status.

### 8.4 `prompt_safety.py`

Responsibilities:

- remove forbidden words;
- strip real brand names;
- reject people/faces/logos in visual briefs;
- map iGaming labels to safe abstract prompts.

Example mapping:

```python
GAME_VISUAL_HINTS = {
    "fruit_slots": "colorful abstract fruit-like symbols",
    "live_blackjack": "abstract playing card silhouettes",
    "football_bets": "stadium lights and moving field lines",
}
```

### 8.5 `task_store.py`

Responsibilities:

- persist Runway task IDs;
- status updates;
- failure codes;
- retry counters;
- output URLs;
- credit estimates.

For MVP it can be a JSON field in `Campaign`, but a separate model is cleaner.

---

## 9. Runway Skills repository usage

### 9.1 What the repo provides

The Runway Skills repo is positioned for:

- direct media generation at scale;
- app integration guidance;
- API key setup;
- compatibility checks;
- querying org details;
- API reference fetching;
- uploads;
- video/image/audio generation.

Relevant skills listed in repo:

- `rw-generate-video`
- `rw-generate-image`
- `rw-generate-audio`
- `rw-integrate-video`
- `rw-integrate-image`
- `rw-integrate-audio`
- `rw-recipe-full-setup`
- `rw-check-compatibility`
- `rw-setup-api-key`
- `rw-check-org-details`
- `rw-integrate-uploads`
- `rw-api-reference`
- `rw-fetch-api-reference`
- `use-runway-api`

### 9.2 How to use for Recall

Do not depend on skills at runtime.

Use them during build:

```text
Install skills -> use examples/scripts -> adapt into backend/app/runway -> commit own code
```

### 9.3 Suggested build workflow

1. Install skills:

```bash
npx skills add runwayml/skills
```

2. Use skills for smoke tests:

```text
Generate a 5-second gen4_turbo test clip from a reference frame.
Generate one gen4_image_turbo frame from Recall visual style prompt.
Generate one TTS voiceover with eleven_multilingual_v2.
```

3. Copy working parameters into:

```text
docs/RUNWAY_WORKING_PARAMS.md
backend/app/runway/defaults.py
```

4. Do not allow agent to rewrite architecture around Skills repo.

### 9.4 Why this matters

Skills repo is useful because it reduces boilerplate. It is risky if it turns into a second app architecture. The Recall source of truth remains:

```text
FastAPI backend -> Runway module -> dashboard-triggered tasks
```

---

## 10. Go-live checklist mapped to Recall

Runway production checklist maps to Recall as follows:

### 10.1 Usage management

Runway recommends checking tier/concurrency and autobilling for production.

Recall MVP:

- no autobilling needed for hackathon;
- track credits manually;
- check credit balance before final batch;
- throttle parallel jobs if tasks become `THROTTLED`.

Production roadmap:

- tier up before customer pilot;
- estimate daily generations;
- set autobilling threshold;
- alert on remaining credits.

### 10.2 Integration testing

MVP test matrix:

```text
Runway health:
- create 1 text-to-image
- create 1 image-to-video
- create 1 TTS
- poll status
- download result
- handle failed task

Pipeline health:
- create 1 campaign
- approve
- generate 1 scene
- stitch
- store mp4
- show preview in dashboard
```

### 10.3 Security

Runway says API keys should not be hard-coded and should be searched before launch.

Recall checklist:

```bash
git grep "RUNWAYML_API_SECRET"
git grep "key_"
git grep "TELEGRAM_BOT_TOKEN"
git grep "ANTHROPIC_API_KEY"
```

Expected:

- only `.env.example`, docs, config names;
- no real values.

### 10.4 Monitoring

Track:

- Runway API request count;
- task status count;
- failure codes;
- throttled count;
- credits estimated;
- render duration;
- scenes failed per campaign.

Dashboard can show only simple counts, but docs should mention production monitoring.

---

## 11. Technical risks added by Runway

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| Render queue latency | High | High | Generate final batch Sunday; async polling; fallback assets |
| Moderation failure | Medium | High | Safe prompts; no logos/faces/brands; generic submission mode |
| Bad visual quality | Medium | Medium | Start frame strategy; prompt templates; accept shorter gallery videos |
| ffmpeg sync issue | Medium | High | English-only voiceover; fixed durations; fallback static montage |
| Credits overspend | Low | Medium | Credit estimator; use `gen4_turbo` for tests |
| API key leak | Low | High | `.env`; git grep; no secrets in repo |
| Task failure handling absent | Medium | High | Store task IDs/failure codes; retry policy |

---

## 12. Recommended updates to existing docs

### 12.1 `03_constraints_and_risks.md`

Add:

```text
Runway SAFETY.INPUT failures are not retried as-is. Prompt is rewritten first.
Runway INTERNAL failures can be retried with delay.
Moderated generations still cost credits, so prompt safety happens before API calls.
```

### 12.2 `01_tech_spec.md`

Add optional file:

```text
backend/app/runway/credit_estimator.py
backend/app/runway/prompt_safety.py
backend/app/runway/task_store.py
```

If scope is tight, `task_store.py` can be folded into `models.py`.

### 12.3 `docs_pm_artifacts.md`

Add PM note:

```text
Runway is treated as an external vendor with latency, safety moderation and credit-cost risks. Recall wraps it with observability, fallbacks and human approval.
```

---

## 13. Final Runway implementation checklist

Before writing UI polish:

- [ ] `RUNWAYML_API_SECRET` loads from env.
- [ ] `client.image_to_video.create(...).wait_for_task_output()` works.
- [ ] `client.text_to_image.create(...).wait_for_task_output()` works.
- [ ] `client.text_to_speech.create(...).wait_for_task_output()` works.
- [ ] One output URL downloads locally.
- [ ] ffmpeg can read downloaded clips.
- [ ] Failed task is displayed in dashboard.
- [ ] Prompt safety strips forbidden visual terms.
- [ ] Credit estimator logs expected cost.
- [ ] Final generated mp4 is under Telegram 50MB cap.

---

## 14. What to tell Codex

Use this instruction when implementation starts:

```text
Runway integration must be isolated under backend/app/runway.
Do not call Runway directly from API route files.
Implement prompt safety and credit estimation before enabling batch generation.
Persist task IDs and failure codes.
Use gen4_turbo for smoke tests where possible.
Use gen4.5 for final hero video.
Do not implement Characters/avatars.
Do not generate real faces, logos, or brand names.
```

---

## 15. Sources

- Runway API docs: https://docs.dev.runwayml.com/
- Runway models: https://docs.dev.runwayml.com/guides/models/
- Runway pricing: https://docs.dev.runwayml.com/guides/pricing/
- Runway API getting started: https://docs.dev.runwayml.com/guides/using-the-api/
- Runway go-live checklist: https://docs.dev.runwayml.com/guides/go-live/
- Runway task failures: https://docs.dev.runwayml.com/errors/task-failures/
- Runway moderation: https://docs.dev.runwayml.com/api-details/moderation/
- Runway Skills: https://github.com/runwayml/skills
