# Tech Spec: Recall - AI CRM Reactivation Agent

Спека на 3 дня хакатона 8-11 мая 2026. Submission 11.05 16:00 МСК. Соло-проект, 50K credits Runway лимит.

## Ключевые технические факты, которые формируют архитектуру

1. **Gen-4.5 генерит клипы по 5 или 10 секунд за раз.** Для постера 30-45 сек собираем видео из 3-5 клипов через ffmpeg + накладываем voiceover отдельно.
2. **В Runway API уже встроен ElevenLabs** через эндпоинты `/v1/text_to_speech` и `/v1/voices` (модель `eleven_multilingual_v2`). Отдельный ElevenLabs API key не нужен. TTS = 1 credit per 50 chars.
3. **Telegram sendVideo cap 50MB** через cloud Bot API. Для 720p 45 сек H.264 ~10-15MB - укладываемся без локального сервера.
4. **Runway compliance review** может зафлажить gambling-контент - отсюда EN-версия лендинга для submission.
5. **Backend geo-agnostic.** Delivery market-specific. MVP реализует Telegram real delivery + email preview. SMS/WhatsApp/push - production roadmap.

---

## 1. Промпт для Codex - инициализация репо

Скармливается Codex первым месседжем, он сам создает репу и заливает.

```
Создай GitHub-репозиторий recall-agent (private), инициализируй структуру:

recall-agent/
├── README.md                          # описание проекта, quickstart
├── .env.example                       # все ключи (RUNWAYML_API_SECRET, TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, BASE_URL)
├── .gitignore                         # python, node, .env, *.mp4, *.wav, .venv
├── docker-compose.yml                 # backend + dashboard + landing локально
├── Makefile                           # make dev, make seed, make demo
│
├── backend/
│   ├── pyproject.toml                 # poetry или uv, python 3.11+
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── config.py                  # pydantic-settings, env vars
│   │   ├── db.py                      # SQLite + SQLModel
│   │   ├── models.py                  # Player, Event, Campaign, VideoAsset, Delivery, Tracking
│   │   ├── api/
│   │   │   ├── events.py              # /events ingestion
│   │   │   ├── agent.py               # /agent/decide, /agent/script
│   │   │   ├── approval.py            # /approval/*
│   │   │   ├── video.py               # /video/generate, /video/status
│   │   │   ├── delivery.py            # /delivery/send
│   │   │   └── tracking.py            # /track/* webhook
│   │   ├── agent/
│   │   │   ├── classifier.py          # rule-based/deterministic cohort classifier
│   │   │   ├── script_generator.py    # LLM script generation
│   │   │   ├── prompts.py             # все system/user prompts
│   │   │   └── offers.py              # offer rules engine
│   │   ├── runway/
│   │   │   ├── client.py              # обертка над Runway Python SDK с интерфейсом VideoProviderProtocol
│   │   │   ├── video_pipeline.py      # склейка клипов + voiceover через ffmpeg
│   │   │   └── tts.py                 # text_to_speech через Runway
│   │   ├── delivery/
│   │   │   ├── adapters.py            # DeliveryAdapter Protocol
│   │   │   ├── eligibility.py         # get_available_channels, can_send_channel, select_best_channel, block_reason
│   │   │   ├── telegram_adapter.py    # TelegramAdapter - real
│   │   │   ├── email_adapter.py       # EmailPosterAdapter - stub/mock
│   │   │   ├── landing_adapter.py     # LandingTrackingAdapter - real
│   │   │   └── crm_writeback.py       # CrmWritebackAdapter - mock write-back в local DB
│   │   ├── telegram/
│   │   │   └── bot.py                 # aiogram
│   │   └── workers/
│   │       └── scheduler.py           # APScheduler, polling event bus
│   ├── seeds/
│   │   ├── players.json               # 7 mock players (international)
│   │   ├── events.json                # mock event stream
│   │   ├── sim_config.json            # mock metrics simulation
│   │   └── seed.py                    # загрузка в SQLite
│   └── tests/
│       └── test_pipeline.py
│
├── dashboard/
│   ├── package.json                   # Next.js 14 + shadcn/ui
│   ├── app/
│   │   ├── page.tsx                   # approval queue
│   │   ├── campaign/[id]/page.tsx     # детали кампании, edit script
│   │   └── metrics/page.tsx           # uplift dashboard
│   └── components/
│       ├── ApprovalCard.tsx
│       ├── ScriptEditor.tsx
│       └── VideoPreview.tsx
│
├── landing/
│   ├── package.json                   # Next.js + Tailwind (один app, не две сборки)
│   ├── app/
│   │   ├── page.tsx                   # hero + concept + demo_video + how_it_works + cta
│   │   ├── case/page.tsx              # case study со скринами и метриками
│   │   └── r/[campaign_id]/page.tsx   # reactivation landing для конкретного игрока
│   ├── content/
│   │   ├── en.ts                      # EN copy (primary: international iGaming; optional generic subscription mode)
│   │   └── ru.ts                      # RU copy (международный iGaming-кейс на русском)
│   └── lib/
│       └── tracking.ts                # postMessage в backend tracking webhook
│
├── docs/
│   ├── ARCHITECTURE.md                # схема, dataflow
│   ├── DEMO.md                        # как запустить demo за 3 минуты
│   ├── SUBMISSION.md                  # текст для Runway submission
│   ├── PRD.md                         # product requirements
│   ├── DELIVERY_PLAN.md               # delivery scope и roadmap
│   ├── RISK_REGISTER.md               # риски и митигации
│   ├── ROI_MODEL.md                   # формула и сценарии ROI (USD-first)
│   └── CASE_STUDY.md                  # цифры симуляции с источниками
│
└── assets/
    ├── visual_style/                  # референсы для Gen-4.5
    ├── reference_frames/              # стартовые кадры image-to-video
    └── demo_video/                    # финальное submission video

Запушь начальный коммит "scaffold". Все секреты только в .env.example как заглушки.
```

