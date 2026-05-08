# Architecture — Recall

## Dataflow

```text
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  SEED   │───▶│  SCAN   │───▶│ CLASSIFY│───▶│  OFFER  │───▶│ SCRIPT  │
│ players │    │  dormant│    │ cohort  │    │ matrix  │    │ + visual│
│ + events│    │  detect │    │ + risk  │    │         │    │ prompts │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                                  │
                                                                  ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ METRICS │◄───│ TRACKING│◄───│ LANDING │◄───│ DELIVERY│◄───│ APPROVAL│
│dashboard│    │ events  │    │  page   │    │ adapters│    │  gate   │
│ + ROI   │    │         │    │         │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                                  │
                                                                  ▼
                                                           ┌─────────┐
                                                           │  VIDEO  │
                                                           │GENERATION│
                                                           │ Runway  │
                                                           │ + ffmpeg│
                                                           └─────────┘
```

### Stage-by-stage description

| Stage | Responsibility | Output |
|---|---|---|
| **Seed** | Load synthetic player profiles and event history into SQLite. | 7 players, 96 events, deterministic demo data. |
| **Scan** | Poll the mock event bus for players whose `last_login_at` / `last_deposit_at` exceeds the dormancy threshold. | List of `player_id`s flagged for reactivation. |
| **Classify** | Apply a deterministic decision tree to assign a cohort and risk score. No LLM is involved in classification. | `ClassificationResult` with `cohort`, `risk_score`, `ltv_tier`, `reasoning`. |
| **Offer** | Look up a deterministic offer matrix keyed by `cohort × ltv_tier`. | `Offer` with `type`, `value`, `game_label`, `valid_until`. |
| **Script** | LLM (Claude Sonnet 4.5 via Anthropic SDK) generates a personalized 70–110 word voiceover script, CTA text, tone, and four `visual_brief` prompts for Runway. | `ScriptResult` with 4 scenes, `full_voiceover_text`, `tone`, `cta_text`. |
| **Approval** | CRM manager reviews the campaign draft in the dashboard. They can approve as-is, approve with edits, reject with a reason, or request script regeneration. | Campaign status moves from `draft` → `pending_approval` → `approved` / `rejected`. |
| **Video generation** | Runway pipeline: generate start frames → parallel `image_to_video` tasks (Gen-4.5, 5–10 sec each) → TTS voiceover (`eleven_multilingual_v2`) → ffmpeg concat + audio overlay → poster JPG from first frame. | `VideoAsset` with `video_url`, `poster_url`, `duration_sec`, `size_bytes`. |
| **Delivery** | Eligibility service checks consent + identifiers, selects the best available channel, and dispatches. Telegram is real; email is a preview stub; landing tracking is real. | `DeliveryResult` per channel with `status`, `message_id`, `reason` (if skipped). |
| **Tracking** | Landing page at `/r/[campaign_id]` posts `play`, `click`, and `deposit` events to the backend tracking webhook. | `TrackingEvent` persisted; campaign may advance to `watched` or `converted`. |
| **Metrics** | Dashboard shows funnel visualization, cohort breakdown table, recent campaigns list, and an interactive ROI calculator with conservative / base / aggressive scenarios. | Live metrics + simulated projections in USD. |

## Main Modules

### `backend/app/api/*`

FastAPI routers that expose the public API surface:

- `agent.py` — `/agent/scan`, `/agent/decide/{player_id}`
- `approval.py` — `/approval/queue`, `/approval/{campaign_id}` (GET/PATCH), approve/reject/regenerate shortcuts
- `video.py` — `/video/generate`, `/video/status/{task_id}`
- `delivery.py` — `/delivery/send`
- `tracking.py` — `/track/play`, `/track/click`, `/track/deposit`

### `backend/app/agent/*`

Agent logic that drives the pre-approval pipeline:

- `classifier.py` — deterministic cohort classifier. Uses player profile + last 30 events. No LLM.
- `script_generator.py` — LLM script generation with injectable boundary, forbidden-term validation, and fallback templates.
- `offers.py` — deterministic offer matrix for all 6 cohorts.
- `prompts.py` — system prompt, scene prompt templates, and tool schemas.
- `fallback_templates.py` — pre-screened fallback scripts for all 6 cohorts (B-03 verified).

### `backend/app/runway/*`

Runway API integration and media orchestration:

- `client.py` — thin SDK wrapper (`RunwayML` / `AsyncRunwayML`) with env validation.
- `video_pipeline.py` — orchestrates scene generation, TTS, download, ffmpeg stitch, and campaign status updates.
- `tts.py` — text-to-speech via Runway `eleven_multilingual_v2`.
- `prompt_safety.py` — strips forbidden terms, maps game labels to safe abstract visual hints.
- `visual_hints.py` — 18 game hints + 12 category hints (B-04 verified).
- `task_store.py` — CRUD helpers for `RunwayTask` persistence and status polling.
- `credit_estimator.py` — estimates credits before generation; no real SDK calls.

### `backend/app/delivery/*`

Delivery adapters and eligibility service:

- `adapters.py` — `DeliveryAdapter` protocol.
- `eligibility.py` — `get_available_channels`, `can_send_channel`, `select_best_channel`, `block_reason`.
- `telegram_adapter.py` — real Telegram delivery via aiogram 3.x (`sendPhoto` + inline button, optional `sendVideo`).
- `email_adapter.py` — preview/stub only; dashboard shows email preview with poster + CTA + landing URL.
- `landing_adapter.py` — real landing tracking integration.
- `crm_writeback.py` — mock write-back to local SQLite.

