# Risk Register — Recall

**Purpose:** Portfolio-ready risk transparency for the AI CRM Reactivation Pipeline.  
**Context:** International iGaming operators. 3-day hackathon PoC → production roadmap.  
**Currency note:** All financial references in USD.

---

## Risk Matrix Summary

| Category | Risks tracked | Residual exposure after mitigations |
|---|---|---|
| Product & agent logic | 3 | Low — deterministic classifier, LLM constrained to script/visuals |
| Compliance & moderation | 3 | Medium — moderations still cost credits; Runway policy opaque |
| Runway / media generation | 5 | Medium-High — render latency is the #1 hackathon risk |
| Telegram delivery | 2 | Low — fallback path exists; 50MB cap not hit at 720p/45s |
| Data & privacy | 3 | Low — synthetic data only; no real PII in demo |
| Demo reliability | 2 | Medium — end-to-end depends on Runway queue availability |
| Deployment | 2 | Low — Railway + Vercel, simple env config |
| Timeline | 2 | Medium — Sunday render batch is critical path |

---

## 1. Product & Agent Logic

### R-01: Classifier misclassifies a player cohort

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low |
| Trigger | Edge-case event history or missing data fields |
| Impact | Wrong script tone, wrong offer band → demo looks broken to reviewer |
| Mitigation | Classifier is **deterministic rule-based**, not LLM. Rules documented in TECH_SPEC §4.2 and HANDOFF_CONTEXT §9. All 7 mock players pre-classified and verified in tests. |
| Owner | Backend (classifier.py) |
| Fallback | Fallback template per cohort exists in `backend/app/agent/fallback_templates.py`. Dashboard shows classifier reasoning in approval side-panel so CRM manager can override. |
| Demo workaround | If classifier gives unexpected output during live demo, re-seed DB and re-run scan. |

### R-02: LLM generates unsafe or misleading script

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Low |
| Trigger | LLM hallucination, poorly constrained prompt, or forbidden terms slipping through |
| Impact | Script contains "guaranteed win" language, real brand names, or urgency stacking → compliance violation in demo recording |
| Mitigation | Forbidden-term validation in `script_generator.py`. Fallback templates (`fallback_templates.py`) with pre-screened scripts for all 6 cohorts. Approval gate: CRM manager must approve before video generation. Prompt rules in TECH_SPEC §4.1 explicitly prohibit guarantee language, urgency stacking, and real brands. |
| Owner | Backend (script_generator.py, prompts.py) |
| Fallback | Fallback template automatically used if LLM unavailable or output fails validation. |
| Demo workaround | Show approval gate UI during demo, highlight the human-in-the-loop checkpoint. |

### R-03: Offer engine assigns inappropriate reward

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low |
| Trigger | Player LTV/cohort edge case not covered by offer matrix |
| Impact | VIP gets free_spins_small → looks cheap; low-value player gets deposit_match_high → looks reckless |
| Mitigation | Deterministic offer matrix (`offers.py`) keyed to classifier cohort + LTV tier. Tested for all 6 cohorts. Dashboard inline edit allows CRM manager to adjust value before approval. |
| Owner | Backend (offers.py) |
| Fallback | Approval dashboard shows offer inline; CRM manager can edit before approve. |
| Demo workaround | Pre-approve known-good offers for 3-4 players; show edit workflow on one campaign only. |

---

## 2. Compliance & Moderation

### R-04: Runway moderation flags video generation

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Medium |
| Trigger | Visual prompt contains gambling-adjacent terms (`slot`, `casino`, `bet`), real brand names, faces, or logos |
| Impact | `SAFETY.INPUT.*` or `SAFETY.OUTPUT.*` task failure. Credits still consumed. Campaign stuck in `generation_failed`. Worst case: repeated flags risk account suspension. |
| Mitigation | `prompt_safety.py` strips forbidden terms before API call. All visual prompts use abstract motion graphics (no faces, no logos, no text in video, no real game/provider names). Two visual modes: `igaming_safe` and `generic_subscription`. Visual hints (`visual_hints.py`) map game labels to safe abstract descriptions. EN-version landing for submission removes all iGaming framing. |
| Owner | Backend (prompt_safety.py, visual_hints.py) |
| Fallback | `SAFETY` failures are NOT retried as-is — prompt is rewritten. Fallback ladder: retry with generic mode → static image + ffmpeg pan/zoom → pre-rendered asset from `assets/demo_video/fallbacks/`. |
| Demo workaround | Have 1-2 pre-rendered fallback videos ready. If Runway moderation blocks during demo, switch explanation to "this is why we have prompt safety layer + fallback assets — production CRM systems cannot depend on raw generation without guards." |

