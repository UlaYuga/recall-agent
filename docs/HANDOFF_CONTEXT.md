# Recall - Codex Handoff Context

**Purpose:** Paste or reference this file when starting the implementation chat.  
**Use with:** `01_tech_spec.md`, `docs_pm_artifacts.md`, `05_runway_api_deep_research.md`, `06_modal_infra_research.md`.  

---

## 1. Project identity

**Name:** Recall  
**Repo:** `recall-agent`  
**Full title:** Recall - AI CRM Reactivation Pipeline for International iGaming Operators  

Recall is a portfolio-first PM/Delivery case, not just a hackathon toy.

The hackathon gives:

- deadline;
- free Runway credits;
- external proof point.

The real career goal:

- transition from Senior Content Producer to PM/Delivery Manager / AI Implementation Manager in international iGaming.

---

## 2. Final product narrative

Recall is an event-driven CRM reactivation pipeline.

It:

1. reads dormant player events from mock CRM/event bus;
2. identifies eligible dormant depositors;
3. classifies cohort/risk using deterministic rules;
4. generates personalized script/CTA/visual prompts with LLM;
5. sends campaign draft to CRM manager approval;
6. generates motion graphics video postcard via Runway;
7. delivers through Telegram PoC adapter and email preview;
8. sends player to landing page;
9. tracks play/click/mock deposit;
10. shows metrics and ROI simulation.

Core formula:

```text
event -> agent -> approval -> video -> delivery -> landing -> tracking -> metrics
```

---

## 3. Non-negotiable decisions

### 3.1 Market framing

```text
International iGaming.
Not Russia/CIS.
RU text is explanation language, not market geography.
```

### 3.2 Delivery framing

```text
Backend geo-agnostic.
Delivery market-specific.
Telegram is PoC adapter.
Email is preview/stub.
WhatsApp/SMS/push are roadmap.
```

### 3.3 Agent logic

```text
Classifier is rule-based/deterministic.
LLM generates script, tone, CTA, visual prompts.
LLM does not decide cohort.
```

### 3.4 Video strategy

```text
Motion graphics only.
No realistic talking head.
No real faces.
No real operator/provider logos.
No concrete game/provider brands.
MVP voiceover English-only.
Multilingual voiceover roadmap.
```

### 3.5 Data source

Recall does not collect player contacts.

Production data comes from:

- CRM;
- PAM;
- CDP;
- KYC profile;
- consent layer;
- event bus.

Mock data represents normalized operator profile data.

---

## 4. Implementation priority

Do not start with Runway.

Start with the spine:

```text
models -> seed data -> agent scan -> classifier -> campaign draft -> approval -> delivery status -> tracking -> metrics
```

Then add Runway.

Then add Telegram.

Then polish dashboard/landing.

---

## 5. First Codex task

Use this as first implementation prompt:

```text
Работаем над проектом Recall.

Context folder:
/Users/axel/Documents/Проекты/Recall

Source of truth:
- 01_tech_spec.md
- docs_pm_artifacts.md
- 05_runway_api_deep_research.md
- 06_modal_infra_research.md
- 03_constraints_and_risks.md

Task:
Create scaffold for repo recall-agent and implement MVP spine without real Runway/Telegram calls yet.

Start with:
1. Create repo structure from 01_tech_spec.md.
2. Create FastAPI backend skeleton.
3. Create SQLModel models.
4. Add seed data for 7 international mock players.
5. Implement rule-based classifier.
6. Implement campaign draft generation using fallback templates.
7. Implement delivery eligibility service.
8. Implement API endpoints with stubs.
9. Add Makefile: make dev, make seed, make test.
10. Add initial docs from docs_pm_artifacts.md.

Do not implement real Runway or Telegram yet.
Do not implement WhatsApp/SMS/push.
Do not add production auth.
Verify with tests before claiming completion.
```

---

## 6. Recommended repo phases

### Phase 0 - scaffold

Goal: repo exists, commands run.

Deliver:

- backend skeleton;
- dashboard skeleton;
- landing skeleton;
- docs skeleton;
- `.env.example`;
- Makefile.

Verification:

```bash
make test
make seed
make dev
```

### Phase 1 - data and agent spine

Goal: dormant player scan creates campaign drafts.

Deliver:

- `Player`;
- `Event`;
- `Campaign`;
- seed files;
- `/events`;
- `/agent/scan`;
- classifier;
- offer rules.