---

## 2. Стек по компонентам

| Слой | Библиотека | Версия | Зачем |
|---|---|---|---|
| Backend framework | FastAPI | 0.115+ | async, OpenAPI auto, webhooks |
| ASGI server | uvicorn[standard] | 0.32+ | dev + prod |
| ORM | SQLModel | 0.0.22 | pydantic + SQLAlchemy в одном |
| DB | SQLite | builtin | mock event bus |
| Settings | pydantic-settings | 2.6+ | env management |
| Runway SDK | runwayml | latest (>=3.0) | официальный Python SDK |
| LLM | anthropic | 0.40+ | Claude Sonnet 4.5 для агента |
| HTTP client | httpx | 0.27+ | async, для Telegram |
| Telegram | aiogram | 3.13+ | async, удобнее python-telegram-bot |
| Video processing | ffmpeg-python | 0.2.0 + системный ffmpeg | склейка клипов + audio mix |
| Scheduler | apscheduler | 3.10+ | cron-like для event polling |
| Dashboard | Next.js | 14.2+ (app router) | shadcn ready |
| UI | shadcn/ui + Tailwind | latest | минимум время на стиль |
| State | TanStack Query | 5.59+ | fetch backend |
| Landing | Next.js | 14.2+ | static export, Vercel deploy |
| Charts (dashboard) | Recharts | 2.13+ | uplift графики |
| Hosting backend | Railway или Render | - | один-клик deploy |
| Hosting landing | Vercel | - | бесплатно |
| File storage | локально + публичный CDN | - | для demo хватает Railway volumes |

LLM выбор: **Claude Sonnet 4.5** для агента. Если Anthropic key недоступен - fallback на gpt-4o-mini.

`backend/app/runway/client.py` делается под интерфейс `VideoProviderProtocol`, чтобы swap на Veo/Kling/Luma/Pika занял час, а не неделю.

---

## 3. API endpoints (FastAPI)

### 3.1 Event ingestion
```
POST   /events/ingest               # принимает событие из mock event bus
GET    /events?player_id=...        # история событий игрока
POST   /events/simulate             # demo trigger: создать dormant игрока вручную
```

### 3.2 Agent decision pipeline
```
POST   /agent/scan                  # запустить scan базы, найти dormant
POST   /agent/classify              # {player_id} -> cohort + risk score
POST   /agent/generate-script       # {player_id, cohort} -> {script, offer, tone}
GET    /agent/campaigns?status=...  # campaigns в статусах pending/approved/rejected/sent/tracked
```

### 3.3 Approval gate
```
GET    /approval/queue              # все pending approval
GET    /approval/{campaign_id}      # детали + script + offer + player profile
PATCH  /approval/{campaign_id}      # body: {action: approve|reject|edit, script?, offer?, comment?}
POST   /approval/{campaign_id}/approve  # shortcut
POST   /approval/{campaign_id}/reject   # с обязательным reason
```

### 3.4 Video generation

```
POST   /video/generate              # {campaign_id} -> запускает Runway pipeline, возвращает task_id
GET    /video/status/{task_id}      # polling статуса (queued|generating|stitching|ready|failed)
GET    /video/{campaign_id}/preview # mp4 + poster jpg
```

