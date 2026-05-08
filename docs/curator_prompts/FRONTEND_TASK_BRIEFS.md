# Frontend Task Readiness Brief

## Current Dashboard Snapshot

- `dashboard/package.json` already exists and currently uses Next `15.5.15`, React `18.3.1`, TypeScript, Tailwind, `@tanstack/react-query`, `recharts`, and `lucide-react`.
- Current app files are minimal placeholders: `dashboard/app/layout.tsx`, `dashboard/app/page.tsx`, `dashboard/app/metrics/page.tsx`, `dashboard/components/ApprovalCard.tsx`, `dashboard/components/ScriptEditor.tsx`, and `dashboard/components/VideoPreview.tsx`.
- There is also an existing singular detail route at `dashboard/app/campaign/[id]/page.tsx`; it is only a placeholder and does not match the future XLSX/planned plural route shape `/campaigns/[id]`.
- What already exists: App Router scaffold, global CSS wiring, package install baseline, metrics page stub, and basic placeholder components.
- What is missing: real sidebar/header layout, `/campaigns` index route, `/campaigns/[id]` workspace route, `/settings` route, shared API client at `dashboard/lib/api.ts`, real table/workspace/metrics UI, and any `dashboard/components/ui/*` shadcn-style primitives.
- XLSX mismatch to account for in future prompts:
  - `T-12` says “Next.js 14 + shadcn init”, but repo reality is an existing Next `15.5.15` dashboard app.
  - XLSX assumes greenfield creation, but future work must adapt and upgrade the existing scaffold.
  - XLSX routes use plural `/campaigns...`, while repo currently has a singular placeholder route under `campaign/[id]`.

## Design Direction

- Internal CRM approval cockpit, not a public landing page.
- Dense, scan-friendly, work-focused UI for operators reviewing queue items quickly.
- Avoid landing-page hero sections, decorative filler, generic purple gradients, nested cards, and oversized spacing.
- Prefer restrained but polished operational patterns: tables, side panels, tabs, badges, status chips, compact forms, inline actions, and clear empty/error states.
- `lucide-react` icons are already installed and may be used where they improve scanning or status recognition.
- Keep text in English unless a source artifact explicitly requires Russian.

## Shared Frontend Constraints

- Use Next.js App Router.
- Use TypeScript.
- Use Tailwind.
- Expect `NEXT_PUBLIC_API_URL` for backend calls.
- Centralize backend access in a shared fetcher so base URL handling, error normalization, and loading/error patterns are not duplicated per page.
- Do not fetch unavailable endpoints before the backend dependency is done unless the prompt explicitly allows a clearly marked mock/static fallback.
- Build must pass before handoff.

## T-12 Readiness Notes

- XLSX goal: dashboard skeleton Next.js + shadcn with sidebar/header foundation.
- XLSX scope: `dashboard/package.json`, `dashboard/app/layout.tsx`, `dashboard/app/page.tsx`, `dashboard/components/ui/*`.
- XLSX deliverable: local dashboard renders and provides baseline app structure.
- XLSX DoD: `localhost:3000` opens and shows sidebar with Campaigns / Metrics / Settings.
- XLSX verification: `cd dashboard && npm run build`.
- Current repo reality: dashboard app already exists, already uses App Router/TypeScript/Tailwind, and already has package dependencies beyond the XLSX baseline.
- Dependency gate: `T-01` must be accepted or explicitly adapted, because the repo scaffold and dashboard directory already exist.
- Future prompt adjustment: instruct executor to **verify/upgrade the existing dashboard skeleton** rather than create one from scratch.
- Required screens/routes for the upgraded skeleton: `/`, `/campaigns`, `/metrics`, `/settings`.
- Required layout: persistent sidebar with Campaigns, Metrics, Settings, plus header/top bar.
- Specific mismatch to resolve in future implementation: repo currently has `dashboard/app/campaign/[id]/page.tsx`; planned route structure should be aligned to plural `campaigns` before T-14 work proceeds.
- Checks the future executor should run:
  - `cd dashboard && npm run build`
  - `cd dashboard && npm run dev`
  - Open `/`, `/campaigns`, `/metrics`, and `/settings`
  - Verify sidebar/header render consistently across routes
  - Verify no placeholder route conflicts remain between `campaign/[id]` and `campaigns/[id]`

## T-13 Readiness Notes

