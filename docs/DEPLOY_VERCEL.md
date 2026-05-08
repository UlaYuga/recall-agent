# Vercel Deploy — Landing + Dashboard

Vercel deploy documentation for the two frontend apps.

> **Status:** deployed and smoke-tested on 2026-05-09 MSK.
> Backend is live from T-32.

---

## Overview

| App | Root directory | Framework | Deploy target |
|---|---|---|---|
| **Landing** | `landing/` | Next.js 15.5.15 | Vercel — public case study + reactivation pages |
| **Dashboard** | `dashboard/` | Next.js 15.5.15 | Vercel — internal CRM approval + metrics UI |

Both apps share the same backend API:
- `NEXT_PUBLIC_API_URL=https://recall-agent-production-4dc7.up.railway.app`

Production frontend URLs:
- Landing: `https://landing-ula-lab.vercel.app`
- Dashboard: `https://dashboard-ula-lab.vercel.app`

---

## Landing (`landing/`)

### Project settings

| Setting | Value |
|---|---|
| Framework preset | Next.js |
| Root directory | `landing` |
| Build command | `npm run build` |
| Dev command | `npm run dev` |
| Output directory | `.next` |
| Install command | `npm install` |

### Environment variables

Set these in the Vercel project dashboard (Settings → Environment Variables):

| Name | Value | Type |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://recall-agent-production-4dc7.up.railway.app` | Production |
| `NEXT_PUBLIC_DASHBOARD_URL` | `https://dashboard-ula-lab.vercel.app` | Production |

No secrets are required for the landing app. `NEXT_PUBLIC_API_URL` is a public backend endpoint.

### Routes

| Route | Purpose |
|---|---|
| `/` | Hero, concept, demo video, how it works, tech stack, CTA |
| `/case` | Case study with screenshots and metrics |
| `/r/[campaign_id]` | Per-player reactivation landing page (video + offer + mock deposit) |

### Pre-deploy build check (local)

```bash
cd landing
npm install
npm run build
```

Expected: build completes with `✓` and outputs to `.next/`.

---

## Dashboard (`dashboard/`)

### Project settings

| Setting | Value |
|---|---|
| Framework preset | Next.js |
| Root directory | `dashboard` |
| Build command | `npm run build` |
| Dev command | `npm run dev` |
| Output directory | `.next` |
| Install command | `npm install` |

### Environment variables

Set these in the Vercel project dashboard (Settings → Environment Variables):

| Name | Value | Type |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://recall-agent-production-4dc7.up.railway.app` | Production |
| `NEXT_PUBLIC_DEMO_MANAGER_PASSWORD` | *(same value as Railway `DEMO_MANAGER_PASSWORD`)* | Production |

> **Safety note:** `NEXT_PUBLIC_DEMO_MANAGER_PASSWORD` is exposed to the browser because the dashboard uses client-side auth for the PoC. This is acceptable for a hackathon demo with a single shared manager password. Do not use a real or reused password.

### Routes

| Route | Purpose |
|---|---|
| `/` | Approval queue — table, filters, side-panel preview/edit |
| `/campaigns/[id]` | Campaign detail — video player, metadata, delivery CTA |
| `/metrics` | Metrics dashboard — funnel, cohort table, ROI calculator |

### Pre-deploy build check (local)

```bash
cd dashboard
npm install
npm run build
```

Expected: build completes with `✓` and outputs to `.next/`.

---

## Deploy Steps

### 1. Landing

```bash
# Option A: Vercel CLI
cd landing
vercel --prod

# Option B: GitHub integration
# Link the repo in Vercel dashboard, set root directory to `landing`,
# push to `main` triggers deploy.
```

### 2. Dashboard

```bash
# Option A: Vercel CLI
cd dashboard
vercel --prod

# Option B: GitHub integration
# Link the repo in Vercel dashboard, set root directory to `dashboard`,
# push to `main` triggers deploy.
```

> **Important:** if using a single GitHub repo with two Vercel projects, configure each project with the correct **Root Directory** so Vercel only builds the relevant app.

---

## Smoke Checks (after deploy)

### Landing