Внутри `/video/generate` оркестрация:
1. Распилить script на 3-5 сцен по 5-10 сек
2. Параллельно дернуть Runway `image_to_video` (model=`gen4.5`, duration=10) на каждую сцену со стартовым кадром из `/assets/reference_frames/`
3. Дернуть Runway `text_to_speech` для voiceover (eleven_multilingual_v2, English для MVP)
4. После всех task complete - ffmpeg-python:
   - concat clips через filelist
   - наложить voiceover как audio track с дакингом
   - добавить нижнюю плашку с offer (drawtext или ass-subtitle)
   - poster jpg = первый кадр intro
5. Сохранить mp4 + jpg в `/storage/{campaign_id}/`, обновить запись в DB до status=`ready`

Статусы pipeline для UI: `queued → generating_frames → generating_voice → stitching → ready`. Возвращает progress 0-100.

**MVP generates demo voiceovers in English for reliability.** Player `preferred_language` is stored and used in script metadata; full multilingual voiceover generation is a production roadmap item.

### 3.5 Distribution

```
POST   /delivery/send                # {campaign_id, channels, fallback_to_available}
POST   /delivery/telegram            # internal: отправка через aiogram
POST   /delivery/email               # internal: stub/preview
GET    /delivery/{campaign_id}       # per-channel delivery status
```

Request body:
```json
{
  "campaign_id": "cmp_001",
  "channels": ["telegram", "email"],
  "fallback_to_available": true
}
```

Response:
```json
{
  "campaign_id": "cmp_001",
  "overall_status": "sent|partial|blocked|failed",
  "channels": {
    "telegram": {"status": "sent", "message_id": "123"},
    "email": {"status": "prepared"},
    "sms": {"status": "skipped", "reason": "no_sms_consent"}
  }
}
```

Поведение:
- Перед отправкой - eligibility check через `delivery/eligibility.py`
- если requested channel недоступен → записать channel-level `skipped` reason
- если `fallback_to_available=true` → выбрать следующий доступный канал
- если нет доступных каналов → campaign status `blocked_no_reachable_channel`

**MVP delivery:**
- `TelegramAdapter` - real (sendPhoto poster + inline button, optional sendVideo)
- `EmailPosterAdapter` - stub: dashboard показывает email preview (subject + poster + CTA + landing URL), статус `email_prepared`, кнопка "Mark as sent"
- `LandingTrackingAdapter` - real tracking
- `CrmWritebackAdapter` - mock write-back в local DB

**Production roadmap adapters (не реализуем в MVP):**
- `WhatsAppBusinessAdapter` - requires business verification, approved templates, opt-in
- `SmsLinkAdapter` - SMS is a fallback link channel for markets where mobile messaging is strong, excluded from MVP because it cannot deliver video natively and adds provider/compliance overhead without improving core demo
- `PushInAppAdapter`
- `OptimoveAdapter`, `SmarticoAdapter`, `FastTrackAdapter`, `CustomerIoAdapter`, `BrazeAdapter`

**Telegram как PoC adapter, не global default channel.** В production delivery обрабатывается через market-specific adapters в зависимости от оператора и player consent.

### 3.6 Tracking webhook

```
POST   /track/play                   # {campaign_id, player_id, watched_seconds}
POST   /track/click                  # {campaign_id, player_id, link_id}
POST   /track/deposit                # {campaign_id, player_id, amount, currency}
GET    /track/{campaign_id}          # агрегированные метрики по кампании
GET    /metrics/dashboard            # global: total_sent, plays, ctr, deposit_uplift, roi_estimate_usd
```

---

## 4. Структура промптов агента

Один общий system prompt + три tool-схемы. Используем **Claude Sonnet 4.5** через structured tool use.

### 4.1 System prompt агента

```
You are a CRM Reactivation Agent for an online subscription/deposit-based service.
Your task: for a given dormant player, identify the cohort, assess churn risk,
generate a personalized reactivation script and offer.

Principles:
- Warm tone, like a familiar account manager, not aggressive sales
- Script 30-45 seconds voiceover = 70-110 words in player's preferred language
- Use player's name, last favorite activity, last notable win or milestone
- Offer must be proportional to risk score and LTV tier
- Final CTA must be single and unambiguous

Prohibited:
- Using urgency more than once in the script
- Guaranteeing wins or money-back
- Words: "guaranteed", "you will definitely win", "don't miss your chance"
```

### 4.2 Tool: classify_cohort

**Classifier is rule-based/deterministic.** LLM не классифицирует cohort. Classifier применяет decision tree по полям профиля и event-истории: days_since_last_deposit, total_deposits_count, ltv_segment, last_event_type.

