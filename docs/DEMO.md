# Demo — Recall

A practical 2-minute demo script for local run-through and screen recording.

## Local Run Commands

```bash
# 1. Install hooks and copy env
cp .env.example .env
make install-hooks

# 2. Seed the database with 7 mock players and 96 events
make seed

# 3. Start the backend (FastAPI + SQLite)
make backend
#    API docs:  http://localhost:8000/docs
#    Health:    http://localhost:8000/health

# 4. In a second terminal, start the dashboard
make dashboard
#    Dashboard: http://localhost:3000

# 5. In a third terminal, start the landing
make landing
#    Landing:   http://localhost:3001
```

Or start all three at once with Docker Compose:

```bash
make dev
# Backend:  http://localhost:8000
# Dashboard: http://localhost:3000
# Landing:   http://localhost:3001
```

## 2-Minute Demo Script

### Setup (before recording)

1. Run `make seed` so the DB has 7 players and 96 events.
2. Open three browser tabs:
   - Dashboard: `http://localhost:3000`
   - Backend docs: `http://localhost:8000/docs`
   - Terminal with `curl` ready.

### Narration (timed)

**0:00 — Intro**
> "This is Recall, an AI CRM reactivation pipeline. It finds dormant users, classifies them, drafts a personalized video message, waits for a manager to approve it, generates the video with Runway, delivers it, and tracks conversion."

**0:10 — Seed and Scan**
> "We start with 7 synthetic players from 6 countries. I will trigger a scan to find dormant users."

Run in terminal:
```bash
curl -X POST http://localhost:8000/agent/scan
```

**0:20 — Approval Queue**
> "The scan created draft campaigns. Let me open the approval queue."

Switch to Dashboard tab. Show the table with columns: Player, Cohort badge, Risk score, LTV, Created, Actions.

**0:30 — Review a Campaign**
> "Click on a high-value dormant player. The side panel opens. We see the cohort reasoning, the offer, and the four-scene script. The manager can edit any scene, change the offer value, or reject with a reason."

Click a row. Scroll through:
- Player profile (name, country, last deposit, favorite game, biggest win)
- Cohort + risk_score + reasoning
- Offer block
- Four scene cards (intro, hook, offer, CTA)

**0:50 — Approve and Generate**
> "I will approve this campaign. That triggers the Runway video pipeline in the background."

Click **Approve as is**. The campaign status changes to `approved`.

Switch to terminal:
```bash
curl -X POST http://localhost:8000/video/generate \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "cmp_001"}'
```

Show the response with `task_id`.

**1:05 — Video Status Polling**
> "The pipeline generates four motion-graphics scenes with Gen-4.5, creates a voiceover with ElevenLabs through Runway, and stitches everything with ffmpeg. We can poll the status."

```bash
curl http://localhost:8000/video/status/{task_id}
```

Show the status moving from `queued` → `generating` → `stitching` → `ready`.

**1:20 — Delivery**
> "Once the video is ready, we send it. The delivery eligibility service checks consent and identifiers, then picks the best channel. Telegram is our real PoC adapter."

```bash
curl -X POST http://localhost:8000/delivery/send \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "cmp_001", "channels": ["telegram"]}'
```

**1:30 — Reactivation Landing**
> "The player receives a message with a poster and a button. Clicking the button opens a personalized landing page."

Open `http://localhost:3001/r/cmp_001`.

Show:
- Video player with poster, autoplay muted
- Offer headline
- CTA button

**1:40 — Tracking**
> "When the player watches the video, clicks the CTA, and submits the mock deposit form, tracking events fire."

Click **Claim my gift**. Fill mock form. Submit.

Switch to terminal:
```bash
curl -X POST http://localhost:8000/track/deposit \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "cmp_001", "player_id": "p_001", "amount": 50, "currency": "USD"}'
```

**1:50 — Metrics / ROI**
> "Finally, the tracking events feed the metrics layer. The ROI model shows the funnel, cohort assumptions, and conservative/base/aggressive scenarios."

Switch to Dashboard → Metrics.

Show:
- Big numbers: total sent, plays, CTR, reactivation rate, net revenue lift
- Funnel chart: Targeted → Sent → Played → Clicked → Converted
- Cohort table
- ROI calculator with conservative / base / aggressive scenarios

**2:00 — Outro**
> "That is the full pipeline in two minutes. Every step has human approval, consent gating, deterministic classification, and a fallback path. Thank you."

---

## Fallback Path: Slow Runway Render

If Runway queue is busy and generation takes longer than the demo window, use this fallback narrative:

**Show queued/generating state**
> "Runway Gen-4.5 is currently processing the scene tasks. In production, this queue is normal. The dashboard shows real-time progress."

Point to:
- `/video/status/{task_id}` returning `queued` or `generating`
- Dashboard showing progress bar or spinner

**Show poster/static fallback**
> "While the full video renders, the delivery can already send a static poster with a voiceover mp3, or a pre-rendered fallback asset."

Point to:
- `assets/demo_video/fallbacks/` directory
- A pre-generated poster JPG + TTS mp3 playing in the browser

**Explain task store and polling**
> "Every scene task is persisted in the task store with its Runway task ID, status, and failure code. The pipeline polls with exponential backoff. If a scene fails, it falls back to a shorter clip or a static frame."

Show:
- `backend/app/runway/task_store.py` schema
- A task row with `status: THROTTLED` and `retry_count: 1`

This demonstrates production resilience without waiting for the full render.

---

## Deploy Demo Steps

Production URLs verified on 2026-05-09 MSK:

1. Use `https://recall-agent-production-4dc7.up.railway.app` for backend curl commands.
2. Use `https://dashboard-ula-lab.vercel.app` for the dashboard walkthrough.
3. Use `https://landing-ula-lab.vercel.app` for landing and reactivation pages.
4. Record the demo against the deployed backend and landing.
5. Upload the demo video to `DEMO_VIDEO_URL_TBD`.

---

## Quick Reference: Demo Endpoints

```bash
# Seed
curl -X POST http://localhost:8000/agent/scan

# Approve (via dashboard UI, or API)
curl -X PATCH http://localhost:8000/approval/cmp_001 \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}'

# Generate video
curl -X POST http://localhost:8000/video/generate \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "cmp_001"}'

# Check status
curl http://localhost:8000/video/status/{task_id}

# Send delivery
curl -X POST http://localhost:8000/delivery/send \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "cmp_001", "channels": ["telegram"]}'

# Track deposit
curl -X POST http://localhost:8000/track/deposit \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "cmp_001", "player_id": "p_001", "amount": 50, "currency": "USD"}'
```

## Pre-Demo Checklist

- [ ] `make seed` completed successfully
- [ ] `make backend` running on `:8000`
- [ ] `make dashboard` running on `:3000`
- [ ] `make landing` running on `:3001`
- [ ] At least one campaign in `pending_approval` status
- [ ] Pre-generated fallback poster + voiceover in `storage/` (optional but recommended)
- [ ] Demo script printed or on second monitor
- [ ] Screen recorder started
- [ ] Timer visible (keep under 2 minutes)
