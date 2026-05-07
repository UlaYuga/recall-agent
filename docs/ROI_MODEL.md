# ROI Model

See [PM Delivery Artifacts](PM_DELIVERY_ARTIFACTS.md) for the full source pack.

## Core Formula

```text
incremental_revenue = targeted_users * baseline_reactivation * relative_uplift * ltv
roi = (incremental_revenue - campaign_cost) / campaign_cost
```

## PoC Assumptions

- Baseline reactivation: 7%.
- Conservative AI-video uplift: 30% relative.
- 60-day LTV per reactivated user: about $58.
- Runway cost per generated video: about $0.57-0.60.

