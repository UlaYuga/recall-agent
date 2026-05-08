# Recall - PM/Delivery Artifacts

Эти документы кладутся в `/docs` репозитория recall-agent.
Для Codex: создай каждый файл по его разделу ниже.

---

# PRD.md

## Product: Recall - AI CRM Reactivation Pipeline

**Version:** PoC 1.0
**Author:** Alexander Ulanov
**Date:** May 2026
**Status:** MVP / Hackathon PoC

---

### Problem

iGaming operators lose 60-70% of registered players within the first 30 days. Dormant depositors represent a significant lost LTV opportunity.

Current approach: mass email/push with generic copy. Baseline reactivation rate: 5-7%.

Gap: Personalized outreach delivers 20-40% uplift but does not scale manually. A CRM team cannot write a custom reactivation script for each dormant player.

---

### Target user

**Primary:** CRM Manager at a mid-tier iGaming operator (10k-100k active players)
- Responsible for reactivation campaigns
- Works in a CRM tool (Smartico, Fast Track, Optimove)
- Has approval authority for bonuses up to $50/player
- Manages 2-5 campaigns per week

**Secondary:** Head of Retention / Head of CRM
- Evaluates ROI of reactivation spend
- Needs reporting on uplift vs baseline

---

### Stakeholders

| Role | Interest | Success metric |
|---|---|---|
| CRM Manager | Less manual work, more personalized campaigns | Time to campaign < 5 min |
| Head of Retention | Higher reactivation rate, measurable ROI | Uplift vs baseline |
| Product | On-brand tone and visual style | Approval rate > 70% |
| Compliance | Responsible gambling, consent management | Zero compliance flags in demo |
| BI/Analytics | Attribution to deposit | Tracking to conversion works |
| Dev Team (future) | Clean API for CRM integration | OpenAPI spec, clear endpoints |

---

### User stories

**CRM Manager:**
- As a CRM Manager, I want to see a queue of dormant players with cohort labels and risk scores, so I can understand priority
- As a CRM Manager, I want to see the agent's reasoning and edit the script before approving, so I stay in control of tone
- As a CRM Manager, I want to click Approve and receive a finished video without manual work
- As a CRM Manager, I want to reject a campaign with a reason, so the agent learns what not to do
- As a CRM Manager, I want to see delivery and tracking status per campaign

**Head of Retention:**
- As a Head of Retention, I want a ROI simulation by cohort and channel
- As a Head of Retention, I want to understand cost per reactivated player

---

### MVP scope

**In - real implementation:**
- Mock event bus (SQLite, 7 players, seed events)
- Dormant trigger: no login + no deposit 7-30 days
- Rule-based cohort classifier + LLM script/offer generation
- Approval dashboard (Next.js + shadcn)
- Runway Gen-4.5 motion graphics video pipeline
- ffmpeg stitching + ElevenLabs voiceover via Runway API
- Telegram delivery (sendVideo + inline CTA button)
- Landing /r/[campaign_id] with play/click/deposit tracking
- Metrics dashboard + ROI simulation
- 1 full hero path (event → video → Telegram → landing → deposit mock)
- 5-7 personalized video postcards as proof of scale

**Mock/stub:**
- Email: mock status in dashboard UI only
- File storage: local / Railway volumes
- Deposit: mock form, not a real gateway
- Auth: single demo password in .env

**Out of scope (post-submission):**
- Real CRM integrations (Smartico, Optimove, Fast Track)
- Real email delivery (SendGrid, Mailtrap)
- Production auth (JWT/OAuth)
- Batch approval workflows
- Multi-language support beyond RU
- Multi-operator configuration

---

### Acceptance criteria

| Criteria | Verifiable by |
|---|---|
| /agent/scan detects dormant players from mock bus | API call + response |
| All 7 mock players get campaign drafts | Dashboard queue |
| Approval dashboard works: approve / edit / reject | Manual walkthrough |
| Runway pipeline generates minimum 3 final videos | Dashboard gallery |
| 1 campaign completes full path to Telegram + landing + deposit mock | Screen recording |
| Metrics dashboard reflects real tracking events | Dashboard metrics page |
| README explains project in 90 seconds | Reading time test |
| Architecture diagram present | docs/ARCHITECTURE.md |
| ROI model present with source citations | docs/ROI_MODEL.md |