### R-05: Runway terms of service restrict iGaming use

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Medium |
| Trigger | Runway TOS enforcement or policy change during/after hackathon |
| Impact | Account suspension; generated assets unusable in portfolio |
| Mitigation | EN landing and submission frame the product as "consumer subscription reactivation" (generic mode). Visual briefs avoid gambling-specific terminology. Pipeline wraps Runway behind `VideoProviderProtocol` — swappable to Veo/Kling/Luma/Pika. |
| Owner | PM (docs positioning) + Backend (provider abstraction) |
| Fallback | `VideoProviderProtocol` allows swap to alternate provider with ~hour of work. Generic subscription mode framing pre-written in landing `content/en.ts`. |
| Demo workaround | Demo video and landing use generic subscription framing. Submission text includes "applicable to consumer subscription products" alongside iGaming. |

### R-06: Generated video content violates advertising standards

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low |
| Trigger | Offer text or visual CTA implies guaranteed outcomes, manipulative urgency, or targets vulnerable players |
| Impact | Mock campaign looks non-compliant to iGaming-aware portfolio reviewer |
| Mitigation | Agent system prompt (§4.1) explicitly prohibits guarantee language and urgency stacking. Script validation checks for forbidden terms. Approval gate ensures human reviews every script. Offer engine avoids "last chance" / "don't miss" / "guaranteed" language. |
| Owner | Backend (prompts.py, script_generator.py) + Dashboard (approval UI) |
| Fallback | CRM manager can edit or reject any script before generation. |
| Demo workaround | Pre-review all 5-7 scripts before final batch. Flag any campaign with >1 urgency phrase for edit. |

---

## 3. Runway / Media Generation

### R-07: Render queue latency blocks final batch

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Medium-High |
| Trigger | Multiple hackathon participants hitting Runway API simultaneously on Sunday evening / Monday morning |
| Impact | Video tasks stay in `THROTTLED`/`PENDING` for hours. Final batch not ready by submission deadline. |
| Mitigation | Schedule: **final batch Sunday 20:00-22:00 MSK** (TECH_SPEC §12, HANDOFF_CONTEXT §17). Monday reserved for backup renders only. Async polling with task store. Parallel scene generation via `AsyncRunwayML`. Fallback ladder includes static montage and pre-rendered assets. |
| Owner | Backend (video_pipeline.py) + PM (schedule enforcement) |
| Fallback | If 3+ tasks are THROTTLED after 30 min: switch remaining scenes to `gen4_turbo` (5 creds/sec vs 12). If video unavailable: use static poster + voiceover as demo content. |
| Demo workaround | Show at least one fully generated hero video. For remaining players, show poster + voiceover + "generation queued" status in dashboard as realistic production scenario. |

### R-08: ffmpeg stitching produces corrupted or out-of-sync video

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Medium |
| Trigger | Clip duration mismatch, variable frame rates from Runway, audio/video offset in concat |
| Impact | Generated video unplayable or glitchy — unusable for demo and portfolio |
| Mitigation | English-only MVP voiceover (fixed known char/duration ratio). Fixed scene durations (5 or 10 sec per Runway spec). ffmpeg concat via filelist with re-encoding to H.264 720p. Test end-to-end on one campaign before batch generation. |
| Owner | Backend (video_pipeline.py) |
| Fallback | If concat fails: fall back to single-scene output with voiceover (shorter but complete). Static poster + voiceover as absolute fallback. |
| Demo workaround | Test concat on Saturday evening. If unreliable, show single-scene hero demo and explain "multi-scene stitching is production-ready but we prioritize clean output for PoC." |

