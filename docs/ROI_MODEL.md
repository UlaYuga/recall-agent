# ROI Model — Recall

**Purpose:** Explain the economic case for AI-personalized video reactivation in international iGaming.  
**Currency:** All figures in USD. Local currencies normalized at dashboard level.  
**Hackathon free credits are excluded from ROI calculations.** Model uses **production economics** — the same numbers an operator would use to evaluate a vendor.

---

## 1. Reactivation Funnel

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ SCANNED  │───▶│ ELIGIBLE │───▶│ APPROVED │───▶│ GENERATED│───▶│ DELIVERED│───▶│  PLAYED  │───▶│ CONVERTED│
│ dormant  │    │ consent  │    │ CRM gate │    │  video   │    │ channel  │    │ watched  │    │ deposited│
│ detected │    │  check   │    │ review   │    │  ready   │    │  sent    │    │  ≥50%    │    │  post-CTA│
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
  100%            ~98%            ~85%            ~80%            ~95%            ~60%            ~9%
```

**Funnel stage definitions:**

| Stage | What happens | Drop-off reason |
|---|---|---|
| Scanned | Agent polls event bus, identifies dormant players | — |
| Eligible | Consent check: `data_processing` + `video_personalization` | Missing generation consent |
| Approved | CRM manager reviews script/offer; approves or rejects | Wrong tone, offer mismatch, data issue |
| Generated | Runway pipeline produces mp4 + poster | Generation failure, moderation block |
| Delivered | Selected channel sends media | Channel unavailable, consent gap |
| Played | Player watches ≥50% of video | Ignored, scrolled past, notification off |
| Converted | Player clicks CTA and completes deposit | Not interested, wrong timing, competitor |

**Key insight:** The largest drop-offs are at the **Played** and **Converted** stages. The AI video pipeline addresses the Played stage (personalization → attention → watch), and the offer engine addresses the Converted stage (right reward → action).

---

## 2. Core Formulas

### 2.1 Incremental Reactivation

```
baseline_reactivations = targeted_players × baseline_reactivation_rate
ai_reactivations = targeted_players × (baseline_reactivation_rate × (1 + relative_uplift))
incremental_reactivated = ai_reactivations - baseline_reactivations
```

Or simplified:

```
incremental_reactivated = targeted_players × baseline_reactivation_rate × relative_uplift
```

### 2.2 Revenue and Cost

```
incremental_revenue = incremental_reactivated × value_60d_per_reactivated_player
campaign_cost = targeted_players × cost_per_targeted_player
net_lift = incremental_revenue - campaign_cost
```

### 2.3 ROI and Payback

```
roi = net_lift / campaign_cost          (expressed as ratio or %)
payback_days = 60 / (1 + roi)           (simplified: 60-day revenue ÷ 60-day cost ratio)
```

Or more precisely for multi-cycle:

```
monthly_net = net_lift / 2              (assuming 60-day window ≈ 2 months)
payback_months = campaign_cost / monthly_net
```

---

## 3. Parameter Definitions

| Parameter | Symbol | Description | Source |
|---|---|---|---|
| `targeted_players` | N | Dormant players in batch | CRM segment size |
| `baseline_reactivation_rate` | r_b | % who return without video outreach | Engagehut benchmarks: 5-10% |
| `relative_uplift` | u | % improvement from personalized video vs generic | Idomoo/Entain case: 100%+; Recall uses conservative 20-50% |
| `value_60d_per_reactivated_player` | v | Average net revenue from reactivated player over 60 days | iGaming international mid-tier: $40-85 |
| `cost_per_targeted_player` | c | Media generation + hosting + CRM ops + delivery per player | Estimated production cost: $0.25 |

**Why conservative uplift?** Idomoo and Entain report 100%+ uplift from personalized video in iGaming. Recall uses 20-50% for the following reasons:
- Those case studies are vendor-published; independent verification is limited.
- PoC-quality video (3-day hackathon) vs production-grade motion graphics differ.
- Conservative numbers are more credible to operators evaluating a new vendor.
- The model still shows positive ROI even at the low end.

---

## 4. Three Scenarios

| Parameter | Conservative | Base | Aggressive |
|---|---|---|---|
| Baseline reactivation rate | 5% | 7% | 10% |
| AI video uplift (relative) | +20% | +30% | +50% |
| 60-day value per reactivated player | $40 | $58 | $85 |
| Cost per targeted player | $0.25 | $0.25 | $0.25 |

### 4.1 Production-Scale Worked Example (Base Scenario)

Target: **10,000 dormant players** in one batch.

```
baseline_reactivations    = 10,000 × 0.07          = 700
ai_reactivations          = 10,000 × (0.07 × 1.30) = 910
incremental_reactivated   = 910 - 700              = 210
incremental_revenue       = 210 × $58              = $12,180
campaign_cost             = 10,000 × $0.25         = $2,500
net_lift                  = $12,180 - $2,500       = $9,680
ROI                       = $9,680 / $2,500        = 3.87× (387%)
Payback (60-day window)   = $2,500 / ($9,680/2)   ≈ 0.5 months
```

**Interpretation:** For every $1 spent on the pipeline, the operator recovers $4.87 within 60 days. The campaign pays for itself in roughly 2 weeks. This holds even at conservative uplift assumptions.

### 4.2 Scenario Comparison (10,000 Players)

| Metric | Conservative | Base | Aggressive |
|---|---|---|---|
| Incremental reactivated | 100 | 210 | 500 |
| Incremental revenue | $4,000 | $12,180 | $42,500 |
| Campaign cost | $2,500 | $2,500 | $2,500 |
| Net lift | $1,500 | $9,680 | $40,000 |
| ROI | 0.60× (60%) | 3.87× (387%) | 16.0× (1600%) |
| Payback | ~2 months | ~2 weeks | ~4 days |

**The model stays positive even in the conservative scenario** (ROI > 0), which is the critical threshold for operator adoption: "Does this lose money if it underperforms?" → No.

### 4.3 Cohort-Specific Uplift

Not all dormant players respond equally. Cohorts with higher engagement history show stronger uplift:

| Cohort | Relative uplift | Rationale |
|---|---|---|
| `high_value_dormant` | +40% | Previously high activity; strong incentive to return with personalized offer |
| `casual_dormant` | +25% | Light activity; lower attachment; video novelty may help |
| `post_event` | +30% | Event-driven churn; timing and event recall improve response |
| `first_deposit_no_return` | +20% | Weakest attachment; highest risk of no response |
| `lapsed_loyal` | +35% | Past loyalty; reactivation story resonates |
| `vip_at_risk` | +40% | Highest LTV; personal manager call + video synergy |

These cohort-specific uplifts feed into the dashboard's cohort breakdown table (TECH_SPEC §10.2 item 3).

---

## 5. 7-Player Demo Walkthrough

The 7 mock players are not a statistically significant batch for ROI calculation (N=7). They serve as a **qualitative pipeline demonstration**, not a quantitative ROI proof. Here's how to position them:

### 5.1 Demo Batch Composition

| Player | Cohort | Currency | Estimated 60d value (USD) | Demo purpose |
|---|---|---|---|---|
| Lucas (p_001) | high_value_dormant | BRL | ~$1,200 | High-value reactivation showcase |
| Mariana (p_002) | casual_dormant | MXN | ~$80 | Channel fallback demo (no Telegram) |
| Thabo (p_003) | post_event | ZAR | ~$110 | Sportsbook event-triggered reactivation |
| Andrei (p_004) | lapsed_loyal | EUR | ~$60 | Long-tenure decline case |
| James (p_005) | first_deposit_no_return | GBP | ~$12 | Single-deposit, no-return edge case |
| Sofia (p_006) | casual_dormant | EUR | ~$50 | Consent-gated delivery (email disabled) |
| Ingrid (p_007) | vip_at_risk | NOK | ~$4,200 | VIP risk signal + personal touch |

### 5.2 What the Demo Proves

The 7-player batch demonstrates these production-relevant qualities:

- **All 6 cohort archetypes** represented.
- **4 currencies** (BRL, MXN, ZAR, EUR, GBP, NOK) — multi-currency pipeline.
- **Consent diversity** — 2 players with Telegram gaps, 1 with email disabled, 1 VIP with all channels.
- **Pipeline resilience** — channel fallback, consent gating, offer tier adjustment.
- **Dashboard observability** — CRM manager sees all 7 campaigns in queue with cohort, risk score, and delivery status.

### 5.3 How to Talk About ROI in Demo

> "This batch of 7 players demonstrates the full pipeline. At production scale — 10,000 dormant players per batch, 12 batches per year — the conservative model projects $18,000 annual net lift from a $30,000 annual pipeline cost, with base-case showing $116,000 annual net lift. The 7-player demo validates the architecture; the ROI model validates the business case."

---

## 6. Production Cost Breakdown

Cost per targeted player ($0.25) decomposes as follows (production-scale estimate, not hackathon):

| Cost component | Per player | Annual (120K players) | Notes |
|---|---|---|---|
| Media generation (Runway API) | $0.05 | $6,000 | 5 credits @ $0.01; gen4_turbo for gallery, gen4.5 for hero |
| Compute & hosting (Railway) | $0.03 | $3,600 | API server, storage, bandwidth |
| LLM API (Anthropic) | $0.02 | $2,400 | Script generation for classified players; ~5K tokens per script |
| CRM ops (human approval) | $0.10 | $12,000 | CRM manager reviews ~85% of campaigns at ~30 sec each |
| Delivery overhead | $0.05 | $6,000 | Telegram API, email ESP, CDN bandwidth |
| **Total per player** | **$0.25** | **$30,000** | |

**Cost optimization at scale:**
- Human approval cost decreases with trust: after 3 months, auto-approve low/medium-risk cohorts → CRM ops cost drops ~40%.
- Bulk credit pricing from Runway may reduce media generation cost.
- LLM cost decreases with smaller models for known cohorts (fine-tuned templates reduce token count).

---

## 7. Annualized Model

### 7.1 Assumptions

| Parameter | Value |
|---|---|
| Monthly dormant player pool | 10,000 (operators with 50K-200K active players) |
| Batches per year | 12 (monthly scan) |
| Re-contacted player overlap | None (60-day window resets; re-targeting only if no conversion) |
| Scenario | Base |

### 7.2 Annual Projection (Base Scenario)

```
Annual targeted           = 10,000 × 12              = 120,000
Annual incremental react. = 120,000 × 0.07 × 0.30   = 2,520
Annual incremental revenue = 2,520 × $58             = $146,160
Annual pipeline cost       = 120,000 × $0.25         = $30,000
Annual net lift            = $146,160 - $30,000      = $116,160
Annual ROI                 = $116,160 / $30,000      = 3.87×
```

### 7.3 Sensitivity: What Moves the Needle Most

| Variable | -20% change | Impact on net lift |
|---|---|---|
| `value_60d` ($58 → $46) | -20% | Net lift drops to $86,160 (still 2.87× ROI) |
| `relative_uplift` (30% → 24%) | -20% | Net lift drops to $87,600 (still 2.92× ROI) |
| `cost_per_player` ($0.25 → $0.30) | +20% | Net lift drops to $110,160 (still 3.06× ROI) |
| `baseline_rate` (7% → 5.6%) | -20% | Net lift drops to $87,600 (still 2.92× ROI) |

**The model is most sensitive to `value_60d`** — a $12 drop in average reactivated player value costs $30K in annual lift. This is the parameter operators should calibrate from their own data. The pipeline itself (cost structure, uplift) is the controllable part.

---

## 8. Break-Even Analysis

At what point does the pipeline stop being profitable?

```
break_even_uplift = cost_per_player / (baseline_rate × value_60d)
                  = $0.25 / (0.07 × $58)
                  = $0.25 / $4.06
                  = 0.062 (6.2%)
