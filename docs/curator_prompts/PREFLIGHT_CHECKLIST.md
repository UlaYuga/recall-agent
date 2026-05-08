# Recall Preflight Checklist

## Current Snapshot

- Timestamp (MSK): 2026-05-08 12:29 MSK
- Git:
  - Branch: `main`
  - HEAD: `828a0b9 Load root env for backend`
  - Working tree (from `git status --short`):
    - `M backend/seeds/events.json`
    - `?? backend/seed/`
    - `?? docs/curator_prompts/`
- Accepted baseline already verified (do not re-litigate; build on it):
  - **B-01 PASS**: `backend/seed/players.json` (7 synthetic players, IDs `p_001..p_007`, 5 Telegram IDs)
  - **B-02 PASS**: `backend/seeds/events.json` (96 events, all linked to B-01 players)
- Coordinator decision (binding for future prompts): seed-related work must use **`backend/seeds/`** going forward (TECH_SPEC + repo), and **must reconcile** B-01’s `backend/seed/players.json` into `backend/seeds/players.json` (or explicitly declare `backend/seed/players.json` as the source).

## Existing Repo Shape

Key paths that already exist and are relevant to T-01/T-02/T-05:

- Repo scaffold (T-01 scope): `.env.example`, `.gitignore`, `README.md`, `Makefile`, `docker-compose.yml`, `.github/workflows/secret-scan.yml`, `scripts/check-public-repo-safety.sh`
- Backend (FastAPI already exists):
  - `backend/app/main.py` (FastAPI app + routers + `/health`)
  - `backend/app/config.py` (pydantic-settings reads `../.env` / `.env`)
  - `backend/app/db.py` (SQLModel engine + `init_db()`)
  - `backend/app/models.py` (SQLModel tables; currently a simplified schema)
  - `backend/app/api/*` routers exist (currently stub responses)
  - `backend/pyproject.toml`, `backend/Dockerfile`, `backend/tests/test_pipeline.py`
- Seed-related files already exist:
  - `backend/seeds/seed.py` (currently a placeholder; does not load JSON into DB yet)
  - `backend/seeds/events.json` (B-02 accepted location; JSON array)
  - `backend/seeds/players.json` (currently **not** B-01; small placeholder list of 2 without `player_id`)
  - `backend/seed/players.json` (B-01 accepted location; JSON list of 7 with `player_id`, `first_name`, `identifiers`, `consent`, etc.)
- Dashboard and landing already exist:
  - `dashboard/` (Next.js app skeleton present)
  - `landing/` (Next.js app skeleton present)

## Source Conflicts

Concrete mismatches the coordinator must account for before issuing executor prompts:

1. **Seed path and format conflict (must mention in prompts):**
   - XLSX (T-05 scope) expects:
     - `backend/seed/players.json`
     - `backend/seed/events.jsonl`
     - `backend/app/seed.py`
   - TECH_SPEC + repo (and coordinator decision) use:
     - `backend/seeds/players.json`
     - `backend/seeds/events.json` (JSON array, not JSONL)
     - `backend/seeds/seed.py`
   - Current repo reality:
     - B-01 exists at `backend/seed/players.json` (untracked per `git status`)
     - B-02 exists at `backend/seeds/events.json` (modified per `git status`)
     - There is no `backend/seed/events.jsonl` in repo

2. **Seed schema conflict (blocks “just load JSON into DB” unless resolved):**
   - B-01 (`backend/seed/players.json`) schema includes keys like `player_id`, `first_name`, `identifiers`, `consent`, timestamps, etc.
   - Current SQLModel `Player` in `backend/app/models.py` expects fields like `external_id`, `name`, `days_inactive`, `marketing_consent`, etc.
   - Current `backend/seeds/players.json` is a different placeholder schema (2 entries; no `player_id` at all).
   - Result: T-05 must explicitly decide whether to:
     - Align models to B-01 schema (likely, because TECH_SPEC implies richer player profile), or
     - Implement a mapping layer that derives the simplified `Player` fields from B-01 JSON.

