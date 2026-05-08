# Recall Queue Status

Operational coordinator status. XLSX files remain source of truth for the task plan; this file tracks what was issued in this chat without editing the spreadsheets.

Timezone: MSK.

## Active

| ID | Status | Tool / agent | Issued at MSK | Notes |
|---|---|---|---|---|
| - | - | - | - | None. |

## Review

| ID | Status | Tool / agent | Reviewed at MSK | Notes |
|---|---|---|---|---|
| C-01 | superseded | ChatGPT #1 (Codex) | 2026-05-08 11:55 | Superseded by Alexander's direct process decision: do not pre-generate prompts for T-01..T-10. Coordinator writes prompts just-in-time after each executor result. XLSX not updated by request. |

## Done

| ID | Status | Tool / agent | Reviewed at MSK | Notes |
|---|---|---|---|---|
| B-01 | done | DeepSeek V4 Pro | 2026-05-08 12:00 | Verified `backend/seed/players.json`: valid JSON, 7 players, IDs p_001..p_007, required archetypes, 5 Telegram IDs, synthetic international data. Downstream seed path conflict recorded separately. XLSX not updated by request. |
| B-02 | done | DeepSeek V4 Pro | 2026-05-08 12:26 | Verified `backend/seeds/events.json`: valid JSON, 96 events, required keys, IDs unique, player counts >=10, exact last login/deposit events, currencies and timestamps consistent with B-01 players. XLSX not updated by request. |
| C-02 | done | ChatGPT #2 (Codex) | 2026-05-08 12:40 | Verified `docs/curator_prompts/PREFLIGHT_CHECKLIST.md`: required sections present, B-01/B-02 status included, seed path decision included, repo-specific conflicts and T-01/T-02/T-05 prompt adjustments documented. XLSX not updated by request. |
| C-03 | done | ChatGPT #1 (Codex) | 2026-05-08 12:47 | Verified `docs/curator_prompts/FRONTEND_TASK_BRIEFS.md`: readiness brief structure present, T-12/T-13/T-14/T-29 covered, current dashboard reality documented including singular placeholder route, API gates/states/responsive/a11y/performance notes included. XLSX not updated by request. |
| C-04 | done | ChatGPT #2 (Codex) | 2026-05-08 12:59 | Verified `docs/curator_prompts/RUNWAY_TASK_BRIEFS.md`: readiness brief structure present, T-15..T-21 covered, current Runway stubs documented, model/credit/safety/retry/media checks included, open contract/env/schema questions captured. XLSX not updated by request. |
| B-03 | done | Kimi K2.6 | 2026-05-08 13:06 | Verified `backend/app/agent/fallback_templates.py`: compiles, imports, 6 cohorts, 4 scenes each, required placeholders, 70-110 word filled voiceovers, forbidden terms absent. Future T-08 must wire/import it. XLSX not updated by request. |
| B-04 | done | GLM-5.1 | 2026-05-08 13:17 | Verified `backend/app/runway/visual_hints.py`: compiles, imports, 18 game hints, 12 category hints, required B-01 labels/categories present, `no text`/`no logos` included, forbidden terms absent. Future T-16 must wire/import it. XLSX not updated by request. |
| T-00a | done | Coordinator local (Codex) | 2026-05-08 14:25 | Reconciled seed path: accepted B-01 players moved via `git mv` into `backend/seeds/players.json` after intent-to-add because source was untracked; removed empty `backend/seed/`; verified player IDs match `backend/seeds/events.json`. XLSX not updated. |
| T-00b | done | Coordinator local (Codex) | 2026-05-08 14:25 | Standardized Runway env naming on `RUNWAYML_API_SECRET` in `.env.example`, config and docs; added `docs/DECISIONS_LOG.md` entry; verified zero legacy env-name hits by target audit. XLSX not updated. |
| T-01 | done | ChatGPT #1 (Codex), GPT-5.3-Codex, reasoning medium | 2026-05-08 14:37 | PASS. Verified scaffold structure/files, no legacy Runway env-name hits, seed IDs match, `.env` and generated media are ignored, `make public-check` passes, working tree clean. Executor made no extra changes beyond already checkpointed safety-script alignment. XLSX not updated. |

## Blocked

| ID | Status | Owner | Recorded at MSK | Notes |
|---|---|---|---|---|
| SEED-PATH | resolved | Alexander / Coordinator | 2026-05-08 14:25 | Decision: next tasks use existing `backend/seeds/` path as in `TECH_SPEC.md` and current repo. This overrides XLSX `backend/seed/` path for future prompts. T-00a reconciled B-01 players into `backend/seeds/players.json` and removed `backend/seed/`. XLSX not updated. |
| T-05-SCHEMA | resolved | Alexander / Claude review | 2026-05-08 14:14 | Align SQLModel models to rich B-01/TECH_SPEC schema. Do not map rich seed JSON into current simplified models. |
| T-02-CORS | resolved | Alexander / Claude review | 2026-05-08 14:14 | Add CORS immediately in T-02 because dashboard and landing will run on separate origins. |
| T-15-RUNWAY-ENV | resolved | Alexander / Claude review / Coordinator | 2026-05-08 14:25 | Use `RUNWAYML_API_SECRET`. T-00b aligned `.env.example`, config and relevant docs; T-04/T-15 prompts must keep this name. |
| T-21-VIDEO-CONTRACT | resolved | Alexander / Claude review | 2026-05-08 14:14 | Use TECH_SPEC contract: `POST /video/generate` with body `{campaign_id}`, `GET /video/status/{task_id}`. |

## Queue Notes

- Do not update `master_tracker.xlsx` or `tasks_for_codex.xlsx` unless Alexander explicitly asks.
- Before issuing the next dependent task, check this file and the XLSX dependencies.
- Initial pre-15:00 executor gate was lifted by Alexander at 2026-05-08 14:29 MSK because tokens became available. T-01 may be issued early after T-00a/T-00b PASS.
- Coordinator writes full self-contained prompts. Executor chats should not be asked to extract their own task from XLSX.
- Every issued prompt must include target LLM/account, exact model/version when known, recommended reasoning mode (low/medium/high), and a short reason for that routing.
- Git rule from 2026-05-08 14:33 MSK: after coordinator review marks a task `PASS`, run fresh verification, stage only task-scoped files plus status docs, commit with the task ID in the message, then push to the tracked remote branch. Do not commit/push `FAIL`, `BLOCKED`, unrelated dirty files, real secrets, XLSX edits, or generated media unless Alexander explicitly asks.
- Alexander sends each executor result back to the coordinator chat. The next dependent prompt must be adapted to the actual result, changed files, verification output and open issues.
- Do not spend work on full prompt packs for future dependent tasks. Prepare only the next task that is ready to issue now, plus minimal notes needed to adapt the following task after review.
- Next implementation prompt: `T-02` after T-01 PASS review.