```

**Break-even uplift is ~6.2%.** If AI video improves reactivation by at least 6.2% relative to no outreach, the pipeline breaks even. For comparison:
- Industry benchmarks suggest 30-100%+ uplift.
- Recall's conservative scenario assumes 20%.
- The pipeline has ~3× headroom before losing money.

**Break-even at worst-case value_60d ($40, conservative):**
```
break_even_uplift = $0.25 / (0.05 × $40) = $0.25 / $2.00 = 12.5%
```
Still well below the 20% conservative uplift assumption.

---

## 9. What This Model Does NOT Claim

- **No guaranteed reactivation rates.** Uplift is probabilistic; individual campaigns may not convert.
- **No guaranteed deposit amounts.** Value_60d is an average; actual deposits vary by player, market, and offer.
- **No dependency on hackathon free credits.** Model uses production Runway API pricing ($0.01/credit).
- **No revenue attribution beyond 60 days.** Longer-term LTV effects (retention, cross-sell) are excluded from the base model but noted as upside.
- **No claim that video alone drives conversion.** The pipeline includes offer, delivery channel, and landing UX as co-factors.
- **No operator-specific calibration.** Operators should replace baseline rates and value_60d with their own CRM data.

---

## 10. Interactive Dashboard Calculator

The metrics dashboard (TECH_SPEC §10.2 item 4) includes live controls:

| Control | Type | Range | Default |
|---|---|---|---|
| Scenario selector | Dropdown | Conservative / Base / Aggressive | Base |
| Baseline rate slider | Range | 3% – 15% | 7% |
| Uplift slider | Range | 10% – 100% | 30% |
| Value 60d slider | Range | $20 – $150 | $58 |
| Cost per player slider | Range | $0.10 – $0.50 | $0.25 |
| Batch size | Number input | 100 – 100,000 | 10,000 |

All controls trigger live recalculation of:
- Incremental reactivated players
- Net lift (USD)
- ROI ratio
- Payback period (days)
- Annual projection

The calculator is intentionally transparent — every parameter is visible and adjustable. This builds operator trust: "You can plug your own numbers in."

---

## 11. Sources and Benchmarks

| Data point | Source | Notes |
|---|---|---|
| Baseline reactivation 7% | Engagehut dormant player benchmarks | Mid-tier operator average |
| AI video uplift 100%+ | Idomoo/Entain iGaming case study | Recall uses conservative 20-50% |
| 60-day LTV $58 | iGaming international mid-tier composite | Mix of casino + sportsbook; varies by GEO |
| Runway API pricing | https://docs.dev.runwayml.com/guides/pricing/ | $0.01/credit; gen4.5 = 12 creds/sec |
| Telegram delivery cost | Telegram Bot API (free) | Infrastructure cost is hosting + bandwidth |
| Human review time | Estimated: 30 sec per campaign | CRM manager approval gate |

All benchmarks are explicitly labeled as "industry estimates" in the dashboard UI with a tooltip: **"Simulation based on industry benchmarks. Actual results vary by operator, market, and player segment."**

---

## 12. Key Takeaways for Portfolio

1. **The model breaks even at ~6% uplift** — the pipeline does not need to be a miracle to be profitable.
2. **Conservative scenario is net-positive** (60% ROI) even with pessimistic assumptions.
3. **Base scenario delivers 3.9× ROI** with mid-range, defensible numbers.
4. **Cost structure is transparent** — every component has a documented assumption and data source.
5. **The 7-player demo validates architecture, not ROI** — production-scale numbers come from the model, not from N=7.
6. **The model is operator-customizable** — every parameter can be replaced with the operator's own CRM data.
