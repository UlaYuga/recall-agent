from fastapi import FastAPI

from app.api import agent, approval, delivery, events, tracking, video

app = FastAPI(title="Recall API", version="0.1.0")

app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(approval.router, prefix="/approval", tags=["approval"])
app.include_router(video.router, prefix="/video", tags=["video"])
app.include_router(delivery.router, prefix="/delivery", tags=["delivery"])
app.include_router(tracking.router, prefix="/track", tags=["tracking"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