### R-09: Generated visuals look low-quality or off-brand

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Medium |
| Trigger | Abstract motion graphics prompts produce muddy or inconsistent frames |
| Impact | Portfolio video looks amateur → undermines production-readiness claim |
| Mitigation | Start-frame strategy: generate reference frames via `gen4_image_turbo` (2 credits) before `image_to_video` for scene coherence. Fixed visual style: deep purple + gold palette, bokeh, cinematic motion. `visual_hints.py` maps 18 game labels to safe abstract descriptions. Reference frames in `assets/reference_frames/`. |
| Owner | Backend (video_pipeline.py, visual_hints.py) |
| Fallback | Accept shorter gallery videos (15-25 sec). Hero campaign gets 2× prompt iteration budget. |
| Demo workaround | Curate best 3-4 outputs for demo video. Use poster frames for gallery where video quality is marginal. Show prompt iteration as feature, not bug ("CRM team can A/B test visual style"). |

### R-10: Credit overconsumption during prompt iteration

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low-Medium |
| Trigger | Multiple retries of failed tasks, excessive prompt tuning, re-generating all scenes for quality |
| Impact | Burn through 50K hackathon credits before final batch is complete |
| Mitigation | Credit estimator (`credit_estimator.py`) logs expected cost before each task. Use `gen4_turbo` (5 creds/sec) for tests and smoke runs. Use `gen4_image_turbo` (2 creds) for start frames, not `gen4_image` (5-8 creds). Budget: ~1,700 credits for final 7-video batch, ~8,400 with 5× iteration, ~17,000 with 10×. 50K credits provide ≥2× headroom even at worst case. Monitor via `client.organization.usage`. |
| Owner | Backend (credit_estimator.py) + PM |
| Fallback | If credits approach 50%: freeze iteration, use best outputs as-is, switch remaining to `gen4_turbo`. |
| Demo workaround | Budget was pre-calculated and is tracked in dashboard credit estimator. |

### R-11: Runway API key exposure

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Low |
| Trigger | Accidental commit of `.env`, hard-coded key in source, leak through debug logs |
| Impact | Key revocation, all generated assets lost, campaign state unrecoverable |
| Mitigation | `.env` in `.gitignore`. `.env.example` uses placeholder values only. Pre-commit hook: `git grep "key_"` and `git grep "RUNWAYML_API_SECRET"`. Dashboard never accesses Runway key (backend-only). `make public-check` includes secret scan. |
| Owner | Backend (config.py) + PM (pre-submission checklist) |
| Fallback | Key rotation in Runway dev portal. Regenerate with new key if compromised. |
| Demo workaround | Run `make public-check` before every push and before submission. |

---

## 4. Telegram Delivery

### R-12: Telegram sendVideo fails for files near 50MB

| Field | Detail |
|---|---|
| Severity | Low |
| Likelihood | Low |
| Trigger | Generated video exceeds 50MB after ffmpeg export at high bitrate |
| Impact | Player receives poster-only message with link; no inline video playback in Telegram |
| Mitigation | Target: 720p H.264, 30-45 sec → estimated 10-15MB (well within 50MB cap, TECH_SPEC §1.3). Hybrid delivery approach: `sendPhoto` (poster) + inline button first message; optional `sendVideo` as second message (HANDOFF_CONTEXT: "Telegram не дает notify о просмотре mp4, трекаем только на лендинге"). |
| Owner | Backend (telegram_adapter.py) |
| Fallback | If video > 50MB: send poster + link to mp4 hosted on Railway volume. Player watches on landing. |
| Demo workaround | Use poster + landing path as primary demo flow (this is the recommended hybrid approach anyway). |

### R-13: Player has no Telegram chat_id (channel unavailable)

| Field | Detail |
|---|---|
| Severity | Low |
| Likelihood | Medium (2 of 7 mock players lack Telegram) |
| Trigger | Mariana (p_002) and Sofia (p_006) have `telegram_chat_id: null` |
| Impact | Cannot demo Telegram delivery for these players |
| Mitigation | This is a **designed demo feature**, not a bug. Shows channel fallback logic: eligibility service (`eligibility.py`) returns available channels per player; selects next preferred channel; shows `skipped` reason per channel. Email preview stub covers these players in dashboard. |
| Owner | Backend (delivery/eligibility.py) |
| Fallback | Dashboard shows "No Telegram — sent via Email preview" for p_002/p_006. |
| Demo workaround | Use these two players to demonstrate the delivery eligibility layer: "Telegram is a PoC adapter. In production, SMS/WhatsApp/Push adapters handle players without Telegram. The consent-based channel selection works identically across all adapters." |

---

## 5. Data & Privacy

