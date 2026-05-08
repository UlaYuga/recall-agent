# Recall

AI CRM reactivation pipeline for personalized video postcards.

**Updated:** May 8, 2026  
**Hackathon window:** May 8-11, 2026

Recall is a hackathon PoC and portfolio case for an event-driven retention agent. It detects dormant users, prepares a human-approved campaign draft, generates motion-graphics video assets with Runway API, delivers through a Telegram PoC adapter, and tracks the path through a campaign landing page.

The project is built around one practical retention workflow: a CRM team has a base of inactive users, but generic email and push campaigns are weak. Recall turns that workflow into an agent-assisted pipeline. The system selects eligible users, explains why they belong to a cohort, drafts a personalized message, waits for manager approval, generates a short video postcard, sends it through an available delivery channel, and writes tracking events back into the metrics layer.

This is not positioned as a generic video generator. Runway is the media layer inside a larger CRM orchestration system.

## Project Goal

Recall is designed for two outcomes:

- **Runway API Hackathon submission:** a working AI media application that goes beyond a single API call.
- **Portfolio case:** a PM/Delivery case for an AI implementation in retention, CRM automation, approval workflows, and measurable ROI.

The public submission framing is generic: **AI Retention Agent for Consumer Subscription Products**. The deeper product case is written for international iGaming retention teams, with compliance-friendly messaging and no real operator brands, no real faces, and no manipulative claims.

## How It Works

1. Mock CRM events and player profiles are loaded into the backend.
2. The agent scans for dormant users.
3. A deterministic classifier assigns a cohort such as `high_value_dormant` or `warm_dormant`.
4. The script generator prepares message copy, CTA, offer framing, and Runway visual prompts.
5. A CRM manager reviews, edits, approves, or rejects the draft in the dashboard.
6. The video pipeline generates motion graphics and voiceover through Runway.
7. Delivery adapters send the approved asset through Telegram or create a preview through email.
8. The reactivation landing page tracks play, click, and mock conversion events.
9. The metrics page shows funnel and ROI simulation.

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

## Main Components

### Backend

FastAPI service for events, agent decisions, approval, video generation, delivery, tracking, and metrics. The backend owns the deterministic classifier, consent checks, delivery eligibility, and media-provider abstraction.

### Dashboard

CRM manager workspace for campaign approval. It is meant to show dormant users, cohort reasoning, generated scripts, render status, delivery status, and ROI metrics.

### Landing

Public/demo Next.js app for the Runway submission page, case study, and per-campaign reactivation pages at `/r/[campaign_id]`.

### Docs

Product and delivery source of truth: tech spec, architecture, PRD, delivery plan, risk register, ROI model, submission notes, and research packs.

## Quickstart

```bash
cp .env.example .env
make install-hooks
make dev
```

The scaffold intentionally starts with safe placeholders. Fill `.env` with real keys locally only.

## Key Environment Variables

- `RUNWAYML_API_SECRET`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `BASE_URL`
- `DATABASE_URL`

## Public Repository Safety

The repository is intended to be public for hackathon review and portfolio use. Real API keys must stay outside git:

- local development: `.env` only;
- CI/deployments: GitHub or hosting secrets;
- committed config: `.env.example` placeholders only.

Before pushing, run:

```bash
make public-check
```

See [Security](docs/SECURITY.md) for the full policy.

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

## License

This repository uses the MIT License.

In plain language: other people can use, copy, modify, and distribute the code, including commercially, as long as they keep the copyright and license notice. The code is provided without warranty.