LLM получает на вход уже готовый cohort + risk_score от classifier и только генерит script, tone, CTA и visual prompts.

Input classifier: player profile + last 30 events.
Output schema:
```json
{
  "cohort": "casual_dormant|high_value_dormant|post_event|first_deposit_no_return|vip_at_risk|lapsed_loyal",
  "risk_score": 0,
  "ltv_tier": "low|mid|high|vip",
  "reasoning": "2-3 sentences why this cohort",
  "recommended_offer_band": "free_spins_small|free_spins_mid|deposit_match_low|deposit_match_high|cashback|personal_manager_call"
}
```

### 4.3 Tool: generate_script

Input: player profile + cohort + selected_offer.
Output schema:
```json
{
  "scenes": [
    {"id": 1, "type": "intro", "text": "...", "visual_brief": "..."},
    {"id": 2, "type": "personalized_hook", "text": "...", "visual_brief": "..."},
    {"id": 3, "type": "offer", "text": "...", "visual_brief": "..."},
    {"id": 4, "type": "cta", "text": "...", "visual_brief": "..."}
  ],
  "full_voiceover_text": "full text for TTS, 70-110 words",
  "estimated_duration_sec": 38,
  "tone": "warm|friendly_excited|premium_calm",
  "cta_text": "single CTA for video overlay and landing"
}
```

`visual_brief` - короткое описание кадра для Gen-4 Image на английском. Например: "abstract slot machine reels with golden coins falling, cinematic motion, brand palette deep purple and gold, no text".

### 4.4 Mini-prompts для каждой сцены

В `backend/app/agent/prompts.py` лежит словарь шаблонов:
```python
SCENE_PROMPTS = {
  "intro": "abstract slot reels spinning, bokeh lights, deep purple gradient, cinematic, smooth motion, no text, no logos",
  "personalized_hook": "warm spotlight on a single playing card or slot symbol related to {favorite_game_visual_hint}, motion blur, dreamy",
  "offer": "shimmering golden particles forming abstract gift box shape, brand purple background, anticipation",
  "cta": "soft pulsing button glow, deep purple to magenta gradient, minimal motion, looping"
}
```

LLM подставляет переменные. Никаких лиц, логотипов, конкретных провайдеров - чтобы Runway moderation не флажила.

---

## 5. Schema mock event bus

### 5.1 Player profile

Mock players - международные. Страны: Brazil, Mexico, South Africa, Romania, UK, Spain, Norway. Валюты: BRL, MXN, ZAR, EUR, GBP, NOK. Никакого RUB-first, никаких +7-only номеров.

```json
{
  "player_id": "p_001",
  "external_id": "demo_op_4471",
  "first_name": "Lucas",
  "preferred_language": "en",
  "market_language": "pt-BR",
  "country": "BR",
  "registered_at": "2025-08-12T14:23:00Z",
  "last_login_at": "2026-04-08T19:11:00Z",
  "last_deposit_at": "2026-04-05T20:44:00Z",
  "total_deposits_count": 14,
  "total_deposits_amount": 7100,
  "currency": "BRL",
  "favorite_vertical": "casino",
  "favorite_game_category": "slots",
  "favorite_game_label": "fruit_slots",
  "biggest_win": {"amount": 3100, "currency": "BRL", "at": "2026-03-22T00:00:00Z"},
  "ltv_segment": "mid",
  "tags": ["weekly_player", "bonus_hunter", "telegram_subscribed"],
  "identifiers": {
    "player_id": "p_001",
    "external_crm_id": "crm_9f2a",
    "email": "lucas.demo@example.com",
    "phone_e164": "+5511999990000",
    "telegram_chat_id": "123456789",
    "push_token": "mock_push_token_001"
  },
  "consent": {
    "marketing_communications": true,
    "marketing_email": true,
    "marketing_sms": false,
    "whatsapp_business": true,
    "push_notifications": true,
    "video_personalization": true,
    "data_processing": true
  },
  "preferred_channels": ["telegram", "email", "whatsapp", "push"]
}
```

### 5.2 Event

```json
{
  "event_id": "ev_8c4...",
  "player_id": "p_001",
  "event_type": "login|deposit|withdrawal|bet_placed|session_end|bonus_claimed|support_contact|logout|page_view",
  "timestamp": "2026-04-08T19:11:00Z",
  "payload": {
    "amount": 50,
    "currency": "USD",
    "game_id": "...",
    "session_duration_sec": 1840
  },
  "source": "mock_event_bus_v1"
}
```

### 5.3 Campaign