### R-14: Mock data accidentally contains real PII

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Very Low |
| Trigger | Copy-paste error, real data mixed into seed files |
| Impact | GDPR/compliance exposure in public repo |
| Mitigation | All player data is synthetic: `demo@example.com` emails, `+X0000000` phone format, `mock_tg_XXX` Telegram IDs, `mock_push_token_XXX` tokens. No real operator names. Verified in B-01/B-02 acceptance. |
| Owner | PM (data review) + Backend (seed files) |
| Fallback | Regenerate seed data from archetype templates (scripted, not manual). |
| Demo workaround | Pre-commit verification: run B-01/B-02 validation scripts. |

### R-15: Consent model gaps in demo data

| Field | Detail |
|---|---|
| Severity | Low |
| Likelihood | Low |
| Trigger | Mock player with contradictory consent flags (e.g., `marketing_communications: false` but `preferred_channels: [telegram]`) |
| Impact | Delivery eligibility returns unexpected results during demo |
| Mitigation | Two-layer consent model explicitly designed and tested (TECH_SPEC §6.2): generation consent gates video pipeline; delivery consent gates channel sending. All 7 mock players verified for consent consistency in B-01 seed review. Sofia's `email_disabled` tag correctly maps to `marketing_email: false` — this is intentional demo content. |
| Owner | Backend (delivery/eligibility.py) |
| Fallback | Dashboard shows consent status per player. CRM manager sees `blocked_generation_consent` or `ready_blocked_delivery` with explanation. |
| Demo workaround | Use Sofia's case as demo of consent-gated delivery. |

### R-16: Tracking webhook captures real data in demo

| Field | Detail |
|---|---|
| Severity | Low |
| Likelihood | Very Low |
| Trigger | Real visitor submits mock deposit form on public landing |
| Impact | Unclear (synthetic data only) |
| Mitigation | Landing `/r/[campaign_id]` uses mock deposit form (no real payment). Tracking webhook stores synthetic campaign/player IDs only. Landing explains "this is a demo — no real deposit is made." Public landing does not require login or collect real personal data. |
| Owner | Backend (tracking.py) + Landing (`app/r/[campaign_id]/page.tsx`) |
| Fallback | Database seeded with synthetic data; real submissions create synthetic tracking events only. |
| Demo workaround | Pre-populate tracking events for demo. Show "converted" status from seeded conversions. |

---

## 6. Demo Reliability

### R-17: End-to-end demo breaks during live recording

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Medium |
| Trigger | Network failure, Runway outage, Railway deploy issue, Telegram rate limit |
| Impact | Cannot record working demo video for submission |
| Mitigation | Record demo video in segments (screen recording + voiceover, not live one-take). Backend and landing pre-deployed and smoke-tested. At least one hero campaign fully pre-generated and stored. Demo script pre-written for each pipeline stage (TECH_SPEC §12 Monday 10:00-13:00). All 7 players pre-seeded. |
| Owner | PM (demo script + screen recording) |
| Fallback | If live pipeline fails: use pre-generated assets and explain architecture over static screenshots. Still shows working codebase. |
| Demo workaround | Demo format: recorded screen capture, not live demo. Each stage is a separate recording segment. Stitched in post. |

### R-18: Dashboard or landing CSS breaks during Vercel deploy

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low |
| Trigger | Missing dependency, build error after last-minute polish, Tailwind config issue |
| Impact | Public landing or dashboard unavailable during recording |
| Mitigation | Deploy landing to Vercel by Sunday evening (TECH_SPEC §12: Sunday 18:00-20:00). Run `npm run build` before deploy. Static export where possible. Keep fallback HTML page at root. |
| Owner | Frontend (dashboard + landing) |
| Fallback | Fallback static HTML page with project description and GitHub link. |
| Demo workaround | Screenshot dashboard and landing for demo video if live deploy fails. Show architecture diagram instead. |

---

## 7. Deployment

### R-19: Railway/Render backend deploy fails

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low |
| Trigger | Missing env vars, port binding issue, startup crash, Python version mismatch |
| Impact | Backend API unavailable → delivery and landing tracking don't work |
| Mitigation | Use `uvicorn` with `--host 0.0.0.0 --port $PORT` pattern (standard Railway/Render). All env vars in `.env.example`. Health endpoint `GET /health` returns 200. CORS configured for Vercel preview URLs. Test deploy Sunday. |
| Owner | Backend (main.py, config.py) |
| Fallback | Run backend locally and expose via ngrok for demo if deploy fails. |
| Demo workaround | Show localhost demo with explanation "production deployed on Railway — demo uses local instance for reliability." |

