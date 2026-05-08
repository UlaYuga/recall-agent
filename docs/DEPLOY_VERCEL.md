# Vercel Deploy — Landing + Dashboard

Vercel deploy documentation for the two frontend apps.

> **Status:** prep only. Do NOT deploy until T-26 (reactivation page) is PASS.
> Backend is already live at T-32.

---

## Overview

| App | Root directory | Framework | Deploy target |
|---|---|---|---|
| **Landing** | `landing/` | Next.js 15.5.15 | Vercel — public case study + reactivation pages |
| **Dashboard** | `dashboard/` | Next.js 15.5.15 | Vercel — internal CRM approval + metrics UI |

Both apps share the same backend API:
- `NEXT_PUBLIC_API_URL=https://recall-agent-production-4dc7.up.railway.app`

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

## Deploy Steps (execute after T-26 PASS)

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
curl -fsS "https://LANDING_URL_TBD/" >/dev/null

# 2. Case study page loads
curl -fsS "https://LANDING_URL_TBD/case" >/dev/null

# 3. Reactivation page loads (use a seeded campaign ID)
curl -fsS "https://LANDING_URL_TBD/r/cmp_001" >/dev/null
```

### Dashboard

```bash
# 1. Root (approval queue) loads
curl -fsS "https://DASHBOARD_URL_TBD/" >/dev/null

# 2. Metrics page loads
curl -fsS "https://DASHBOARD_URL_TBD/metrics" >/dev/null

# 3. Can reach backend health (CORS must allow dashboard origin)
curl -fsS "https://recall-agent-production-4dc7.up.railway.app/health" >/dev/null

# 4. Can fetch approval queue
curl -fsS "https://recall-agent-production-4dc7.up.railway.app/approval/queue" >/dev/null
```

### Browser checks

1. Open `https://LANDING_URL_TBD/` — hero renders, Cyrillic text is readable.
2. Open `https://LANDING_URL_TBD/r/cmp_001` — video player placeholder + offer + CTA button loads.
3. Open `https://DASHBOARD_URL_TBD/` — login gate appears; enter manager password.
4. After login — approval queue table renders with player names, cohort badges, risk scores.
5. Click a row — side panel opens with profile, script scenes, offer, action buttons.

---

## CORS Check

The backend (`recall-agent-production-4dc7.up.railway.app`) must allow CORS from the Vercel origins.

Current CORS config in `backend/app/main.py` should include:

```python
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://LANDING_URL_TBD",
    "https://DASHBOARD_URL_TBD",
]
```

> After T-33 deploy, update the backend CORS allowlist with the real Vercel URLs and redeploy the backend if necessary.

---

## Public Repo Safety

- Do not commit Vercel tokens or project IDs to git.
- `.vercel/` is already in `.gitignore` (verify if not).
- `NEXT_PUBLIC_API_URL` is safe to expose — it is a public backend URL.
- `NEXT_PUBLIC_DEMO_MANAGER_PASSWORD` is a demo placeholder; do not reuse a real password.
- Run `make public-check` before every push.

---

## Production URLs

> **Landing and dashboard Vercel URLs are TBD until T-33 real deploy.**
>
> - Landing: `LANDING_URL_TBD`
> - Dashboard: `DASHBOARD_URL_TBD`

Backend URL (from T-32):
- `https://recall-agent-production-4dc7.up.railway.app`

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

- [ ] Landing root returns 200
- [ ] Landing `/case` returns 200
- [ ] Landing `/r/cmp_001` returns 200
- [ ] Dashboard root returns 200
- [ ] Dashboard `/metrics` returns 200
- [ ] Backend `/health` reachable from dashboard browser (CORS OK)
- [ ] Backend `/approval/queue` reachable from dashboard browser
- [ ] `NEXT_PUBLIC_API_URL` set to `https://recall-agent-production-4dc7.up.railway.app` on both projects
- [ ] `NEXT_PUBLIC_DEMO_MANAGER_PASSWORD` set on dashboard project
- [ ] Real Vercel URLs added to backend CORS allowlist
- [ ] README "Deploy Status" section updated with live URLs
- [ ] `docs/ARCHITECTURE.md` deployment placeholders updated
- [ ] `docs/SUBMISSION.md` deploy placeholders updated
- [ ] `make public-check` passes
- [ ] `git diff --check` passes