---

# DELIVERY_PLAN.md

## 3-Day Delivery Plan - Recall PoC

**Start:** Friday May 8, 2026, 16:00 MSK
**Deadline:** Monday May 11, 2026, 16:00 MSK
**Feature freeze:** Sunday May 10, 18:00 MSK

---

### Critical path

```
Day 1 (Fri): Scaffold → Data model → Mock players → Agent scan + classify → Runway smoke test
Day 2 (Sat): Script gen → Approval API → Dashboard → Video pipeline → Telegram delivery
Day 3 (Sun): Landing + tracking → Metrics dashboard → End-to-end hero path → FREEZE
Day 4 (Mon): Batch videos → Demo recording → Submission
```

**Single-thread constraint:** Solo project. No parallel dev streams.

**Highest risk block:** Video pipeline (Day 2, 16:00-19:00). Runway queue latency unpredictable. Buffer explicitly allocated.

---

### Milestones

| # | Milestone | Day | Time MSK | Proof |
|---|---|---|---|---|
| M1 | Repo scaffold + seed data | Fri | 21:00 | GitHub commit |
| M2 | Runway API smoke test (1 clip + 1 TTS) | Fri | 22:00 | mp4 file |
| M3 | Agent scan + classify on 3 mocks | Sat | 12:00 | API response |
| M4 | Approval dashboard (queue + workspace) | Sat | 16:00 | localhost |
| M5 | Video pipeline end-to-end on 1 mock | Sat | 19:00 | mp4 in storage |
| M6 | Telegram delivery working | Sat | 22:00 | Video in personal TG |
| M7 | Landing + tracking working | Sun | 12:00 | /track events in DB |
| M8 | Metrics dashboard working | Sun | 15:00 | Dashboard page |
| M9 | Full hero path (event→conversion) | Sun | 18:00 | Screen recording |
| M10 | FEATURE FREEZE | Sun | 18:00 | - |
| M11 | 5-7 videos generated | Mon | 10:00 | Dashboard gallery |
| M12 | Demo video recorded | Mon | 13:00 | YouTube unlisted |
| M13 | Submission filed | Mon | 15:55 | Confirmation email |

---

### Fallback plan

| Risk | Trigger | Fallback |
|---|---|---|
| Runway queue > 30 min | M5 slipping past 20:00 Sat | Pre-generate videos Friday night, store as static assets |
| Video pipeline fails | M5 not achieved by 10:00 Sun | Show generation status UI + 1 pre-rendered video as demo |
| Dashboard not complete | M8 slipping | Streamlit fallback instead of Next.js, accept lower polish |
| Telegram delivery fails | M6 not achieved | Show delivery button + mock status in dashboard, explain in README |
| LLM API unavailable | Any point | Switch to hardcoded fallback templates (pre-written scripts per cohort) |
| Railway deploy fails | Mon morning | Use localhost + ngrok for demo recording |

---

### Dependency map

```
Runway API key → video pipeline (M5)
Anthropic API key → script generation (M3)
Telegram bot token + personal TG account → delivery test (M6)
FastAPI backend running → all API tests
SQLite with seed data → all agent tests
Next.js dashboard → approval flow
Vercel deploy → landing tracking (can use localhost for demo)
Railway deploy → public URL for submission (can use ngrok fallback)
```

---

# RISK_REGISTER.md

