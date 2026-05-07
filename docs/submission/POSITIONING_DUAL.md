# Двойная упаковка кейса: RU vs EN

Один продукт, два marketing-wrappers с идентичным backend. Backend, код агента, архитектура pipeline, визуальный стиль demo-видео - **идентичны**. Меняется только marketing copy на лендингах и в submission text.

## Зачем двойная упаковка

Защищает от двух противоположных рисков:

1. **Runway compliance review** не должна флажить iGaming-контент в submission - используем EN-версию с generic framing
2. **Российские iGaming-рекрутеры** должны видеть прямой кейс с цитатами 01.tech и iGaming-терминологией - используем RU-версию с прямым позиционированием

Оба лендинга деплоятся на Vercel, оба работают параллельно. EN ставится первым (под submission), RU - бонусом если успеваем (или после хакатона).

---

## RU-версия: позиционирование

### Целевая аудитория
- Senior CRM/Retention/Lifecycle менеджеры iGaming СНГ
- Head of CRM операторов tier-2
- Recruiter'ы iGaming-компаний (PIN-UP, BetBoom, Fonbet, BC.Game и т.д.)

### Фрейминг
**Headline:** "AI-агент реактивации игроков для iGaming СНГ"
**Sub:** "Автономный CRM-агент находит dormant игроков, генерит персональное видео-послание под approve менеджера и доставляет через Telegram. Human in the loop встроен в архитектуру."

### Что подсвечиваем
- Прямая работа с iGaming-cohorts: high_value_dormant, post_event_sportsbook, first_deposit_no_return, vip_at_risk
- Mock-игроки в iGaming-контексте: имя, любимый слот, биггест вин, last deposit RUB
- ROI-расчеты на СНГ-цифрах: baseline 7%, uplift 30%, LTV 5800 руб
- Telegram как primary channel - реальный инсайт по СНГ
- Approval gate как "human in the loop" - прямо повторяет вывод 01.tech-отчета

### Цитаты для RU-лендинга (из Global iGaming Report 2026, 01.tech x G GATE MEDIA)

**Цитата 1 - Head of Sportsbook 01.tech (раздел 4.5):**
> "AI как персональный консультант, способный сопровождать игрока на всех этапах воронки до целевого действия"

Применение: используем в hero-блоке как валидацию концепции. AI-агент в нашем кейсе именно сопровождает игрока на этапе churn-prevention, что точно ложится в эту формулировку.

**Цитата 2 - Head of White Label 01.tech, Александр Романов (заключение отчета):**
> "Смещение фокуса с быстрого оборота трафика к работе с LTV, retention и долгосрочной монетизацией"
> "AI как мультипликатор эффективности"

Применение: в case-блоке про экономику. Аргумент "не привлекать новый траф, а реактивировать имеющийся" - прямо в эту цитату упирается.

**Цитата 3 - раздел 4.5 отчета:**
> "Глубокое внедрение AI: 30% упоминаний как главный тренд 2026"

Применение: в блоке "почему сейчас". Тренд подтвержден отчетом, мы строим конкретный инструмент под этот тренд.

### Структура RU-лендинга

**1. Hero**
- Headline + sub
- 30-сек loop demo видео слева, справа - три bullets:
  - Находит dormant за 7-30 дней
  - Генерит персональное видео под approve менеджера
  - Доставляет через Telegram + email, трекает до депозита
- CTA "Посмотреть demo"

**2. Проблема (problem block)**
- "Реактивация в iGaming СНГ работает плохо: D30 retention 10-20% у tier-2 операторов (Smartico data)"
- "Human-led outreach даёт до 15% реактивации (Enteractive), но не масштабируется"
- "Mass email/push - 5-10% реактивации в лучшем случае (Engagehut benchmarks)"

**3. Решение (concept)**
- Цитата 1 - Head of Sportsbook 01.tech
- Описание архитектуры pipeline: trigger → classify → script → approve → render → deliver → track
- Схема dataflow