### `dashboard/`

Next.js 14 + shadcn/ui CRM manager interface:

- `page.tsx` (root) — approval queue with filters, table, and side-panel preview/edit.
- `campaigns/[id]/page.tsx` — campaign detail with video player, metadata, and delivery CTA.
- `metrics/page.tsx` — funnel chart, cohort table, ROI calculator, big numbers.

### `landing/`

Next.js 14 static-export-ready public surface:

- `page.tsx` (root) — hero + concept + demo video + how it works + tech stack + CTA.
- `case/page.tsx` — case study with screenshots and metrics.
- `r/[campaign_id]/page.tsx` — per-player reactivation landing with video player, offer, and mock deposit form.

## Key Architectural Decisions

| Decision | Rationale | Where enforced |
|---|---|---|
| **Deterministic classifier** | LLM does not decide eligibility. More reliable demo, lower hallucination risk, easier to explain as a PM/Delivery system. | `backend/app/agent/classifier.py` |
| **LLM only for scripts** | Claude Sonnet 4.5 generates script, tone, CTA, and visual prompts. No decision-making authority. | `backend/app/agent/script_generator.py` |
| **Runway prompt safety** | All visual prompts use abstract motion graphics. No faces, no logos, no real game/provider brands. Avoids moderation flags. | `backend/app/runway/prompt_safety.py`, `visual_hints.py` |
| **Human approval gate** | Every campaign must be approved by a CRM manager before video generation or delivery. | `backend/app/api/approval.py`, `dashboard/` |
| **Consent gates** | Two-layer consent: generation consent (`data_processing` + `video_personalization`) blocks pipeline; delivery consent (`marketing_communications` + channel-specific) blocks send. | `backend/app/delivery/eligibility.py` |
| **No real brands / faces / logos** | Compliance-friendly positioning. Abstract visuals only. Generic subscription mode available for submission. | `docs/DECISIONS_LOG.md`, `landing/content/en.ts` |
| **Telegram as PoC adapter** | Fastest real-delivery channel for demo. Not positioned as global default. | `backend/app/delivery/telegram_adapter.py` |
| **USD-first ROI model** | All financial figures in USD. No RUB-first assumptions. Hackathon free credits excluded from ROI. | `docs/ROI_MODEL.md` |
| **VideoProviderProtocol** | Runway integration is isolated behind a protocol so swapping to Veo/Kling/Luma/Pika takes ~1 hour, not a week. | `backend/app/runway/client.py` |

## Current API Surface

### Agent

```
POST /agent/scan                  # Scan event bus for dormant players; create draft campaigns
GET  /agent/decide/{player_id}    # Run classifier + offer + script for a single player
```

### Approval

```
GET    /approval/queue                      # List all pending approval campaigns
GET    /approval/{campaign_id}              # Get campaign details + script + offer + player profile
PATCH  /approval/{campaign_id}              # Body: {action, script?, offer?, comment?}
POST   /approval/{campaign_id}/approve      # Shortcut approve
POST   /approval/{campaign_id}/reject       # Shortcut reject (requires reason)
POST   /approval/{campaign_id}/regenerate   # Regenerate script
```

### Video

```
POST /video/generate              # Body: {campaign_id} → start Runway pipeline, returns task_id
GET  /video/status/{task_id}      # Poll pipeline status: queued|generating|stitching|ready|failed
```

### Delivery

```
POST /delivery/send               # Body: {campaign_id, channels?, fallback_to_available?}
```

### Tracking

```
POST /track/play                  # Body: {campaign_id, player_id, watched_seconds}
POST /track/click                 # Body: {campaign_id, player_id, link_id}
POST /track/deposit               # Body: {campaign_id, player_id, amount, currency}
```

### Metrics

```
GET /metrics/dashboard            # Global metrics: total_sent, plays, ctr, deposit_uplift, roi_estimate_usd
```

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Backend framework | FastAPI | 0.115+ | Async API, OpenAPI auto-docs |
| ASGI server | uvicorn | 0.32+ | Dev + prod server |
| ORM | SQLModel | 0.0.22 | Pydantic + SQLAlchemy |
| DB | SQLite | builtin | Mock event bus and persistence |
| Settings | pydantic-settings | 2.6+ | Env management |
| Runway SDK | runwayml | >=3.0 | Media generation |
| LLM | anthropic | 0.40+ | Claude Sonnet 4.5 for script generation |
| HTTP client | httpx | 0.27+ | Async HTTP |
| Telegram | aiogram | 3.13+ | Bot delivery |
| Video processing | ffmpeg-python | 0.2.0 | Clip stitching + audio overlay |
| Scheduler | APScheduler | 3.10+ | Cron-like scan scheduling |
| Dashboard | Next.js | 14.2+ | App router, shadcn/ui |
| State | TanStack Query | 5.59+ | Backend data fetching |
| Charts | Recharts | 2.13+ | Uplift graphs |
| Landing | Next.js | 14.2+ | Static export, Vercel deploy |

## Deployment Placeholders

> **Production endpoints are TBD until tasks T-32/T-33 PASS.**
>
> - Backend API: `BACKEND_URL_TBD`
> - Dashboard: `DASHBOARD_URL_TBD`
> - Landing: `LANDING_URL_TBD`

These will be updated after Railway/Render backend deploy and Vercel landing/dashboard deploy are verified.
