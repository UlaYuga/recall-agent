from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import agent, approval, delivery, events, metrics, public, tracking, video
from app.config import settings


def _resolve_base_origin(base_url: str) -> str | None:
    parsed = urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _build_cors_origins() -> list[str]:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    base_origin = _resolve_base_origin(settings.base_url)
    if base_origin and base_origin not in origins:
        origins.append(base_origin)
    return origins


app = FastAPI(title="Recall API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_origin_regex=r"^https://[a-z0-9-]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(approval.router, prefix="/approval", tags=["approval"])
app.include_router(video.router, prefix="/video", tags=["video"])
app.include_router(delivery.router, prefix="/delivery", tags=["delivery"])
app.include_router(tracking.router, prefix="/track", tags=["tracking"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(public.router, prefix="/public", tags=["public"])
app.mount(
    "/storage",
    StaticFiles(directory=settings.storage_dir, check_dir=False),
    name="storage",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
