# Repository Instructions

Prefer concrete code changes over abstract advice.

## Project Shape

- `backend/` is the FastAPI service and owns business logic, API contracts, persistence, delivery adapters, and media orchestration.
- `dashboard/` is the internal CRM manager interface for approval, script editing, render status, delivery status, and metrics.
- `landing/` is the public/demo surface for submission, case study, and per-campaign reactivation pages.
- `docs/` is the source of truth for product, delivery, research, risk, and submission context.

## Safety

- Do not commit real secrets. Use `.env.example` placeholders only.
- Do not commit generated videos or audio unless explicitly needed for final demo artifacts.
- Keep Runway prompts compliance-friendly: no real faces, no real brands, no guaranteed outcomes, no manipulative urgency.
- Keep the classifier deterministic. LLMs may generate script, CTA, tone, and visual prompts, but should not decide eligibility.

## Verification

- For backend changes, run tests from `backend/`.
- For UI changes, verify responsive layouts and Cyrillic text rendering where applicable.
- For media pipeline changes, verify generated file size stays Telegram Bot API friendly.