**4. Почему AI-видео а не текст**
- Idomoo + Entain case: 88% conversion rate у personalized video
- Optimove benchmark: advanced CRM maturity = 61% активированной базы vs 14% у low-maturity
- Цитата 2 (LTV-фокус) - Александр Романов

**5. Demo + скриншоты**
- Скриншот approval dashboard (queue + side panel)
- Скриншот reactivation landing с видео и offer
- Гифка/видео Telegram доставки

**6. Метрики симуляции**
- Big numbers: targeted, sent, played, converted, ROI
- Cohort breakdown
- Источники цифр явно указаны: Optimove, Xtremepush, Enteractive, Engagehut, Idomoo

**7. Tech stack**
- FastAPI + Anthropic Claude Sonnet 4.5 + Runway Gen-4.5 + ElevenLabs (внутри Runway) + Telegram Bot API + Next.js
- Цитата 3 - "глубокое внедрение AI как тренд 2026"

**8. Принципы (важно для retention-аудитории)**
- Human in the loop встроен в архитектуру (approval gate)
- Никаких guarantees, манипулятивных триггеров, gambling slang в скриптах
- Compliance-friendly: agent не отправляет ничего без подтверждения CRM-менеджера

**9. CTA**
- "GitHub репо" + "Связаться: telegram, email"
- (для рекрутеров) "Резюме: link"

### CTA-формулировки RU
- "Сделать депозит" (на reactivation landing)
- "Получить бонус"
- "Возвращайся, у нас для тебя кое-что есть"
- "Забрать подарок"

---

## EN-версия: позиционирование

### Целевая аудитория
- Runway hackathon judges
- Generic AI/SaaS engineering audience
- Anyone who lands on the page from Runway's submission showcase

### Фрейминг
**Headline:** "AI Retention Agent for Consumer Subscription Products"
**Sub:** "Autonomous agent monitors user activity, identifies churn risk, generates personalized motion graphics video messages with human approval, and delivers them via Telegram. Built on Runway API."

### Что подсвечиваем
- Generic industry framing: subscription products, consumer SaaS, content platforms, fintech
- Mock-users без gambling-контекста: имя, любимая фича, milestone, last activity date
- Generic CTA-формулировки: "We miss you", "personal welcome back gift", "check what's new"
- Technical depth: parallel Runway tasks, ffmpeg pipeline, async approval workflow
- Real distribution через Telegram bot - не просто демо, реальная end-to-end система

### Цитаты для EN-лендинга
01.tech цитаты - **не используем**. Вместо них:
- Generic AI-CRM industry data (Gartner, Forrester, Optimove public benchmarks)
- Quote-style блок с обобщенным insight: "Personalization is no longer optional - users churn without it"
- Никаких отсылок к gambling, casino, sportsbook, iGaming

### Структура EN-лендинга

**1. Hero**
- Headline + sub
- 30-сек loop demo video
- Three bullets:
  - Detects user churn risk via event bus
  - Generates personalized motion graphics with approval gate
  - Delivers via Telegram + email, tracks to conversion
- CTA "See live demo"

**2. Problem**
- "Customer retention is the new growth lever for subscription products"
- "Mass email reactivation campaigns convert at 2-5%"
- "Manual personalized outreach doesn't scale"
- (Без iGaming-цифр)

**3. Solution / How it works**
- Architecture diagram
- Pipeline description: event bus → AI classifier → script generation → human approval → video render → delivery → tracking

**4. Why AI Video**
- Personalized video messaging shows higher engagement than text in B2C contexts
- Reference to public studies on video CTR (без gambling-cases)

**5. Demo screenshots**
- Same as RU but with EN-localized UI

**6. Metrics simulation**
- Same numbers but в USD равно RUB-конвертация: $58 LTV per reactivated user
- Cohort breakdown в generic terms: "high-value dormant", "casual lapsed", "post-onboarding inactive", "first-purchase no-return"
- Sources cited: industry benchmark data (avoid gambling-specific citations)

