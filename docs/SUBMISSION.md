# Submission — Recall

English submission draft for the Runway API Hackathon.

## Project Name

**Recall** — AI CRM Reactivation Pipeline for Consumer Subscription / iGaming Operators

## Short Description

Recall is an event-driven CRM reactivation agent that monitors player activity, identifies dormant users, generates personalized motion-graphics video messages with Runway API, routes every campaign through a human approval gate, delivers via a Telegram PoC adapter, and tracks conversion through a campaign landing page.

It is not a generic video generator. Runway is the media generation layer inside a larger CRM orchestration system: data-driven selection, deterministic classification, human approval, generated media, consent-gated delivery, tracking, and ROI simulation.

## What It Does

1. **Scans** a mock event bus for dormant players.
2. **Classifies** each player into a cohort with a deterministic rule-based engine.
3. **Generates** a personalized script, offer, CTA, and visual briefs via LLM.
4. **Approves** every campaign draft through a CRM manager dashboard before any media is created or sent.
5. **Generates** a 30–45 second motion-graphics video postcard using Runway Gen-4.5 for scenes and ElevenLabs multilingual TTS for voiceover.
6. **Delivers** the approved asset through Telegram (real) or email preview (stub), respecting player consent and channel availability.
7. **Tracks** video play, CTA click, and mock deposit events on a personalized landing page.
8. **Reports** funnel metrics and an interactive ROI calculator with conservative, base, and aggressive scenarios.

## Why Runway

- **Gen-4.5** (`image_to_video`, 12 credits/sec) generates abstract motion-graphics scenes from start frames.
- **Gen-4 image turbo** (2 credits/image) creates fast reference frames for scene coherence.
- **ElevenLabs multilingual v2** (1 credit/50 chars) produces the voiceover through Runway's built-in TTS endpoint.
- **Parallel task execution** with async polling, credit estimation, prompt safety, and a fallback ladder for failed or throttled tasks.

The pipeline treats Runway as an external vendor with latency, moderation, and cost risks. It wraps those risks with observability (task store), safety (prompt sanitization), retry policy, and human review.

## Built With

| Technology | Role |
|---|---|
| Runway Gen-4.5 | Motion-graphics video generation |
| Runway text-to-speech | English voiceover via ElevenLabs multilingual v2 |
| FastAPI + SQLModel + SQLite | Backend API, ORM, mock event bus |
| Anthropic Claude Sonnet 4.5 | Script, tone, CTA, and visual prompt generation |
| Next.js 14 + shadcn/ui | Approval dashboard and metrics |
| Next.js 14 + Tailwind | Public landing and reactivation pages |
| aiogram 3.x | Telegram bot delivery |
| ffmpeg-python | Clip stitching + audio overlay |
| APScheduler | Periodic scan scheduling |

## Demo Evidence

- **Working approval dashboard** with queue, filters, inline edit, and side-panel preview.
- **End-to-end campaign path** from scan to delivery to conversion tracking.
- **Generated personalized video postcard** with motion graphics and voiceover.
- **Telegram delivery** with poster + inline button to personalized landing.
- **Tracking API and ROI model** with funnel events, cohort assumptions, and an interactive dashboard.

## Safety and Compliance

- **No real faces.** All visual prompts use abstract motion graphics. No people, no avatars.
- **No real brands or logos.** No operator names, no game provider names, no concrete slot titles.
- **No guaranteed-win language.** The agent system prompt explicitly prohibits guarantees, urgency stacking, and manipulative claims. Scripts are validated against a forbidden-term list.
- **Human approval gate.** Every campaign is reviewed by a CRM manager before generation or delivery.
- **Consent-gated delivery.** Two-layer consent model: generation consent blocks the pipeline; delivery consent blocks the send. Players without consent see `blocked_generation_consent` or `ready_blocked_delivery` status.
- **Generic submission mode.** The public landing and submission text frame the product as "AI Retention Agent for Consumer Subscription Products," with iGaming as a primary use case, not an exclusive one.

## ROI Model

Recall includes a transparent, conservative ROI model in USD. It does not claim guaranteed outcomes.

| Scenario | Baseline rate | AI video uplift | 60-day value | Cost per player | ROI |
|---|---|---|---|---|---|
| **Conservative** | 5% | +20% | $40 | $0.25 | 0.60× (60%) |
| **Base** | 7% | +30% | $58 | $0.25 | 3.87× (387%) |
| **Aggressive** | 10% | +50% | $85 | $0.25 | 16.0× (1,600%) |