```json
{
  "campaign_id": "cmp_...",
  "player_id": "p_001",
  "created_at": "...",
  "status": "pending|approved|rejected|generating|ready|sent|watched|converted",
  "cohort": "high_value_dormant",
  "risk_score": 78,
  "script": {},
  "offer": {
    "type": "free_spins",
    "value": 30,
    "game_label": "fruit_slots",
    "valid_until": "2026-05-18T00:00:00Z"
  },
  "video_asset": {
    "video_url": "/storage/cmp_.../video.mp4",
    "poster_url": "/storage/cmp_.../poster.jpg",
    "duration_sec": 38,
    "size_bytes": 11200000
  },
  "approver": {
    "user_id": "demo_crm_manager",
    "decided_at": "...",
    "comment": "Smaller offer, please"
  },
  "delivery": {
    "telegram": {"status": "sent", "sent_at": "...", "message_id": "..."},
    "email": {"status": "prepared", "sent_at": null}
  },
  "tracking": {
    "video_played_at": "...",
    "watched_seconds": 32,
    "cta_clicked_at": "...",
    "deposit_at": "...",
    "deposit_amount_usd": 75
  }
}
```

---

## 6. Delivery adapter architecture

### 6.1 DeliveryAdapter Protocol

```python
class DeliveryAdapter(Protocol):
    def can_send(self, player: Player, campaign: Campaign) -> bool: ...
    async def send(self, player: Player, campaign: Campaign, asset: VideoAsset) -> DeliveryResult: ...
    async def get_status(self, campaign_id: str) -> DeliveryStatus: ...
```

### 6.2 Channel Eligibility Service

`backend/app/delivery/eligibility.py`

Функции:
- `get_available_channels(player)` - возвращает список доступных каналов на основе consent + identifiers
- `can_send_channel(player, channel)` - bool, проверяет конкретный канал
- `select_best_channel(player, campaign)` - выбирает оптимальный по preferred_channels + availability
- `block_reason(player, channel)` - возвращает причину блока если канал недоступен

Два уровня consent gate:

**Generation consent** (проверяется до запуска video pipeline):
- `data_processing: true` + `video_personalization: true`
- если отсутствует → campaign не создается, статус `blocked_generation_consent`

**Delivery consent** (проверяется перед отправкой):
- `marketing_communications: true` + channel-specific consent
- если delivery consent отсутствует → campaign может быть сгенерена, статус `ready_blocked_delivery`
- это позволяет CRM-менеджеру видеть готовое видео и решить что делать с кейсом

Разделение важно для демо: mock-игрок без channel consent не заблочит video flow, а покажет корректное пограничное состояние в dashboard.

Блокировки delivery:
- нет `marketing_communications` → `blocked_no_consent`
- нет channel opt-in → channel unavailable, fallback на следующий
- нет ни одного доступного канала → `blocked_no_reachable_channel`

### 6.3 MVP implementations

| Адаптер | Тип | Поведение |
|---|---|---|
| `TelegramAdapter` | real | sendPhoto poster + inline button "Watch video" → landing; optional sendVideo если < 50MB |
| `EmailPosterAdapter` | stub | dashboard preview: subject + poster + CTA + landing URL; статус `email_prepared`; кнопка "Mark as sent" |
| `LandingTrackingAdapter` | real | tracking events на landing |
| `CrmWritebackAdapter` | mock | write-back статусов в local SQLite DB |

### 6.4 Production roadmap adapters

```python
# production roadmap - не реализуем в MVP
WhatsAppBusinessAdapter   # checks phone_e164 + whatsapp_business consent + approved template
SmsLinkAdapter            # fallback link channel, no video delivery
PushInAppAdapter          # requires push_token
OptimoveAdapter
SmarticoAdapter
FastTrackAdapter
CustomerIoAdapter
BrazeAdapter
```

---

## 7. Schema approval dashboard

Dashboard - Next.js + shadcn. Три экрана.

### 7.1 Approval queue (главный)

Таблица + фильтры. Колонки: `Player | Cohort badge | Risk | LTV | Created | Preview button | Action buttons`. Фильтры по cohort, risk_score, status.

Клик на preview - открывается **side panel** с:
- профиль игрока (имя, страна, последний депозит, любимая игра, biggest win, всего депозитов)
- блок Cohort + risk_score + reasoning (что сказал агент)
- блок Offer с возможностью inline edit value
- блок Script - 4 карточки сцен, каждую можно редактировать textarea
- кнопки **Approve as is** / **Approve with edits** / **Regenerate script** / **Reject** (с обязательным reason из dropdown: too_aggressive | wrong_offer | wrong_tone | data_issue | other)

### 7.2 Campaign detail (после approve)

Видео-плеер + все метаданные. Статусы pipeline. После ready - кнопка **Send to Telegram + Email**.

