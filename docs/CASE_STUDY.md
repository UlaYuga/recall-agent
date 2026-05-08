# Case Study

Recall models a mid-tier consumer subscription retention workflow where dormant users are selected for human-approved personalized video outreach.

## E2E Smoke Test (2026-05-09 MSK)

The deployed hero path was verified end-to-end:

| Stage | Result |
|---|---|
| Seed | 7 players + 96 events loaded |
| Scan | 7 campaigns created (all cohorts represented) |
| Approval | 1 campaign approved (high_value_dormant) |
| Tracking | play → click → deposit all recorded |
| Metrics | funnel confirmed 7 → 1 → 1 → 1 → 1 → 1 |
| Dashboard | `/`, `/campaigns`, `/campaigns/{id}`, `/metrics` → 200 |
| Landing | `/`, `/case`, `/r/{campaign_id}` → 200 |
| CORS | preflight OK from both Vercel origins |

Live URLs:
- Backend: `https://recall-agent-production-4dc7.up.railway.app`
- Dashboard: `https://dashboard-ula-lab.vercel.app`
- Landing: `https://landing-ula-lab.vercel.app`

## Simulated Funnel

```text
targeted -> approved -> rendered -> delivered -> played -> clicked -> converted
```

## Optional Visual Artifacts

- Approval queue screenshot.
- Campaign detail screenshot.
- Delivery adapter state or Telegram capture if a real send is approved.
- Reactivation landing screenshot.
- Metrics dashboard screenshot.