## Risk Register - Recall PoC

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Runway API queue latency > 30 min during peak (hackathon weekend) | High | High | Pre-generate Friday night. Async polling with timeout. Store pre-rendered fallback videos. | Solo dev |
| R2 | Video quality too abstract / unreadable | Medium | Medium | Validate visual prompts Friday smoke test. Iterate prompts before Day 2. Fallback: simpler static frame + text overlay. | Solo dev |
| R3 | Telegram 50MB file size exceeded | Low | Medium | 720p 30-45 sec H.264 = ~10-15MB. Well within limit. Monitor size at generation. | Solo dev |
| R4 | Runway compliance flags gambling content | Medium | High | EN-framing in video prompts (abstract visuals, no casino brand names, no logos, no gambling terms in prompts). Separate EN submission wrapper. | Solo dev |
| R5 | LLM hallucination in script (compliance violation) | Low | High | Rule-based classifier first. LLM only for script text. System prompt has explicit prohibitions. CRM Manager approval gate catches issues before delivery. | Solo dev |
| R6 | LLM API unavailable or rate-limited | Low | Medium | Fallback templates per cohort hardcoded in prompts.py. Pipeline continues with template if LLM fails. | Solo dev |
| R7 | Delivery timeline (can't complete hero path by deadline) | Medium | High | Critical path tracked daily. Feature freeze Sun 18:00 enforced. Minimal viable demo = 1 video + approval flow + tracking, rest can be static. | Solo dev |
| R8 | Anthropic API key unavailable | Low | Medium | Fallback to gpt-4o-mini (same tool use interface, minimal code change). | Solo dev |
| R9 | ffmpeg stitching fails on Railway (missing binary) | Low | Medium | Test ffmpeg availability in Railway environment Day 1. Alternative: moviepy or cloud ffmpeg service. | Solo dev |
| R10 | Demo video recording insufficient quality | Low | Medium | Record Saturday evening after M6 as backup. Full demo Monday morning as main. | Solo dev |

---

**Legend:**
- Probability: Low (<20%), Medium (20-50%), High (>50%)
- Impact: Low (cosmetic), Medium (partial demo broken), High (core demo blocked)

---

# ROI_MODEL.md

## ROI Model - Recall PoC

> Disclaimer: All figures are simulations based on published industry benchmarks. This is a PoC model, not a production audit.

---

### Assumptions: Operator baseline

| Parameter | Value | Source |
|---|---|---|
| Total registered players | 50,000 | Mid-tier operator estimate |
| Dormant base (no login/deposit 7-30d) | 15,000 | ~30% of registered (industry avg) |
| Targeted cohort per campaign | 5,000 | Selective high-value + mid-value |
| Baseline reactivation rate | 7% | Engagehut published benchmark |
| AI-video uplift (relative) | +30% | Conservative vs Idomoo/Entain case (+100%+) |
| Uplifted reactivation rate | 9.1% | 7% * 1.30 |
| 60-day LTV per reactivated player | 5,800 RUB / ~$58 | Russia avg $42-45/month * 1.3 |

---

### Costs per campaign (per 5,000 players)

| Cost item | Per user | Total |
|---|---|---|
| Runway video generation | ~576 credits | ~$0.57 / player |
| CRM Manager time (with Recall) | ~5 min per batch | vs 40+ min manual |
| Telegram delivery | $0 | Bot API free |
| Landing hosting | $0 | Vercel free tier |
| **Total cost per player** | **~$0.60** | **~$3,000** |

Runway credit math: 3-5 clips * 10 sec * ~30 credits/sec + TTS 100 chars * 2 = ~480-600 credits/video.
50K credits hackathon budget → ~83-104 videos.

---

### Revenue model (per 5,000-player cohort)

| Scenario | Reactivation rate | Reactivated players | Revenue (60d) | Cost | Net | ROI |
|---|---|---|---|---|---|---|
| Baseline (no AI) | 7% | 350 | 2,030,000 RUB | ~50,000 RUB (manual) | 1,980,000 RUB | - |
| Conservative (AI, +20%) | 8.4% | 420 | 2,436,000 RUB | ~103,000 RUB | 2,333,000 RUB | +18% |
| Base (AI, +30%) | 9.1% | 455 | 2,639,000 RUB | ~103,000 RUB | 2,536,000 RUB | +28% |
| Aggressive (AI, +50%) | 10.5% | 525 | 3,045,000 RUB | ~103,000 RUB | 2,942,000 RUB | +49% |

---

### Break-even analysis

Break-even uplift needed to cover AI costs: **+5.2% relative** (from 7.0% to 7.36% reactivation rate).

Any uplift above 5.2% relative = positive ROI. Published benchmarks suggest 20-100%+ relative uplift for personalized video vs static.

---

### Sources

- Engagehut (2024): baseline reactivation 5-10% for dormant re-engagement campaigns
- Idomoo x Entain case: personalized video uplift 100%+ vs control
- Optimove (2024): segmented campaigns outperform mass by 3-5x on conversion
- Russia avg monthly GGR per active player: $42-45 (industry estimate, 01.tech research)
- Xtremepush: personalized push CTR 2-4x vs broadcast

---

# VENDOR_INTEGRATION_PLAN.md

## Vendor Integration Plan - Recall PoC

---

### Runway API

**Role:** Core video generation (motion graphics clips + TTS voiceover)
**Model:** Gen-4.5 image_to_video, gen4_image_turbo for start frames, eleven_multilingual_v2 for RU voice
**Integration:** Official Python SDK `runwayml` >= 3.0
**Authentication:** RUNWAYML_API_SECRET in .env
**Rate limits:** Unknown for hackathon tier. Mitigation: async polling, retry with backoff, pre-generate fallback
**Cost:** 50K credits allocated. ~480-600 credits per video. Estimated capacity: 83-104 videos.
**Fallback vendor:** Kling API, Luma Dream Machine, Pika 2.0 (all accessible via VideoProviderProtocol interface)

---

### ElevenLabs (via Runway)

**Role:** Russian language voiceover
**Integration:** Via Runway `/v1/text_to_speech` endpoint. No separate ElevenLabs account needed.
**Model:** `eleven_multilingual_v2`
**Cost:** 1 credit per 50 characters
**Fallback:** Edge TTS (free, lower quality) or Google Cloud TTS

---

### Telegram Bot API

**Role:** Primary delivery channel for video postcards
**Integration:** aiogram 3.13 (async)
**Authentication:** TELEGRAM_BOT_TOKEN in .env
**Constraints:**
- sendVideo cloud API cap: 50MB (our videos ~10-15MB, no issue)
- No video play tracking (tracking only via landing URL click)
**Fallback:** sendPhoto + link if video send fails

---

### Anthropic Claude API

**Role:** Script generation, tone adaptation, visual prompt generation
**Model:** Claude Sonnet 4.5 (claude-sonnet-4-5)
**Integration:** `anthropic` Python SDK 0.40+, structured tool use
**Authentication:** ANTHROPIC_API_KEY in .env
**Fallback:** OpenAI GPT-4o-mini (same tool use interface, minimal code change)

---

### Future CRM integrations (V1 production roadmap)

| CRM/CDP | Integration approach | Notes |
|---|---|---|
| Smartico | REST API webhooks for event bus, bonus API for offer creation | Most common in CIS tier-2 |
| Fast Track | Event webhooks + Campaign API | Strong EU presence |
| Optimove | Segment push API | Enterprise-grade |
| Generic CDP | Kafka/Redis event stream consumer | Replaces SQLite mock bus |

---

### Deployment

| Service | Provider | Plan | Notes |
|---|---|---|---|
| Backend (FastAPI) | Railway | Starter ($5/mo) | Persistent volume for video storage |
| Dashboard (Next.js) | Vercel | Free | |
| Landing (Next.js) | Vercel | Free | Separate project |
| Database | SQLite on Railway | - | Sufficient for PoC, replace with Postgres for V1 |

---

### Production roadmap additions (V1)

- Replace SQLite with PostgreSQL
- Replace local file storage with S3 or GCS
- Add Redis for async job queue (replace APScheduler)
- Add SendGrid for email channel
- Add Amplitude or Mixpanel for advanced analytics
- Add proper auth (JWT + role management for CRM operators)