### 7.3 Metrics dashboard

Подробнее в секции 9.

### 7.4 Аутентификация

Для PoC - один зашитый user в `.env` (`DEMO_MANAGER_PASSWORD`). HTTP basic auth на dashboard. Никакого JWT/OAuth.

---

## 8. Telegram bot workflow

Library: **aiogram 3.13**. Конкретные методы:

**MVP: long polling (не webhook)**

Для MVP используем `executor.start_polling` / `dp.start_polling()`. Webhook требует публичный URL, secret, Railway deploy и debugging цикл - для хакатонного демо это лишний overhead без демо-ценности. Webhook вынесен в production roadmap.

```python
# MVP: polling
await dp.start_polling(bot)

# Production roadmap: webhook
# await bot.set_webhook(url=f"{BASE_URL}/telegram/webhook", secret_token=WEBHOOK_SECRET)
```

**Setup один раз:**
- `setMyCommands`: `/start`, `/optin`, `/optout`, `/help`

**Onboarding mock-игрока (для demo):**
- Игрок пишет `/start` боту, бот сохраняет `chat_id` в DB по совпадению telegram_username с player.telegram_username (или просит ввести reactivation code из лендинга)

**Доставка кампании:**
1. `sendPhoto(poster)` + InlineKeyboardButton "Watch video" → `{LANDING_URL}/r/{campaign_id}`
2. Optional: `sendVideo(chat_id, video=open(mp4_path), caption=offer_text, supports_streaming=True, parse_mode="HTML")` + тот же inline button
3. Если файл > 50MB - fallback: sendMessage с ссылкой на mp4 на Railway volume. Для 720p 30-45 сек это не наш кейс.

**Tracking play:**
Telegram не дает notify о просмотре mp4 в боте. "play" трекаем только на лендинге. Telegram-метрики: delivered + clicked.

**Гибрид-подход (рекомендую):** первый месседж - `sendPhoto` poster + кнопка "Watch" → лендинг (где работает аналитика). Второй месседж сразу под ним - `sendVideo` для тех кто смотрит прямо в Telegram.

---

## 9. Лендинг кейса - архитектура

Один Next.js app, два content-файла. Деплой на Vercel.

**EN copy** (`content/en.ts`) - primary public case: International iGaming CRM Reactivation Pipeline. Optional Runway-safe mode: generic subscription framing (used if submission requires removing iGaming context).

**RU copy** (`content/ru.ts`) - русскоязычное объяснение международного iGaming-кейса. Не позиционирование под Россию/СНГ как primary market.

Язык выбирается через query param `?lang=ru` или через Next.js i18n routing. Одна сборка, один деплой.

### 9.1 Структура страниц

```
/                         - hero + concept + demo_video + how_it_works + tech_stack + cta
/case                     - подробный case study со скринами dashboard и метриками
/r/[campaign_id]          - reactivation landing для конкретного игрока (видео + offer + mock deposit form)
/api/track                - proxy на backend tracking webhook
```

**Reactivation landing `/r/[campaign_id]`:**
- 720p видео-плеер с poster, autoplay muted
- под видео - заголовок offer
- mock CTA-кнопка **Claim my gift** (EN) / **Забрать подарок** (RU). По клику - модалка с формой, на submit - запрос на `/track/deposit`, потом thank you screen.

### 9.2 Что трекать

Каждое событие летит на `/api/track/{event}`:
- `landing_loaded`
- `video_play`
- `video_25/50/75/95_percent`
- `cta_click`
- `deposit_submit`
- `bounce` (beforeunload без play)

Используем fetch keepalive чтобы события не терялись на bounce.

---

## 10. Mock metrics и ROI model

### 10.1 ROI model (USD-first)

Primary currency: USD. Dashboard нормализует все ROI в USD. RUB не используется в primary model.

**Конфиг симуляции** (`backend/seeds/sim_config.json`):
```json
{
  "scenarios": {
    "conservative": {
      "baseline_reactivation_rate": 0.05,
      "ai_video_uplift_relative": 0.20,
      "value_60d_per_reactivated_user_usd": 40,
      "cost_per_targeted_user_usd": 0.25
    },
    "base": {
      "baseline_reactivation_rate": 0.07,
      "ai_video_uplift_relative": 0.30,
      "value_60d_per_reactivated_user_usd": 58,
      "cost_per_targeted_user_usd": 0.25
    },
    "aggressive": {
      "baseline_reactivation_rate": 0.10,
      "ai_video_uplift_relative": 0.50,
      "value_60d_per_reactivated_user_usd": 85,
      "cost_per_targeted_user_usd": 0.25
    }
  },
  "cohort_breakdown": {
    "high_value_dormant": {"size": 1240, "uplift": 0.40},
    "casual_dormant": {"size": 8400, "uplift": 0.25},
    "post_event": {"size": 3100, "uplift": 0.30},
    "first_deposit_no_return": {"size": 2200, "uplift": 0.20}
  }
}
```