### R-20: DNS or domain issues block landing access

| Field | Detail |
|---|---|
| Severity | Low |
| Likelihood | Low |
| Trigger | Vercel preview URL blocked, custom domain not propagated |
| Impact | Submission reviewer cannot open landing |
| Mitigation | Vercel provides automatic preview URLs (`*.vercel.app`). No custom domain needed for submission. Both EN and RU landing accessible via query param `?lang=ru` from single deploy. |
| Owner | Frontend (landing) |
| Fallback | GitHub Pages or static HTML mirror if Vercel unavailable. |
| Demo workaround | Record landing walkthrough from localhost if deploy URL is unavailable during recording. |

---

## 8. Timeline

### R-21: Sunday render batch delayed by Runway queue

| Field | Detail |
|---|---|
| Severity | High |
| Likelihood | Medium |
| Trigger | High traffic from other hackathon participants during Sunday evening (20:00-22:00 MSK) |
| Impact | <5 videos ready by Monday morning, insufficient content for demo |
| Mitigation | Start render batch **earlier on Sunday** if agent pipeline finishes ahead of schedule. Default batch time: Sunday 20:00. If available, move to 18:00. Run parallel tasks. Use `gen4_turbo` (2.4× cheaper, likely faster queue) for gallery videos. Hero video uses `gen4.5`. Monday 08:00-10:00 reserved for backup renders only. |
| Owner | PM (schedule) + Backend (parallel task execution) |
| Fallback | Submit with minimum 1 hero video + 2-3 gallery videos + static posters for remaining. 3 complete videos is acceptable for a 3-day PoC. |
| Demo workaround | Frame video count as intentional scope management: "The pipeline generates 7 videos from the same codebase. For the 3-day PoC, we focused on quality over quantity — here are 3 completed campaigns, with 4 more in the generation queue." |

### R-22: Feature freeze violation adds scope creep

| Field | Detail |
|---|---|
| Severity | Medium |
| Likelihood | Low |
| Trigger | "One more feature before Monday" — new adapter, new dashboard widget, multilingual voiceover attempt |
| Impact | Existing pipeline destabilized; no time to test new code; demo breaks |
| Mitigation | Explicit feature freeze: **Sunday 2026-05-10 18:00 MSK** (HANDOFF_CONTEXT §17). After freeze: only backup renders, demo recording, README, submission. WhatsApp/SMS/Push adapters explicitly listed as "production roadmap — not MVP" (TECH_SPEC §6.4, DECISIONS_LOG). |
| Owner | PM (scope discipline) |
| Fallback | If critical bug found after freeze: fix only the bug, do not add features. |
| Demo workaround | N/A — feature freeze is a process gate, not a technical issue. Mention it in README as "MVP scope discipline." |

---

## Risk Heat Map

```
                    Likelihood
                    Low       Medium    High
Severity  High      R-14      R-04      R-07
                    R-15      R-05      R-17
                    R-11      R-08      R-21
                              R-19

          Medium    R-01      R-06      R-02 (low likelihood but)
                    R-03      R-09      R-18
                    R-12      R-10
                    R-13      R-22
                    R-16
                    R-20
```

---

## Top-5 Risks for Submission Day

1. **R-07** — Render queue latency (mitigated: Sunday batch, parallel tasks, fallback assets)
2. **R-04** — Runway moderation flags (mitigated: prompt safety, abstract visuals, generic mode)
3. **R-08** — ffmpeg stitch corruption (mitigated: test Saturday, fallback to single-scene)
4. **R-21** — Sunday batch timing (mitigated: start early if possible, accept 3+ videos as success)
5. **R-17** — Live demo reliability (mitigated: pre-recorded segments, not live one-take)

---

## Review Cadence

| Checkpoint | When | What to verify |
|---|---|---|
| Agent pipeline tested | Saturday midday | Classifier + script generator on all 7 players |
| Video pipeline E2E | Saturday evening | One campaign: approve → generate → stitch → play |
| Final batch start | Sunday 20:00 MSK | All 7 videos queued in parallel |
| Pre-submission secret scan | Monday 14:00 MSK | `make public-check`; `git grep "key_"` |
| Feature freeze | Sunday 18:00 MSK | No new code after this point |