```bash
# 1. Root returns 200
curl -fsS "https://landing-ula-lab.vercel.app/" >/dev/null

# 2. Case study page loads
curl -fsS "https://landing-ula-lab.vercel.app/case" >/dev/null

# 3. Reactivation page loads (use a seeded campaign ID)
curl -fsS "https://landing-ula-lab.vercel.app/r/cmp_001" >/dev/null
```

### Dashboard

```bash
# 1. Root (approval queue) loads
curl -fsS "https://dashboard-ula-lab.vercel.app/" >/dev/null

# 2. Metrics page loads
curl -fsS "https://dashboard-ula-lab.vercel.app/metrics" >/dev/null

# 3. Can reach backend health (CORS must allow dashboard origin)
curl -fsS "https://recall-agent-production-4dc7.up.railway.app/health" >/dev/null

# 4. Can fetch approval queue
curl -fsS "https://recall-agent-production-4dc7.up.railway.app/approval/queue" >/dev/null
```

### Browser checks

1. Open `https://landing-ula-lab.vercel.app/` — hero renders, Cyrillic text is readable.
2. Open `https://landing-ula-lab.vercel.app/r/cmp_001` — video player placeholder + offer + CTA button loads.
3. Open `https://dashboard-ula-lab.vercel.app/` — login gate appears; enter manager password.
4. After login — approval queue table renders with player names, cohort badges, risk scores.
5. Click a row — side panel opens with profile, script scenes, offer, action buttons.

---

## CORS Check

The backend (`recall-agent-production-4dc7.up.railway.app`) must allow CORS from the Vercel origins.

Current CORS config in `backend/app/main.py` allows local dashboard/landing origins and Vercel preview/production origins:

```python
allow_origin_regex = r"^https://[a-z0-9-]+\.vercel\.app$"
```

Verified CORS preflight from:
- `https://landing-ula-lab.vercel.app`
- `https://dashboard-ula-lab.vercel.app`

---

## Public Repo Safety

- Do not commit Vercel tokens or project IDs to git.
- `.vercel/` is already in `.gitignore` (verify if not).
- `NEXT_PUBLIC_API_URL` is safe to expose — it is a public backend URL.
- `NEXT_PUBLIC_DEMO_MANAGER_PASSWORD` is a demo placeholder; do not reuse a real password.
- Run `make public-check` before every push.

---

## Production URLs

- Landing: `https://landing-ula-lab.vercel.app`
- Dashboard: `https://dashboard-ula-lab.vercel.app`
- Backend: `https://recall-agent-production-4dc7.up.railway.app`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Build fails with "Cannot find module" | `node_modules` not installed in correct root | Ensure Vercel root directory is `landing` or `dashboard`, not repo root |
| Runtime 404 on `/r/[campaign_id]` | `next.config.mjs` missing `trailingSlash` or `export` settings | Keep dynamic routes; do not static-export if reactivation pages need SSR |
| Dashboard cannot call backend | CORS blocks Vercel origin | Add real Vercel URL to backend CORS allowlist and redeploy backend |
| `NEXT_PUBLIC_` var missing at runtime | Set in Production environment, not Preview | Check Vercel env var scope |
| Landing Cyrillic text broken | Font not loaded or Tailwind config missing Cyrillic-safe font | Verify `landing/app/layout.tsx` loads a Cyrillic-safe font (e.g., Inter) |

---

## Post-Deploy Checklist

- [x] Landing root returns 200
- [x] Landing `/case` returns 200
- [x] Landing `/r/cmp_001` returns 200
- [x] Dashboard root returns 200
- [x] Dashboard `/metrics` returns 200
- [x] Backend `/health` reachable from dashboard browser (CORS OK)
- [x] Backend `/approval/queue` reachable from dashboard browser
- [x] `NEXT_PUBLIC_API_URL` set to `https://recall-agent-production-4dc7.up.railway.app` on both projects
- [x] `NEXT_PUBLIC_DEMO_MANAGER_PASSWORD` set on dashboard project
- [x] Real Vercel URLs added to backend CORS allowlist
- [x] README "Deploy Status" section updated with live URLs
- [x] `docs/ARCHITECTURE.md` deployment placeholders updated
- [x] `docs/SUBMISSION.md` deploy placeholders updated
- [x] E2E smoke test passed: seed → scan → approve → track → metrics
- [x] `make public-check` passes
- [x] `git diff --check` passes
