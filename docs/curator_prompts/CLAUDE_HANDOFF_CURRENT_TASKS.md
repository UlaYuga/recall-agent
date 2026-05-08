# Claude Handoff: Recall Current Tasks

Last updated: 2026-05-08 14:14 MSK.

This file is for a Claude Code executor or reviewer to quickly understand the current Recall repo state before taking an implementation task.

## Project

Recall is an AI CRM Reactivation Agent for international iGaming operators.

Core demo spine:

```text
event history -> deterministic cohort classifier -> offer rules -> LLM/fallback script -> manager approval -> Runway media generation -> Telegram/email delivery -> landing tracking -> metrics/ROI
```

## Source Priority

Use in this order:

1. Direct Alexander/coordinator prompt for the current task.
2. `docs/curator_prompts/QUEUE_STATUS.md`
3. `docs/curator_prompts/PREFLIGHT_CHECKLIST.md`
4. `docs/curator_prompts/FRONTEND_TASK_BRIEFS.md`
5. `docs/curator_prompts/RUNWAY_TASK_BRIEFS.md`
6. `tasks_for_codex.xlsx` / `master_tracker.xlsx`
7. `docs/HANDOFF_CONTEXT.md`
8. `docs/TECH_SPEC.md`
9. `docs/DECISIONS_LOG.md`
10. research docs.

Do not edit XLSX unless explicitly told.

## Completed Pre-Claude Work

Done by coordinator review:

| ID | Artifact |
|---|---|
| B-01 | `backend/seed/players.json` |
| B-02 | `backend/seeds/events.json` |
| C-02 | `docs/curator_prompts/PREFLIGHT_CHECKLIST.md` |
| C-03 | `docs/curator_prompts/FRONTEND_TASK_BRIEFS.md` |
| C-04 | `docs/curator_prompts/RUNWAY_TASK_BRIEFS.md` |
| B-03 | `backend/app/agent/fallback_templates.py` |
| B-04 | `backend/app/runway/visual_hints.py` |

Superseded:

| ID | Reason |
|---|---|
| C-01 | Do not pre-generate prompts for all future tasks. Coordinator writes prompts just-in-time after each result. |

## Important Accepted Files

### `backend/seed/players.json`

Accepted B-01 output:

- 7 synthetic players.
- IDs `p_001..p_007`.
- International markets: BR, MX, ZA, RO, GB, ES, NO.
- 5 players have Telegram IDs.
- Rich player schema: identifiers, consent, favorite vertical/category/label, timestamps, deposits, LTV.

Important: this accepted file currently lives under `backend/seed/`, but future canonical seed path is `backend/seeds/`.

### `backend/seeds/events.json`

Accepted B-02 output:

- 96 events.
- Valid JSON array.
- Linked to B-01 player IDs.
- Every player has at least 10 events.
- Exact last login/deposit events match player profiles.

### `backend/app/agent/fallback_templates.py`

Accepted B-03 output:

- `FALLBACK_TEMPLATES`.
- 6 cohorts.
- 4 scenes per cohort.
- English, warm, compliant copy.
- Future T-08 must wire/import this into `script_generator.py`.

### `backend/app/runway/visual_hints.py`

Accepted B-04 output:

- `GAME_VISUAL_HINTS`: 18 entries.
- `CATEGORY_VISUAL_HINTS`: 12 entries.
- `DEFAULT_VISUAL_HINT`.
- Optional `get_visual_hint(...)`.
- Every hint includes `no text` and `no logos`.
- Future T-16 must wire/import this into prompt safety.

## Key Decisions

### Seed Path

Use `backend/seeds/` going forward.

Reason:

- TECH_SPEC and current repo use `backend/seeds/`.
- XLSX still mentions `backend/seed/` for T-05, but Alexander chose `backend/seeds/`.

Next seed task must reconcile:

- accepted `backend/seed/players.json`
- into canonical `backend/seeds/players.json`

Do not silently keep two divergent player files.

### Prompt Process

Do not prebuild all future prompts.

Coordinator writes one self-contained task at a time, after reviewing the previous result.

### XLSX

XLSX remains plan source, but not status source for this chat. Status is local in `QUEUE_STATUS.md`.

## Resolved Implementation Decisions

### T-00 Seed Reconcile

Add a local coordinator task before T-01:

```text
T-00 — Seed path reconcile
```

Scope:

- `git mv backend/seed/players.json backend/seeds/players.json`
- remove empty `backend/seed/`
- verify `backend/seeds/events.json` references the same `p_001..p_007`

Do not copy and leave duplicate player files.

### T-05 Schema

Decision: align SQLModel models to rich B-01/TECH_SPEC schema.

Reason:

- Simplified current models lose consent flags, vertical/category/label, LTV and Telegram fields.
- Agent, delivery and tracking need those fields.

Do not map rich seed JSON into simplified models.

### T-02 CORS

Decision: add CORS immediately in T-02.

Reason:

- Dashboard and landing will run on different origins in local/dev/deploy.

### T-15 Runway Env Name

Decision: use `RUNWAYML_API_SECRET`.

Reason:

- Runway SDK docs/troubleshooting expect `RUNWAYML_API_SECRET`.
- `RunwayML()` can pick it up from env.
- Legacy Runway env naming in TECH_SPEC/current repo is drift.

Future T-15/T-04 should align `.env.example`, config and handoff docs. Patch TECH_SPEC/DECISIONS_LOG references if they create implementation drift.

### T-21 Video API Contract

Decision: use TECH_SPEC contract.

- `POST /video/generate` with body `{ "campaign_id": "..." }`
- `GET /video/status/{task_id}`

Reason:

- One campaign can create multiple retry tasks.
- The polling object is a Runway/internal task, not the campaign itself.

## Next Likely Task

After 15:00 MSK, next planned Claude task is `T-00`.

```text
Seed path reconcile.
```

After T-00, run adapted `T-01`.

Do not initialize from scratch.

Adapted T-01 should be:

```text
Verify and align existing scaffold with TECH_SPEC and public repo safety.
```

Expected behavior:

- inspect existing repo;
- preserve accepted B/C artifacts;
- verify scaffold files;
- fix only missing scaffold items;
- run safety checks;
- report deviations.

## Updated Execution Order

1. `T-00` — Seed path reconcile.
2. `T-01` — Verify+align scaffold.
3. `T-02` — FastAPI app + CORS + health.
4. `T-03` — DB + SQLModel base.
5. `T-04` — Pydantic settings with `RUNWAYML_API_SECRET`.
6. `T-05` — Rich models.
7. `T-06` — Seed loader from `backend/seeds/players.json` + `backend/seeds/events.json`.
8. `T-07` — Deterministic classifier.
9. `T-08` — Script generator + B-03 fallback wire.
10. `T-09` — Offer rules.
11. `T-10` — `/agent/scan` + `/agent/decide`.

## Current Dirty State

Expected dirty/untracked work includes accepted artifacts:

- `M backend/seeds/events.json`
- `?? backend/seed/`
- `?? backend/app/agent/fallback_templates.py`
- `?? backend/app/runway/visual_hints.py`
- `?? docs/curator_prompts/`

Do not revert these.

## Safety Rules

- No real secrets.
- `.env` must not be committed.
- Generated media should not be committed unless explicitly selected as demo artifact.
- No real faces/logos/brands in Runway prompts.
- No guaranteed outcomes.
- No manipulative urgency.
- Classifier is deterministic; LLM does not decide eligibility/cohort.
- Runway calls stay under `backend/app/runway`.