`cost_per_targeted_user_usd` represents estimated production-scale cost including media generation, hosting, CRM ops and delivery overhead. **Hackathon free credits are excluded from ROI calculation** - модель строится на production economics, а не на бесплатных кредитах хакатона.

**ROI formula:**
```
incremental_reactivated = targeted_users * baseline_reactivation_rate * relative_uplift
incremental_revenue = incremental_reactivated * value_60d_per_reactivated_user_usd
campaign_cost = targeted_users * cost_per_targeted_user_usd
net_lift = incremental_revenue - campaign_cost
roi = net_lift / campaign_cost
```

Источники цифр:
- baseline 7% реактивации - Engagehut benchmarks
- uplift 30% - консервативно по сравнению с 100%+ из Idomoo/Entain case
- 60-day LTV $58 - iGaming international mid-tier benchmark
- Источники указаны явно в UI: badge **"Simulation based on industry benchmarks"** + tooltip

### 10.2 Dashboard metrics

1. **Big numbers row:** Total players analyzed, Campaigns created, Approval rate %, Videos delivered, Average CTR, Reactivation rate (mock), Estimated 60-day net revenue lift (USD)
2. **Funnel chart:** Targeted -> Sent -> Played -> Clicked -> Converted
3. **Cohort table:** breakdown по cohort с baseline vs uplifted numbers
4. **ROI calculator (interactive):** слайдеры baseline rate, uplift, cohort size, scenario selector -> live пересчет ROI и payback period в USD
5. **Time series (mock):** "Last 30 days" - график plays/conversions по дням
6. **Recent campaigns list:** последние 10 одобренных кампаний с финальным статусом

---

## 11. PM Artifacts - синхронизация с docs/

### docs/PRD.md
- Target user: international iGaming operator CRM manager
- No RUB/Russia primary market assumptions
- Channel adapter / consent layer в scope

### docs/DELIVERY_PLAN.md
- MVP: Telegram real delivery + Email preview stub
- WhatsApp/SMS/push - production roadmap, не MVP scope

### docs/RISK_REGISTER.md
- Risk: "wrong market/channel assumptions in demo" - mitigation: market-specific DeliveryAdapter roadmap, Telegram positioned as PoC-only adapter, not global default
- Risk: Runway moderation - mitigation: EN generic framing for submission, no gambling slang in visual briefs

### docs/ROI_MODEL.md
- USD-first, three scenarios (conservative/base/aggressive)
- No Russia primary benchmark
- Formula: incremental_reactivated * value_60d_usd - campaign_cost

---

## 12. Schedule на 3 дня (МСК)

Закладываются двойные буферы на rendering queue Runway и debugging async pipeline. Работа в Cursor + Codex параллельно.

### Пятница 8 мая

| Время МСК | Что делаем |
|---|---|
| 16:00-17:00 | Kickoff Runway live. Showcase + tech walkthrough |
| 17:00-17:30 | API key, регистрация, проверка credit balance |
| 17:30-19:00 | Codex заводит репу по промпту из секции 1, scaffold-коммит |
| 19:00-21:00 | Mock players (7 профилей, international), seed events, SQLite init. Базовая FastAPI |
| 21:00-22:00 | Тест Runway API: gen4_image + gen4.5 image-to-video 5 сек + text_to_speech. Зафиксировать рабочие параметры |
| 22:00-00:00 | Buffer + сон |

### Суббота 9 мая

| Время МСК | Что делаем |
|---|---|
| 09:00-12:00 | Agent pipeline: classifier + script_generator с Anthropic SDK + tool use. Тест на 3 моках |
| 12:00-13:00 | Перерыв + обед |
| 13:00-16:00 | Approval API + минимальный Next.js dashboard: queue + side panel preview/edit |
| 16:00-19:00 | **Самый рисковый блок:** video pipeline. Параллельные Runway tasks, polling, ffmpeg склейка + voiceover overlay, poster generation. End-to-end на одном моке |
| 19:00-20:00 | Buffer на debug. Discord помощь от Runway eng |
| 20:00-22:00 | Telegram bot scaffold: long polling, /start, sendPhoto + optional sendVideo with inline button. Тест на личном tg |
| 22:00-00:00 | Закрытие дня, коммит |

### Воскресенье 10 мая

