# Architecture

```text
CRM events
  -> FastAPI ingestion
  -> SQLite mock event bus
  -> deterministic cohort classifier
  -> LLM script / CTA / visual prompt generator
  -> CRM manager approval
  -> Runway media generation
  -> ffmpeg stitching
  -> delivery adapter
  -> landing page
  -> tracking events
  -> metrics and ROI dashboard
```

## Principles

- Classifier is deterministic; LLM does not decide eligibility.
- Human approval is mandatory before delivery.
- Runway integration is isolated behind `VideoProviderProtocol`.
- Delivery adapters are replaceable.
- All secrets stay in `.env`; only placeholders are committed.