3. **XLSX task statuses vs repo state (avoid “init from scratch” prompts):**
   - `tasks_for_codex.xlsx` and `master_tracker.xlsx` list T-01/T-02/T-05 as `not started`, but:
     - Scaffold and FastAPI already exist in the repo
     - Seed files exist in *both* `backend/seed/` and `backend/seeds/`
   - `master_tracker.xlsx` lists B-01/B-02 as `not started` and B-02 target path `backend/seed/events.jsonl`, but `docs/curator_prompts/QUEUE_STATUS.md` marks B-01/B-02 **done** and B-02 is verified at `backend/seeds/events.json`.

4. **Environment variable naming drift (minor but causes prompt/test mismatch):**
   - XLSX mentions `DEMO_AUTH_PASSWORD` in verification text for T-01/T-02.
   - Repo uses `DEMO_MANAGER_PASSWORD` (`.env.example`, `backend/app/config.py`). Renamed from `DEMO_PASSWORD` in T-04.
   - Coordinator should standardize future prompts on repo reality unless explicitly choosing to rename variables later.

## T-01 Preflight

**What T-01 expects (per XLSX):**
- “Init repo recall-agent”: create scaffold files (`.env.example`, `.gitignore`, `README.md`, `Makefile`, `docker-compose.yml`) and repo structure from `docs/TECH_SPEC.md`.

**What already exists:**
- The scaffold and full repo structure already exist (including backend/dashboard/landing/docs).
- There is already a safety workflow (`.github/workflows/secret-scan.yml`) and `scripts/check-public-repo-safety.sh`.

**How the coordinator should adapt T-01 prompt:**
- Change T-01 from “create/init repo” to “verify/align scaffold with TECH_SPEC + ensure public repo safety”.
- Explicitly instruct the executor: do not recreate the repo; only reconcile missing bits and document deviations.

**Commands coordinator should ask executor to run (and paste results):**

```bash
git status --short
ls
test -f README.md && sed -n '1,120p' README.md
test -f .env.example && sed -n '1,80p' .env.example
test -f .gitignore && sed -n '1,120p' .gitignore
test -f Makefile && sed -n '1,120p' Makefile
test -f docker-compose.yml && sed -n '1,160p' docker-compose.yml
make public-check
```

## T-02 Preflight

**What T-02 expects (per XLSX):**
- FastAPI skeleton + config: `backend/pyproject.toml`, `backend/app/main.py` with `/health`, config via `pydantic-settings`, DB engine + `create_all`, and “make dev then curl health”.

**What already exists in the repo:**
- `backend/app/main.py` exists and exposes `/health`.
- `backend/app/config.py` exists and reads `.env`.
- `backend/app/db.py` exists and initializes SQLModel metadata.
- `docker-compose.yml` already runs backend on `:8000`.

**What must be checked before issuing T-02:**
- Whether XLSX-required items are missing and should be added during T-02 (example: XLSX mentions CORS middleware; current `backend/app/main.py` has no CORS middleware).
- Whether the expected env var names in the prompt match repo reality (`DEMO_MANAGER_PASSWORD` — renamed from `DEMO_PASSWORD` in T-04).

**Commands coordinator should ask executor to run (and paste results):**

```bash
cd backend && uv run --python 3.11 --extra dev python -c 'import app; print(\"ok\")'
cd /Users/axel/Documents/Проекты/Recall && make dev
# in another shell while docker compose is up:
curl -sS localhost:8000/health
```

## T-05 Preflight

**What T-05 expects (per XLSX):**
- Implement `backend/app/seed.py` to read `backend/seed/players.json` and `backend/seed/events.jsonl`, then write to SQLite so that `make seed` loads 7 players and >50 events.