**7. Tech stack + Runway integration**
- Highlight Runway specifically: gen4.5 для motion graphics, gen4_image_turbo для start frames, eleven_multilingual_v2 для voiceover
- Parallel task orchestration via async Runway SDK
- Эмфазис на "leveraging Runway's full media generation pipeline"

**8. Built for**
- Consumer subscription products (streaming, SaaS, fitness, education)
- E-commerce reactivation
- Content platform retention
- (Не упоминаем gambling)

**9. CTA**
- GitHub link
- "Try it yourself" - инструкция как развернуть репо локально

### CTA-формулировки EN
- "We miss you"
- "Claim your personal welcome back gift"
- "Check what's new"
- "Come back and see what we built for you"
- "Your free month is waiting" (если контекст subscription)

---

## Что одинаково в RU и EN

- Backend код полностью
- LLM промпты для агента (system prompt + tool schemas)
- Schema event bus, players, campaigns
- Approval dashboard UI (только локализация labels)
- Visual style demo видео (motion graphics нейтральные, не привязаны к ru/en)
- Архитектура pipeline на схеме
- Скриншоты dashboard (можно сделать обе локали через `next-intl`, или просто два набора скринов)
- Demo video 2-мин для submission - **один**, на английском с английскими subs/UI

---

## Mock players: разные контексты

**RU-версия (7 mock-игроков):**
- iGaming-контекст: имена RU, last_deposit_amount в RUB, favorite_game_label иGaming-стилизованный (`fruit_slots`, `live_blackjack`, `football_bets`)
- LTV в RUB
- Currency: RUB
- Phone: +7

**EN-версия (те же 7 mock-юзеров, переименованные):**
- Subscription-контекст: имена EN, last_payment_amount в USD, favorite_feature вместо favorite_game (`premium_content`, `pro_features`, `advanced_analytics`)
- LTV в USD
- Currency: USD
- Phone: +1

В коде - **один JSON seed файл с двумя локалями** (`players.ru.json` и `players.en.json`). Бэкенд отдает нужный по `Accept-Language` или флагу в URL.

---

## Submission text для Runway (EN, минимум 200 слов)

Ключевой документ. Это финальный текст в форме хакатона. Пишется в воскресенье-понедельник.

**Структура:**

1. **Hook (что делает в одном предложении):** "Recall is an autonomous CRM agent that turns silent customers back into active users by generating personalized motion graphics video messages on demand, with human approval, and delivering them through Telegram."

2. **Problem:** "Subscription products lose 5-15% of users to churn every month. Mass email reactivation campaigns convert at 2-5%. Manual personalized outreach by a human CRM manager converts much higher but doesn't scale beyond high-value cohorts."

3. **Solution + Runway integration:** "Recall uses Runway's full media stack to close this gap. The agent monitors a mock event bus, classifies dormant users into cohorts, generates a personalized script with an LLM, and after human approval, orchestrates a parallel pipeline: Gen-4 Image Turbo creates branded start frames, Gen-4.5 generates four motion graphics scenes (5-10s each), and ElevenLabs (via Runway API) renders a Russian voiceover. ffmpeg stitches the final 30-45 second video and overlays the offer copy."

4. **Distribution + tracking:** "The video is delivered through a Telegram bot with an inline CTA button leading to a personalized landing page. The landing tracks plays, watch percentages, CTA clicks, and mock conversions back to the dashboard. The CRM manager sees real-time uplift simulation comparing baseline reactivation rates vs AI-video assisted ones."

5. **Why this matters:** "This is not a single API call. It's a chain of creative decisions that respond to user data, run through human review, and produce video that real users actually receive in their messaging app. The same architecture works for any subscription product where personalized reengagement is the bottleneck - SaaS, fitness apps, content platforms, e-commerce."

6. **Tech depth:** "Parallel async Runway tasks, ffmpeg-based stitching with audio mixing, structured LLM tool use for cohort classification, multi-channel delivery, end-to-end conversion tracking. Built solo over 3 days."

Final word count target: 280-350 слов.
