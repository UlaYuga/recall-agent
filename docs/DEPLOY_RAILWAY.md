# Railway Backend Deploy

## Project and Service

- Railway project: pending CLI link verification.
- Railway service: backend service connected to the GitHub repository.
- Repository path: `backend/`.
- Config file: `backend/railway.toml`.

The local Railway CLI is not currently linked to this repository. `railway status`
returns `Project not found`, and `railway whoami` fails locally on DNS lookup for
`backboard.railway.app`. Do not run `railway init` for this repo unless a new
Railway project is intentionally required.

If the service is configured from the Railway dashboard, set:

- Root Directory: `backend`
- Config File Path: `/backend/railway.toml`
- Public networking: enabled
- Healthcheck path: `/health`

## Backend URL

- Public backend URL: pending Railway deployment verification.
- Health endpoint: `GET /health`
- API docs: `GET /docs`

After deployment, verify:

```bash
curl -fsS "$BACKEND_URL/health"
curl -fsS "$BACKEND_URL/docs" >/dev/null
```

## Environment Variables

Set these names in Railway. Do not paste secret values into git or docs.

- `RUNWAYML_API_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `ANTHROPIC_API_KEY`
- `BASE_URL`
- `DEMO_MANAGER_PASSWORD`
- `DATABASE_URL`
- `STORAGE_DIR`

Do not add deprecated aliases for the Runway secret or manager password.

Recommended non-secret values:

- `BASE_URL`: the public Railway backend URL.
- `STORAGE_DIR`: `/app/storage` when using the Docker image.
- `DATABASE_URL`: a Railway Postgres URL for persistent deploys, or
  `sqlite:////app/storage/recall.db` for a demo deploy with an attached volume.

## Deploy Command

When the CLI is linked to the correct project and backend service:

```bash
railway up
```

If GitHub autodeploy is enabled for the backend service, pushing `origin/main`
can trigger the deployment instead of `railway up`.

## Troubleshooting

- If the service starts locally but fails on Railway, check that it listens on
  `0.0.0.0:$PORT`. The Dockerfile uses `${PORT:-8000}` for Railway compatibility
  and local fallback.
- If `/health` fails, inspect Railway deploy logs first; the FastAPI app exposes
  `GET /health` and should return `{"status":"ok"}`.
- If media generation fails, confirm `ffmpeg` is available in the image. The
  backend Dockerfile installs system `ffmpeg`.
- If generated media or SQLite data must survive redeploys, attach a Railway
  volume and point `STORAGE_DIR` and demo SQLite `DATABASE_URL` at that mount.
- If the CLI prints `Project not found`, run `railway link` only after confirming
  the intended existing Railway project/service. Do not create a random new
  project for this repository.
