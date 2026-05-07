# Recall

AI CRM reactivation pipeline for personalized video postcards.

Recall is a hackathon PoC and portfolio case for an event-driven retention agent. It detects dormant users, prepares a human-approved campaign draft, generates motion-graphics video assets with Runway API, delivers through a Telegram PoC adapter, and tracks the path through a campaign landing page.

## What It Demonstrates

- Dormant user detection from a mock CRM/event stream.
- Rule-based cohort classification with deterministic eligibility checks.
- LLM-assisted script, CTA, and visual prompt generation.
- CRM manager approval before any generated message is delivered.
- Runway API media layer for motion graphics scenes and TTS.
- Telegram delivery PoC plus email preview stub.
- Landing tracking and ROI simulation.

## Architecture

```text
event -> agent -> approval -> video -> delivery -> landing -> tracking -> metrics
```

Backend is geo-agnostic. Delivery is channel and market specific. Telegram is only the PoC adapter; WhatsApp, SMS, push, and CRM-native integrations are roadmap items.

## Repository Layout

```text
backend/      FastAPI API, agent logic, Runway wrapper, delivery adapters
dashboard/    CRM approval and metrics UI
landing/      Public/demo landing and campaign reactivation pages
docs/         Product, delivery, architecture, risk and research documents
assets/       Visual references, reference frames and generated demo video
```

## Quickstart

```bash
cp .env.example .env
make dev
```

The scaffold intentionally starts with safe placeholders. Fill `.env` with real keys locally only.

## Key Environment Variables

- `RUNWAY_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `BASE_URL`
- `DATABASE_URL`

## Docs

- [Tech Spec](docs/TECH_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Demo Plan](docs/DEMO.md)
- [Submission Notes](docs/SUBMISSION.md)
- [PRD](docs/PRD.md)
- [Delivery Plan](docs/DELIVERY_PLAN.md)
- [Risk Register](docs/RISK_REGISTER.md)
- [ROI Model](docs/ROI_MODEL.md)
- [Vendor Integration Plan](docs/VENDOR_INTEGRATION_PLAN.md)

## Status

Initial repository scaffold. Implementation priority is:

1. Data model and seed data.
2. Agent scan and cohort classifier.
3. Approval API and dashboard.
4. Runway smoke test and video pipeline.
5. Telegram delivery.
6. Landing tracking and metrics.

