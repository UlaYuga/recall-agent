# Comeback Decisions Log

## Career goal

Project is optimized for portfolio transition from Senior Content Producer to PM/Delivery Manager in international iGaming.

Hackathon is used as deadline, Runway credits source and external proof point. Winning the hackathon is secondary.

## Product framing

Final product:
Comeback - AI CRM Reactivation Agent for International iGaming Operators.

Not Russia/CIS product.

Backend is geo-agnostic.
Delivery is market-specific.
Public case is international iGaming.
RU copy is only Russian-language explanation, not Russia/CIS go-to-market.

## MVP pipeline

Event bus -> dormant detection -> rule-based cohort classifier -> LLM script/visual prompt generation -> CRM approval gate -> Runway video generation -> Telegram delivery -> landing tracking -> ROI dashboard.

## Delivery channels

MVP:
- TelegramAdapter: real delivery via poster/video + inline button.
- EmailPosterAdapter: preview/stub only.
- LandingTrackingAdapter: real.
- CrmWritebackAdapter: mock local DB.

Production roadmap:
- WhatsAppBusinessAdapter.
- SmsLinkAdapter.
- PushInAppAdapter.
- CRM-native adapters: Optimove, Smartico, Fast Track, Customer.io, Braze.

Telegram is used because it is fast for PoC and supports direct media. It is not positioned as global default channel.

SMS is excluded from MVP because it cannot deliver video natively and adds provider/compliance overhead without improving core demo.

WhatsApp is excluded from MVP because it requires business verification, approved templates and opt-in setup.

## Data source assumption

Comeback does not collect contacts itself.

Production profile data comes from operator CRM/PAM/CDP/KYC/consent layer:
- player_id / external_crm_id
- email
- phone_e164
- push_token
- telegram_chat_id only after opt-in
- whatsapp opt-in only if already collected
- preferred language
- country / currency
- marketing consent
- event history

## Consent model

Generation consent:
- data_processing
- video_personalization

Delivery consent:
- marketing_communications
- channel-specific consent

If generation consent is missing, campaign is blocked before video pipeline.
If delivery consent is missing, video can be generated but delivery is blocked with ready_blocked_delivery.

## GEO and mock data

Use international mock players:
- Brazil
- Mexico
- South Africa
- Romania
- UK
- Spain
- Norway

Currencies:
- BRL
- MXN
- ZAR
- EUR
- GBP
- NOK

No RUB-first model.
No Russia/CIS go-to-market.
No +7-only mock phones.

## Agent logic

Classifier is rule-based/deterministic.

LLM is used only for:
- script generation
- tone
- CTA
- visual prompts

Reason: more reliable demo, easier to explain as PM/Delivery system, lower hallucination risk.

## Video strategy

Motion graphics video postcards only.
No realistic talking heads.
No real faces.
No real operator/provider logos.
No concrete game/provider brands.

MVP voiceover is English-only for reliability.
Player preferred_language / market_language stored for production roadmap.

Target output:
- 5-7 personalized video postcards.
- 1 full end-to-end hero campaign.

## ROI model

USD-first.

Hackathon free credits are excluded from ROI model.
Cost per targeted user represents production-scale media generation, hosting, CRM ops and delivery overhead.

Scenarios:
- Conservative: baseline 5%, uplift +20%, value_60d $40.
- Base: baseline 7%, uplift +30%, value_60d $58.
- Aggressive: baseline 10%, uplift +50%, value_60d $85.

## PM/Delivery artifacts

Repo must include:
- PRD.md
- DELIVERY_PLAN.md
- RISK_REGISTER.md
- ROI_MODEL.md
- ARCHITECTURE.md
- DEMO.md
- CASE_STUDY.md
- SUBMISSION.md

These documents are part of the portfolio case, not secondary docs.

## Scope discipline

Build what proves the delivery spine:
event -> agent -> approval -> video -> delivery -> landing -> tracking -> metrics.

Do not implement:
- WhatsApp
- SMS
- push/in-app
- real ESP
- real CRM vendor integration
- production auth
- payment gateway

Feature freeze:
Sunday May 10, 18:00 MSK.

Final video batch:
Sunday May 10, 20:00-22:00 MSK.

Monday:
backup renders, demo recording, README, submission only.