**Base scenario example (10,000 players):**
- Incremental reactivated: 210
- Incremental revenue: $12,180
- Campaign cost: $2,500
- Net lift: $9,680
- Payback: ~2 weeks

The model stays positive even in the conservative scenario. Break-even uplift is ~6.2%, well below the conservative 20% assumption. All numbers are labeled as "Simulation based on industry benchmarks" in the dashboard.

## Architecture Highlights

- **Deterministic classifier:** no LLM decides eligibility; rules are transparent and testable.
- **VideoProviderProtocol:** Runway is isolated behind an adapter interface; swapping to Veo, Kling, Luma, or Pika takes ~1 hour.
- **DeliveryAdapter protocol:** Telegram, email, landing tracking, and CRM writeback are pluggable.
- **Task observability:** every Runway task is persisted with ID, status, failure code, and credit estimate.
- **Fallback ladder:** if Runway moderation or queue blocks a task, the pipeline retries with simplified prompts, switches to `gen4_turbo`, or falls back to static poster + voiceover.

## Repository

- GitHub: `https://github.com/UlaYuga/recall-agent.git`
- README with local quickstart: [README.md](../README.md)
- Architecture: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Demo script: [docs/DEMO.md](DEMO.md)
- ROI model: [docs/ROI_MODEL.md](ROI_MODEL.md)
- Risk register: [docs/RISK_REGISTER.md](RISK_REGISTER.md)

## Deploy URLs

- Backend API: `https://recall-agent-production-4dc7.up.railway.app`
- Dashboard: `https://dashboard-ula-lab.vercel.app`
- Landing: `https://landing-ula-lab.vercel.app`

## Demo Video (Optional)

> **A demo screen recording is not required for submission.**
>
> The project was smoke-tested end-to-end against the deployed services without screen recording.
> A 2-minute walkthrough recording can be added later if needed.

The planned demo video covers:
1. Seed and scan (10s)
2. Approval queue review (20s)
3. Approve and trigger generation (10s)
4. Status polling and ready state (15s)
5. Telegram delivery and landing (20s)
6. Tracking and metrics (25s)

See [docs/DEMO.md](DEMO.md) for the full demo script.

## E2E Smoke Test Results (2026-05-09 MSK)

The hero path was verified on the deployed services:

```bash
# 1. Seed database
curl -X POST https://recall-agent-production-4dc7.up.railway.app/events/seed
→ {"players":7,"events":96}

# 2. Scan for dormant players
curl -X POST https://recall-agent-production-4dc7.up.railway.app/agent/scan
→ {"scanned":7,"created":7,"skipped":0}

# 3. Approve a campaign
curl -X POST https://recall-agent-production-4dc7.up.railway.app/approval/{cid}/approve
→ {"status":"approved"}

# 4. Tracking: play → click → deposit
curl -X POST https://recall-agent-production-4dc7.up.railway.app/track/play -d '{"campaign_id":"...","player_id":"p_001","watched_seconds":32}'
curl -X POST https://recall-agent-production-4dc7.up.railway.app/track/click -d '{"campaign_id":"...","player_id":"p_001","link_id":"watch_video"}'
curl -X POST https://recall-agent-production-4dc7.up.railway.app/track/deposit -d '{"campaign_id":"...","player_id":"p_001","amount":75,"currency":"BRL"}'
→ All return {"status":"recorded"}

# 5. Metrics funnel confirmed
curl https://recall-agent-production-4dc7.up.railway.app/metrics/dashboard
→ {"funnel":{"scanned":7,"approved":1,"delivered":1,"played":1,"clicked":1,"deposited":1}, ...}
→ Funnel: 7 → 1 → 1 → 1 → 1 → 1

# 6. All frontend pages return 200
Dashboard: /, /campaigns, /campaigns/{id}, /metrics
Landing:  /, /case, /r/{campaign_id}

# 7. CORS preflight verified from both Vercel origins
```

## Submitted Checklist

- [x] GitHub repo public: `https://github.com/UlaYuga/recall-agent.git`
- [x] Backend Railway URL verified.
- [x] Dashboard Vercel URL verified.
- [x] Landing Vercel URL verified.
- [x] All 7 players seeded; 7 campaigns created via scan.
- [x] Tracking play/click/deposit confirmed; metrics dashboard shows funnel 7→1→1→1→1→1.
- [x] CORS preflight verified from dashboard and landing origins.
- [x] `.env.example` contains only placeholders.
- [x] No real secrets, no generated media, no `.next` cache in git.
- [x] `make public-check` passes.
