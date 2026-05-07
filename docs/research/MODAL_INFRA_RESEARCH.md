# Recall - Modal Infrastructure Research

**Date:** 2026-05-07  
**Purpose:** Decide how Modal should and should not be used in Recall.  
**Primary sources:**  
- Modal docs: https://modal.com/docs  
- Modal pricing: https://modal.com/pricing  
- Modal batch processing: https://modal.com/docs/guide/batch-processing  
- Modal web endpoints: https://modal.com/docs/guide/webhooks  
- Modal secrets: https://modal.com/docs/guide/secrets  
- Modal volumes: https://modal.com/docs/guide/volumes  

---

## 1. Executive summary

Modal should **not** be a required dependency for Recall MVP.

Modal should be documented as an optional production/batch worker layer for:

- ffmpeg stitching at scale;
- async render post-processing;
- batch asset generation;
- future self-hosted inference;
- worker isolation;
- public callback endpoints if needed.

For the three-day PoC:

```text
FastAPI backend + local/Railway ffmpeg is enough.
Modal is a roadmap/fallback, not core spine.
```

This is a good PM/Delivery decision because it avoids adding cloud-infra complexity before the product workflow is proven.

---

## 2. Modal facts relevant to Recall

### 2.1 Product positioning

Modal describes itself as serverless cloud for compute-intensive applications, including generative AI, batch workflows and job queues.

Implication for Recall:

- Modal is useful if media post-processing becomes compute-heavy.
- Modal is not needed to call Runway API itself; Runway does the actual generation.
- Recall needs orchestration and ffmpeg more than GPUs.

### 2.2 Pricing and free tier

Modal pricing page confirms:

- Starter plan has $30/month free credits.
- You pay for actual compute time, not idle resources.
- Starter includes 100 containers and 10 GPU concurrency.
- Starter has limited crons and web endpoints.
- CPU/memory/GPU billed per second.

Implication:

- Modal is attractive for a PoC because there is no idle server cost.
- But using Modal still costs setup/debugging time.
- For hackathon timeline, only use Modal if local/Railway ffmpeg blocks.

### 2.3 Batch processing

Modal batch docs confirm that Modal can scale batch processing and supports async/background execution.

Implication:

- Good fit for future production batch video post-processing.
- Good fit for processing 5,000 generated videos if Recall becomes real.
- Not needed for 5-7 videos in MVP.

### 2.4 Web endpoints

Modal can expose Python functions as web endpoints and serve FastAPI/ASGI apps.

Implication:

- Modal could host a render worker endpoint.
- Modal could host the entire backend, but that is not recommended for MVP because Railway/Render are simpler for a normal FastAPI service.

### 2.5 Secrets

Modal supports secrets via dashboard, CLI and Python `modal.Secret`.

Implication:

- If using Modal, store `RUNWAYML_API_SECRET`, not raw `.env` values in code.
- Use separate secrets for Runway, Telegram and backend auth.

### 2.6 Volumes

Modal Volumes provide distributed storage for write-once/read-many workflows.

Implication:

- Useful for storing intermediate clips and stitched mp4 files if render workers run on Modal.
- But for MVP, local `/storage` or Railway volume is simpler.

---

## 3. Modal decision for Recall

### 3.1 MVP decision

Do not implement Modal in default MVP.

Use:

```text
FastAPI backend -> Runway API -> download outputs -> local/Railway ffmpeg -> local/Railway storage
```

Document:

```text
ModalRenderWorker is production roadmap and emergency fallback if deployment ffmpeg fails.
```

### 3.2 Fallback decision

Use Modal only if one of these happens:

- Railway/Render does not have ffmpeg or cannot install it quickly.
- Local machine cannot process assets reliably.
- Need public endpoint for render tasks and Railway is unstable.
- Need parallel post-processing for final video batch.

### 3.3 Production decision

In production:

```text
FastAPI orchestration API
  -> queue render jobs
  -> Modal worker downloads Runway outputs
  -> ffmpeg stitch
  -> write output to object storage
  -> callback/write-back to Recall backend
```

Modal becomes worker pool, not product brain.

---

## 4. Proposed Modal architecture

### 4.1 Components

```text
Recall API
  - campaign state
  - approval
  - Runway task orchestration
  - delivery/tracking

Modal Render Worker
  - downloads scene clips
  - downloads voiceover
  - runs ffmpeg
  - writes mp4/poster to storage
  - reports result
```

### 4.2 Data flow

```text
1. Campaign approved.
2. Backend starts Runway generation.
3. Runway tasks complete and output URLs are stored.
4. Backend submits stitch job to Modal.
5. Modal downloads clips + audio.
6. Modal runs ffmpeg concat/overlay.
7. Modal uploads final mp4/poster to storage.
8. Backend marks campaign `ready`.
```

### 4.3 What Modal should not do

Modal should not:

- classify players;
- generate scripts;
- own campaign state;
- own consent state;
- send Telegram messages;
- calculate ROI;
- become primary backend unless there is a strong reason.

Keep product logic in backend.

---

## 5. Modal MVP fallback code sketch

This is not required for day 1. Keep as reference.