Verification:

```bash
curl -X POST localhost:8000/agent/scan
curl localhost:8000/approval/queue
```

### Phase 2 - approval and dashboard

Goal: CRM manager can review and approve.

Deliver:

- approval API;
- dashboard queue;
- campaign detail;
- edit/reject/approve.

Verification:

```text
Open dashboard.
Approve one campaign.
Campaign status becomes approved.
```

### Phase 3 - Runway integration

Goal: one approved campaign generates mp4/poster.

Deliver:

- `backend/app/runway/client.py`;
- `credit_estimator.py`;
- `prompt_safety.py`;
- task status tracking;
- video pipeline;
- local ffmpeg export.

Verification:

```text
1 test text-to-image
1 test image-to-video
1 test TTS
1 campaign video ready
```

### Phase 4 - delivery/tracking

Goal: Telegram and landing close the loop.

Deliver:

- TelegramAdapter real;
- EmailPosterAdapter preview;
- landing `/r/[campaign_id]`;
- tracking endpoints;
- mock deposit form;
- metrics dashboard.

Verification:

```text
Telegram message received.
Landing opens.
Click tracked.
Mock deposit tracked.
Campaign becomes converted.
```

### Phase 5 - portfolio polish

Goal: case reads like PM/Delivery work.

Deliver:

- README;
- PRD;
- Risk Register;
- ROI Model;
- Architecture;
- Case Study;
- demo screenshots;
- demo video script.

Verification:

```text
Hiring manager can understand case in 90 seconds.
```

---

## 7. Data model essentials

### Player

Must include:

```json
{
  "player_id": "p_001",
  "external_id": "demo_op_4471",
  "first_name": "Lucas",
  "preferred_language": "en",
  "market_language": "pt-BR",
  "country": "BR",
  "currency": "BRL",
  "last_login_at": "...",
  "last_deposit_at": "...",
  "total_deposits_count": 14,
  "total_deposits_amount": 7100,
  "favorite_vertical": "casino",
  "favorite_game_category": "slots",
  "favorite_game_label": "fruit_slots",
  "ltv_segment": "mid",
  "identifiers": {},
  "consent": {},
  "preferred_channels": ["telegram", "email"]
}
```

### Consent

Two layers:

```text
Generation consent:
- data_processing
- video_personalization

Delivery consent:
- marketing_communications
- channel-specific consent
```

### Campaign status

Recommended statuses:

```text
pending
approved
rejected
blocked_generation_consent
generating
generation_failed
ready
ready_blocked_delivery
sent
watched
clicked
converted
failed
```

---

## 8. Seven mock players

Use these archetypes:

1. **Lucas Pereira**
   - Brazil
   - BRL
   - `market_language`: `pt-BR`
   - cohort: `high_value_dormant`
   - channels: Telegram/email/WhatsApp in profile, MVP uses Telegram/email

2. **Mariana Torres**
   - Mexico
   - MXN
   - `market_language`: `es-MX`
   - cohort: `casual_dormant`
   - channels: email/push, no Telegram to test channel fallback

3. **Thabo Mokoena**
   - South Africa
   - ZAR
   - `market_language`: `en-ZA`
   - cohort: `post_event`
   - sportsbook post-event churn

4. **Andrei Popescu**
   - Romania
   - EUR/RON
   - `market_language`: `ro`
   - cohort: `lapsed_loyal`

5. **James Carter**
   - UK
   - GBP
   - `market_language`: `en-GB`
   - cohort: `first_deposit_no_return`
   - stronger compliance flags

6. **Sofia Alvarez**
   - Spain
   - EUR
   - `market_language`: `es-ES`
   - cohort: `casual_dormant`

7. **Ingrid Larsen**
   - Norway
   - NOK
   - `market_language`: `no`
   - cohort: `vip_at_risk`

MVP `preferred_language` can be `en` for all to keep voiceover simple.

---

## 9. Rule-based classifier sketch

Rules should be transparent:

```text
if missing generation consent:
  blocked_generation_consent

if total_deposits_count == 1 and days_since_last_deposit between 7 and 30:
  first_deposit_no_return

if favorite_vertical == sportsbook and last_event_type is bet_placed/session_end after event:
  post_event

if ltv_segment == vip and days_since_last_login >= 7:
  vip_at_risk

if total_deposits_amount high and days_since_last_deposit >= 14:
  high_value_dormant

if historical activity high and inactivity >= 21:
  lapsed_loyal

else:
  casual_dormant
```