- XLSX goal: dashboard queue view.
- XLSX scope: `dashboard/app/campaigns/page.tsx` and `dashboard/lib/api.ts`.
- XLSX deliverable: campaigns list from backend plus status filter.
- XLSX DoD: after seed + scan flow, all expected campaigns are visible in the queue.
- XLSX verification: open `/campaigns` and confirm the table renders.
- Dependency gate: `T-11` and `T-12` must be done.
- Expected API: `/approval/queue`.
- Expected UI states:
  - loading
  - empty
  - error
  - data table
  - filters by status
- Expected columns: player id/name, country/currency, cohort badge, risk score, offer summary, status, created_at.
- Row click should route to `/campaigns/[id]`.
- Current repo reality: neither `dashboard/app/campaigns/page.tsx` nor `dashboard/lib/api.ts` exists yet.
- Future prompt should require the executor to keep any temporary mock isolated behind a clear switch or local fallback and use it only if coordinator explicitly allows it because the API is not ready.
- Future prompt should also require the queue view to display classifier output as deterministic backend output, not imply that an LLM decides eligibility.

## T-14 Readiness Notes

- XLSX goal: campaign workspace with approve/reject/edit flow.
- XLSX scope: `dashboard/app/campaigns/[id]/page.tsx` and `dashboard/components/CampaignWorkspace.tsx`.
- XLSX deliverable: functional approval workflow UI.
- XLSX DoD: approve updates status, edits persist and re-read, reject requires reason.
- XLSX verification: manual walkthrough approving `p_001` and confirming DB status changes.
- Dependency gate: `T-13` must be done.
- Expected UI:
  - player profile
  - agent reasoning
  - cohort/risk
  - offer details
  - editable script scenes
  - full voiceover preview
  - consent/delivery eligibility
  - Approve / Reject / Save edits
  - Reject reason required
  - video status polling after approve
- Current repo reality: there is only a placeholder singular route at `dashboard/app/campaign/[id]/page.tsx`; future implementation should align to the planned plural route structure and should not treat the placeholder as finished functionality.
- Manual proof expected: approve a campaign and verify DB status changed accordingly.
- Future prompt should explicitly call out post-approve polling boundaries so polling is isolated to the workspace or status component that needs it.

## T-29 Readiness Notes

- XLSX goal: metrics dashboard page + ROI calc.
- XLSX scope: `dashboard/app/metrics/page.tsx`, `dashboard/components/MetricsCards.tsx`, `dashboard/components/Funnel.tsx`.
- XLSX deliverable: metrics UI backed by real numbers.
- XLSX DoD: conversions visible after hero path and ROI calculation works.
- XLSX verification: manual check that `/metrics` values match DB-backed results.
- Dependency gate: `T-28` and `T-12` must be done.
- Expected API: `/metrics/dashboard`.
- Expected UI:
  - big numbers
  - funnel chart
  - cohort table
  - ROI scenario picker
  - refresh behavior
- `recharts` is already installed, so the future prompt should use the existing dependency rather than add a new charting library.
- Current repo reality: `dashboard/app/metrics/page.tsx` exists only as a minimal stub.

## Responsive And Accessibility Checks

- Desktop-first operational dashboard.
- Mobile must not break, even if dense views horizontally scroll or collapse.
- Buttons, links, filters, tabs, dialogs, and forms must be keyboard accessible.
- Visible focus states are required.
- Use semantic table markup where appropriate.
- Prevent text overflow in compact controls, badges, chips, and table cells.
- Status must not rely on color alone; pair color with text/icon/label.

## Performance Notes

- Avoid unnecessary client components; keep pages/server layout server-first unless interactivity requires client execution.
- Isolate polling to the page or component that actually needs status refresh.
- Centralize the fetcher so caching/error handling patterns are consistent.
- Avoid importing heavy chart components outside the metrics page.
- Use stable keys and primitive dependencies in effects/memos.
- Avoid broad barrel imports if direct imports are available.

## Future Prompt Checklist

- Dependencies accepted?
- API ready?
- Allowed mock fallback?
- Routes/files in scope?
- States covered?
- Build command?
- Browser/manual proof?
- Responsive/a11y checks?
- Product safety constraints?

## Open Questions

- Is `T-11` accepted and does it expose `/approval/queue` in the shape expected by T-13?
- Is `T-28` accepted and does it expose `/metrics/dashboard` with the fields needed for T-29 big numbers, funnel, cohort table, and ROI scenario data?
- For route naming, should the existing placeholder under `dashboard/app/campaign/[id]/page.tsx` be migrated to plural `dashboard/app/campaigns/[id]/page.tsx` as part of T-12 route cleanup or deferred until T-14?
