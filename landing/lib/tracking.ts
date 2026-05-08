/**
 * Tracking helpers for the reactivation landing page.
 *
 * All functions are fire-and-forget: errors are silently swallowed so a
 * failed analytics call never breaks the player UX.
 *
 * Backend contract (T-27):
 *   POST /track/play    { campaign_id, watched_seconds? }
 *   POST /track/click   { campaign_id, link_id? }
 *   POST /track/deposit { campaign_id, amount, currency }
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function post(path: string, body: Record<string, unknown>): void {
  fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).catch(() => {
    // fire-and-forget — never surface tracking errors to the player
  });
}

export function trackPlay(campaignId: string, watchedSeconds?: number): void {
  post('/track/play', {
    campaign_id: campaignId,
    ...(watchedSeconds != null ? { watched_seconds: watchedSeconds } : {}),
  });
}

export function trackClick(campaignId: string, linkId?: string): void {
  post('/track/click', {
    campaign_id: campaignId,
    ...(linkId != null ? { link_id: linkId } : {}),
  });
}

export function trackDeposit(campaignId: string, amount: number, currency: string): void {
  post('/track/deposit', { campaign_id: campaignId, amount, currency });
}
