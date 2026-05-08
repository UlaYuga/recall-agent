# Recall Work Completed Log

Last updated: 2026-05-08 14:14 MSK.

## Count

Master tracker has 55 valid tasks:

- `T-*`: 35
- `B-*`: 16
- `C-*`: 4

Coordinator-verified done:

- `7 / 55` total tasks done.
- `1 / 55` superseded (`C-01`), not counted as done.
- Remaining not done: `48 / 55`.

Pre-Claude block status:

- Planned pre-Claude IDs: `C-01`, `C-02`, `C-03`, `C-04`, `B-01`, `B-02`, `B-03`, `B-04`.
- Useful completed: `7 / 8`.
- `C-01` was intentionally superseded because Alexander decided prompts must be written just-in-time, not pre-generated for future dependent tasks.

## Done Tasks

### B-01 — Mock players JSON x7

Status: PASS.

Artifact:

- `backend/seed/players.json`

Verification:

- Valid JSON.
- 7 players.
- IDs `p_001..p_007`.
- Required archetypes present.
- 5 Telegram IDs.
- Synthetic international data only.

Important note:

- This accepted file is under `backend/seed/`.
- Future canonical seed path is `backend/seeds/`.

### B-02 — Events history seed

Status: PASS.

Artifact:

- `backend/seeds/events.json`

Verification:

- Valid JSON.
- 96 events.
- Required keys.
- Unique event IDs.
- Every player has at least 10 events.
- Exact last login/deposit events match B-01 players.
- Currencies and timestamps consistent.

### C-02 — Preflight repo/docs consistency checklist

Status: PASS.

Artifact:

- `docs/curator_prompts/PREFLIGHT_CHECKLIST.md`

What it captured:

- Existing repo shape.
- Seed path conflict.
- T-01/T-02/T-05 prompt adjustments.
- Open decisions around model schema and CORS.

### C-03 — Frontend readiness brief

Status: PASS.

Artifact:

- `docs/curator_prompts/FRONTEND_TASK_BRIEFS.md`

What it captured:

- Current dashboard scaffold.
- T-12/T-13/T-14/T-29 readiness notes.
- API gates.
- UI states.
- Responsive/accessibility checks.
- React/Next performance notes.

### C-04 — Runway readiness brief

Status: PASS.

Artifact:

- `docs/curator_prompts/RUNWAY_TASK_BRIEFS.md`

What it captured:

- Current Runway stubs.
- T-15..T-21 readiness notes.
- Model/credit rules.
- Prompt safety policy.
- Retry/failure policy.
- Media/ffmpeg/Telegram size checks.
- Open decisions around Runway env and video API contract.

### B-03 — Fallback script templates per cohort

Status: PASS.

Artifact:

- `backend/app/agent/fallback_templates.py`

Verification:

- Python compiles.
- Imports.
- 6 cohorts.
- 4 scenes per cohort.
- Required placeholders present.
- Filled voiceovers are 70-110 words.
- Forbidden terms absent.

Future use:

- T-08 must wire/import this into `script_generator.py`.

### B-04 — GAME_VISUAL_HINTS mapping

Status: PASS.

Artifact:

- `backend/app/runway/visual_hints.py`

Verification:

- Python compiles.
- Imports.
- 18 game hints.
- 12 category hints.
- Required B-01 labels/categories present.
- Every hint includes `no text` and `no logos`.
- Forbidden terms absent.

Future use:

- T-16 must wire/import this into prompt safety.

## Superseded

### C-01 — Curator prompt pack T-01..T-10

Status: superseded, not done.

Reason:

- Alexander clarified the workflow:
  - do not create prompt packs for many future dependent tasks;
  - coordinator writes each next task just-in-time after reviewing the previous result.

## Decisions Made

### Status Tracking

Do not update XLSX unless Alexander explicitly asks.

Use:

- `docs/curator_prompts/QUEUE_STATUS.md`

### Seed Path

Use `backend/seeds/` going forward.

Reason:

- TECH_SPEC and current repo use `backend/seeds/`.
- XLSX had `backend/seed/`, but this is overridden by Alexander’s direct decision.

### Prompt Workflow

Executor chats get self-contained prompts.

They do not inspect XLSX to discover scope.

Coordinator reviews each result and adapts the next prompt.

## Resolved Questions From Claude Review

### 1. T-00 Numbering

Decision: use local `T-00`.

Reason:

- Seed path drift is real and should be fixed before T-01.
- It should not be hidden inside T-01 because it touches accepted B-01/B-02 artifacts and canonical path.
- XLSX is not edited; `T-00` is a coordinator-local task.

### 2. Frontend Stack

Decision: stay with Next.js + shadcn/Tailwind.

Reason:

- TECH_SPEC and repo already use Next.js dashboard/landing.
- C-03 frontend brief is built around current Next scaffold.
- Streamlit is faster, but would create a second UI stack and fight current repo shape.

### 3. Runway Env Naming

Decision: use `RUNWAYML_API_SECRET`.

Implementation guidance:

- T-04/T-15 should update `.env.example`, config and handoff/current docs.
- Patch TECH_SPEC/DECISIONS_LOG references if they create implementation drift.
- Do not leave both env names active unless backward compatibility is explicitly requested.

### 4. T-05 Schema

Decision: align SQLModel to rich B-01/TECH_SPEC schema.

Reason:

- Simplified mapping loses consent, delivery, vertical/category/label, LTV and Telegram fields.

### 5. T-02 CORS

Decision: add CORS now.

Reason:

- Dashboard and landing will call backend from separate origins.

### 6. T-21 API Contract

Decision: use TECH_SPEC contract:

- `POST /video/generate` body `{campaign_id}`
- `GET /video/status/{task_id}`

Reason:

- One campaign can create multiple Runway retry tasks.

## Next Task

No more pre-Claude tasks are left under the original before-15:00 constraint.

At 15:00 MSK, next planned task is `T-00`:

```text
Seed path reconcile.
```

Then `T-01`, adapted as:

```text
Verify and align existing scaffold with TECH_SPEC and public repo safety.
```

Do not issue a greenfield “init repo” prompt.

## Files Created Or Modified During Pre-Claude Work

Accepted generated artifacts:

- `backend/seed/players.json`
- `backend/seeds/events.json`
- `backend/app/agent/fallback_templates.py`
- `backend/app/runway/visual_hints.py`
- `docs/curator_prompts/QUEUE_STATUS.md`
- `docs/curator_prompts/PREFLIGHT_CHECKLIST.md`
- `docs/curator_prompts/FRONTEND_TASK_BRIEFS.md`
- `docs/curator_prompts/RUNWAY_TASK_BRIEFS.md`
- `docs/curator_prompts/NEXT_COORDINATOR_MEGA_PROMPT.md`
- `docs/curator_prompts/CLAUDE_HANDOFF_CURRENT_TASKS.md`
- `docs/curator_prompts/WORK_COMPLETED_LOG.md`