| Время МСК | Что делаем |
|---|---|
| 09:00-12:00 | Tracking webhook + landing scaffold (Next.js, RU/EN, общий бэк). Reactivation page `/r/[campaign_id]` |
| 12:00-13:00 | Перерыв |
| 13:00-15:00 | Metrics dashboard в Next.js: big numbers, funnel, cohort table, ROI calculator (USD) |
| 15:00-18:00 | **End-to-end прогон:** trigger -> classify -> script -> approve -> generate -> deliver -> track. На 3 mock-игроках, фиксим bugs |
| 18:00-20:00 | Полировка dashboard и landing. Копирайт RU и EN. Vercel deploy лендинга. Railway deploy backend |
| 20:00-22:00 | **Финальный batch видео для 5-7 mock-игроков.** Параллельный рендер через Runway. Лучше сделать сейчас - в понедельник очередь Runway может быть загружена другими участниками |
| 22:00-00:00 | Сон |

### Понедельник 11 мая

| Время МСК | Что делаем |
|---|---|
| 08:00-10:00 | Только backup renders и замена проблемных видео. Если все видео готовы в воскресенье - используем время на polish README и чеклист |
| 10:00-13:00 | **Demo video 2 минуты для submission.** Сценарий + screen recording + voiceover. Структура: проблема (15с) -> trigger event (15с) -> agent decision (20с) -> approval gate (15с) -> video generation (15с) -> telegram delivery (15с) -> лендинг с видео (15с) -> metrics dashboard (10с) |
| 13:00-14:00 | Submission text для Runway (EN-версия) |
| 14:00-15:00 | README + ARCHITECTURE.md + DEMO.md |
| 15:00-15:30 | RU-лендинг финальная вычитка |
| 15:30-15:55 | Отправка submission на Runway форму. Скриншот для бэкапа |
| 15:55 | Закрыть ноут |
| 16:00 | **DEADLINE** |

---

## 13. Чеклист к 16:00 МСК 11 мая

### Submission - обязательное

- [ ] GitHub репо публичный, README с quickstart
- [ ] Demo video 1.5-2 мин загружено (YouTube unlisted или Vimeo) и ссылка в submission
- [ ] Submission form Runway заполнена: project name, description, demo video URL, github URL
- [ ] Backend задеплоен и доступен по публичному URL (Railway/Render)
- [ ] Минимум один лендинг (EN-версия для submission) задеплоен на Vercel
- [ ] `.env.example` есть, реальные секреты не закоммичены

### Working demo - end-to-end

- [ ] `/agent/scan` находит dormant игроков из mock event bus
- [ ] Rule-based classifier возвращает cohort + risk_score для всех 7 mock-игроков; LLM генерит script/visual prompts
- [ ] Generation consent blocks only players without data_processing/video_personalization. Delivery consent can block sending after video is ready with status ready_blocked_delivery.
- [ ] Approval dashboard открывается, показывает queue, дает approve/reject/edit
- [ ] При approve запускается Runway video pipeline и генерит mp4 (минимум 30 сек, со склейкой и voiceover)
- [ ] Telegram bot отправляет poster + optional video + inline button реальному tg-аккаунту
- [ ] Лендинг открывается по ссылке из tg, видео автоплеит, CTA трекается
- [ ] Mock deposit submit пишется в `/track/deposit` и обновляет campaign до `converted`
- [ ] Metrics dashboard показывает реальные данные по проведенным кампаниям + simulation цифры в USD

### Polish - желательное

- [ ] Минимум 5 финальных видео сгенерены и доступны для просмотра в demo video
- [ ] RU-лендинг тоже задеплоен
- [ ] ARCHITECTURE.md с диаграммой dataflow
- [ ] CASE_STUDY.md с цифрами симуляции и источниками benchmarks (USD)
- [ ] Скриншоты dashboard и Telegram delivery в README
- [ ] Все три cohort archetypes показаны в demo video (high_value_dormant, casual_dormant, post_event)

### Submission text - что в нем сказать (EN, минимум 200 слов)

- Что делает (autonomous reactivation agent для international iGaming / consumer subscription products)
- Где Runway API использован (gen4_image для frames, gen4.5 для motion graphics, eleven_multilingual_v2 для voiceover, всё в одной orchestration pipeline)
- Что это решает (CRM teams тратят дни на персонализированный outreach, agent делает за минуты с human approval gate)
- Почему это product, а не toy (event-driven, real distribution через Telegram, tracking до conversion, ROI simulation в USD)
- Технический depth (parallel Runway tasks, ffmpeg stitching, async approval workflow, DeliveryAdapter architecture, consent-gated channel selection)