**How B-01/B-02 affect it:**
- B-01 is already accepted at `backend/seed/players.json` (but is currently untracked).
- B-02 is already accepted at `backend/seeds/events.json` (JSON array, not JSONL; file is currently modified and should be treated as the canonical events seed).

**Path decision for `backend/seeds/` (binding):**
- The executor prompt must treat `backend/seeds/` as the source-of-truth directory going forward, per TECH_SPEC and coordinator decision.

**Specific reconciliation step needed for the players file (must be explicit in prompt):**
- Reconcile/copy **the accepted B-01** `backend/seed/players.json` content into **`backend/seeds/players.json`** (replacing the current 2-row placeholder), or explicitly instruct the seed loader to read from `backend/seed/players.json` but still standardize the canonical location under `backend/seeds/`.

Additional must-check before issuing T-05:
- Decide how to resolve the **schema mismatch** between:
  - accepted seed JSON (B-01/B-02), and
  - current SQLModel tables in `backend/app/models.py`.
  The prompt should force the executor to pick one approach and keep it consistent (do not “half map” and leave the pipeline incoherent).

## Safety Checks

Run these before any push/PR, and ask executors to paste output:

```bash
git status --short
make public-check
git grep -n \"RUNWAYML_API_SECRET\\|TELEGRAM_BOT_TOKEN\\|ANTHROPIC_API_KEY\\|key_\\|\\.env\" -- . ':!.env.example' || true
git ls-files | rg -n '(^|/)\\.env(\\.|$)|(^|/)storage/|\\.(mp4|mov|wav|mp3|webm)$' || true
```

Operational checks:
- Ensure `.env` is local-only (never tracked). The repo already has a guard script: `scripts/check-public-repo-safety.sh`.
- Ensure generated media stays out of git (`storage/` is gitignored) and file sizes remain Telegram-friendly (<50MB per video).
- Keep Runway prompts compliance-friendly: no real faces, no real brands, no logos, no “guaranteed outcomes”, no manipulative urgency.

## Recommended Next Prompt Adjustments

Exact changes the coordinator should make when issuing T-01/T-02/T-05 (copy into the prompt verbatim as needed):

- T-01: Replace “create/init repo” with “verify existing scaffold matches TECH_SPEC; do not recreate repo; list deviations and fix only missing scaffold items”.
- T-01: Add “Run `make public-check` and paste output. Confirm `.env` is not tracked.”
- T-02: Add “Backend already exists; verify `/health` works via `make dev` and `curl`. Only add missing pieces (e.g., CORS) if required by TECH_SPEC/XLSX; do not rewrite structure.”
- T-02: Standardized env var naming to repo reality (`DEMO_PASSWORD` at the time; renamed to `DEMO_MANAGER_PASSWORD` in T-04).
- T-05: Replace XLSX seed paths with coordinator decision:
  - Use `backend/seeds/players.json` + `backend/seeds/events.json` + `backend/seeds/seed.py`.
- T-05: Add a mandatory reconciliation step:
  - “Copy accepted `backend/seed/players.json` into `backend/seeds/players.json` (or explicitly treat `backend/seed/players.json` as source), then update seed loader accordingly.”
- T-05: Force a single schema decision:
  - Either “Update SQLModel models to match B-01/B-02 seed schema” or “Map seed JSON into the current simplified models”, but do not leave mixed schemas.
- All tasks: Add a constraint reminder:
  - International iGaming positioning (not Russia/CIS); Telegram is PoC adapter; WhatsApp/SMS/push are roadmap; classifier must be deterministic; LLM must not decide eligibility/cohort.

## Open Questions

1. For T-05: should the executor **align `backend/app/models.py` to the richer TECH_SPEC/B-01 schema**, or keep the simplified current schema and add a mapping layer from B-01 JSON?
2. For T-02: is CORS middleware required for the MVP dev workflow now (XLSX mentions it), or is it deferred until dashboard/landing integration work begins?