```python
import modal

app = modal.App("recall-render")

image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg")
    .pip_install("httpx")
)

volume = modal.Volume.from_name("recall-assets", create_if_missing=True)

@app.function(
    image=image,
    volumes={"/mnt/assets": volume},
    timeout=600,
)
def stitch_campaign_video(campaign_id: str, clip_urls: list[str], voiceover_url: str) -> dict:
    import subprocess
    import pathlib
    import httpx

    workdir = pathlib.Path(f"/mnt/assets/{campaign_id}")
    workdir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    for idx, url in enumerate(clip_urls):
        path = workdir / f"clip_{idx}.mp4"
        path.write_bytes(httpx.get(url, timeout=120).content)
        clip_paths.append(path)

    voice_path = workdir / "voiceover.mp3"
    voice_path.write_bytes(httpx.get(voiceover_url, timeout=120).content)

    filelist = workdir / "filelist.txt"
    filelist.write_text("\n".join([f"file '{p}'" for p in clip_paths]))

    concat_path = workdir / "concat.mp4"
    final_path = workdir / "video.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(filelist),
        "-c", "copy",
        str(concat_path),
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(concat_path),
        "-i", str(voice_path),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        str(final_path),
    ], check=True)

    volume.commit()

    return {
        "campaign_id": campaign_id,
        "video_path": str(final_path),
        "status": "ready",
    }
```

### 5.1 Notes on this sketch

- It uses a Modal Volume for output.
- It assumes external URLs are downloadable.
- It omits poster extraction and subtitles.
- It does not include secrets because this worker only needs public output URLs.
- If outputs require auth, use Modal Secrets.

---

## 6. Modal operational decision tree

Use local/Railway ffmpeg if:

- final assets are fewer than 20 videos;
- mp4 files are small;
- backend host supports ffmpeg;
- no queue/concurrency problem.

Use Modal if:

- ffmpeg install fails;
- parallel batch is needed;
- backend host file system is unstable;
- you need worker isolation;
- render job time exceeds web request timeout.

Avoid Modal if:

- you are still building data models;
- Runway smoke test has not passed;
- UI is not ready;
- using Modal will delay hero path.

---

## 7. Deployment options for Recall

### 7.1 MVP default

```text
Backend: Railway/Render or local for screen recording
Dashboard: local or Vercel
Landing: Vercel
Storage: local/Railway volume/static assets
Worker: backend process
```

### 7.2 MVP fallback

```text
Backend: local + ngrok
Dashboard: local
Landing: Vercel or local
Storage: local static folder
Worker: local ffmpeg
```

### 7.3 Production-ish roadmap

```text
Backend API: Render/Fly/AWS/GCP
Worker: Modal
Storage: S3/R2/GCS
Queue: managed queue or DB-backed jobs
Dashboard: Vercel
Landing: Vercel
Observability: logs + error dashboards
Secrets: cloud secret manager
```

---

## 8. Modal risk register additions

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| Modal setup consumes MVP time | Medium | Medium | Keep Modal optional; local ffmpeg first |
| Volume/file path complexity | Medium | Medium | Use simple local storage in MVP |
| Secrets misconfigured | Low | High | Use `.env` locally, Modal Secrets only if Modal used |
| Cold start delays | Medium | Low | Not user-facing in MVP; use async status |
| Worker callback complexity | Medium | Medium | Backend polls job result or manual status update in MVP |
| Cost confusion | Low | Medium | Separate Runway credits from Modal compute in ROI docs |

---

## 9. PM/Delivery framing

Good interview wording:

> Modal was evaluated as a worker layer for scalable post-processing, but I deliberately kept it out of the MVP because Runway owns the heavy generation step and local ffmpeg was enough to prove the delivery spine. The production roadmap moves stitching and batch jobs into Modal when scale, concurrency or deployment isolation justify the added integration.

This shows:

- scope control;
- vendor evaluation;
- delivery realism;
- infrastructure pragmatism.

Bad wording:

> Modal was a hackathon partner, so I used it.

Do not use tools just because they are available.

---

## 10. Modal checklist if used

Before adding Modal:

- [ ] Local ffmpeg failed or is not deployable.
- [ ] Runway smoke test works.
- [ ] Campaign state model exists.
- [ ] Output URLs are downloadable.
- [ ] Worker task contract is defined.
- [ ] `modal` package installed.
- [ ] `modal setup` completed.
- [ ] Secret strategy decided.
- [ ] Volume/storage strategy decided.

Minimal worker contract:

```json
{
  "campaign_id": "cmp_001",
  "clip_urls": ["https://.../clip1.mp4"],
  "voiceover_url": "https://.../voiceover.mp3",
  "overlay_text": "Claim your gift",
  "output_format": "mp4"
}
```

Expected result:

```json
{
  "campaign_id": "cmp_001",
  "status": "ready|failed",
  "video_url": "https://...",
  "poster_url": "https://...",
  "error": null
}
```

---

## 11. Cost framing

Modal cost is separate from Runway media generation cost.

For Recall ROI model:

- Runway media generation dominates if every targeted user gets unique video.
- Modal compute is small for stitching, but nonzero at scale.
- In MVP, Modal is excluded from ROI.
- In production model, include worker/hosting overhead in `cost_per_targeted_user_usd`.

Potential cost categories:

```text
Runway credits
Worker compute
Object storage
CDN bandwidth
CRM/ESP delivery costs
CRM manager review time
Engineering maintenance
```

---

## 12. Sources

- Modal docs: https://modal.com/docs
- Modal pricing: https://modal.com/pricing
- Modal batch processing: https://modal.com/docs/guide/batch-processing
- Modal web endpoints: https://modal.com/docs/guide/webhooks
- Modal secrets: https://modal.com/docs/guide/secrets
- Modal volumes: https://modal.com/docs/guide/volumes