Risk score:

```text
base = days_since_last_login * 2
+ ltv modifier
+ recency modifier
+ event type modifier
clamp 0-100
```

---

## 10. Delivery eligibility sketch

```python
def get_available_channels(player):
    if not player.consent.marketing_communications:
        return []

    channels = []

    if player.identifiers.telegram_chat_id:
        channels.append("telegram")

    if player.identifiers.email and player.consent.marketing_email:
        channels.append("email")

    if player.identifiers.phone_e164 and player.consent.marketing_sms:
        channels.append("sms")

    if player.identifiers.phone_e164 and player.consent.whatsapp_business:
        channels.append("whatsapp")

    if player.identifiers.push_token and player.consent.push_notifications:
        channels.append("push")

    return [c for c in player.preferred_channels if c in channels]
```

MVP should implement only Telegram and email send behavior. It can still calculate availability for roadmap channels.

---

## 11. Runway implementation rules

Do:

- isolate provider under `backend/app/runway`;
- track task IDs;
- estimate credits;
- store failure code;
- sanitize prompts before API;
- use safe abstract visuals;
- use English voiceover for MVP;
- generate final batch Sunday evening.

Do not:

- call Runway from UI;
- expose API key to frontend;
- generate faces;
- generate logos;
- use real gambling brands;
- retry safety failures as-is;
- leave final batch to Monday morning.

---

## 12. Modal implementation rules

Do not implement Modal by default.

Add docs only:

```text
ModalRenderWorker is production roadmap/fallback for ffmpeg stitching and batch post-processing.
```

Implement Modal only if:

- ffmpeg fails locally/Railway;
- worker timeouts block demo;
- final batch needs parallel stitching.

---

## 13. Dashboard MVP

Minimum useful dashboard:

```text
Left: campaign/player queue.
Right: selected campaign workspace.
Bottom: metrics strip.
```

Must show:

- player name/country/currency;
- cohort;
- risk score;
- agent reasoning;
- offer;
- script scenes;
- consent/delivery eligibility;
- video status;
- delivery status;
- tracking status.

Nice to have:

- full metrics page;
- ROI calculator;
- video gallery.

---

## 14. Landing MVP

Minimum:

- `/r/[campaign_id]`;
- video player;
- poster;
- CTA;
- mock deposit form;
- tracking events.

Tracking:

- `landing_loaded`;
- `video_play`;
- `video_50_percent`;
- `cta_click`;
- `deposit_submit`.

Do not overbuild marketing landing before product loop works.

---

## 15. Documentation requirements

Repo must include:

- `README.md`
- `docs/PRD.md`
- `docs/DELIVERY_PLAN.md`
- `docs/RISK_REGISTER.md`
- `docs/ROI_MODEL.md`
- `docs/ARCHITECTURE.md`
- `docs/CASE_STUDY.md`
- `docs/DEMO.md`
- `docs/SUBMISSION.md`

These docs are part of the portfolio, not extras.

---

## 16. Verification before completion

Every implementation phase requires proof:

```text
Scaffold: tree + commands run.
Seed: database has 7 players.
Classifier: API returns cohorts for all players.
Approval: campaign status changes.
Runway: at least one task succeeds.
Video: mp4 exists and plays.
Delivery: Telegram message received.
Tracking: event stored.
Metrics: dashboard reflects tracked data.
Docs: README explains case in 90 seconds.
```

Do not claim "done" without fresh verification output.

---

## 17. Final cutoff rules

Feature freeze:

```text
Sunday 2026-05-10 18:00 MSK
```

Final render batch:

```text
Sunday 2026-05-10 20:00-22:00 MSK
```

Monday:

```text
No new features.
Only backup renders, demo recording, README, submission.
```

---

## 18. What success looks like

By submission:

- One full hero path works end-to-end.
- 5-7 video postcards exist.
- Dashboard shows approval and status.
- Telegram message opens landing.
- Landing tracks conversion.
- Metrics/ROI dashboard exists.
- PM docs are present.
- Demo video explains the whole pipeline.

For portfolio:

> Recall demonstrates that Alexander can manage AI/vendor-heavy product delivery in international iGaming: business problem, MVP scope, risk management, integration architecture, human approval, tracking, ROI, and production roadmap.

