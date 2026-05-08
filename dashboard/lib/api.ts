const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
};

// ── Shared types ───────────────────────────────────────────────────────────

export type CampaignStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'generating'
  | 'generation_failed'
  | 'ready'
  | 'ready_blocked_delivery'
  | 'delivered'
  | 'converted';

export interface PlayerProfile {
  first_name: string;
  country: string;
  currency: string;
  ltv_segment: string;
  last_login_at: string | null;
  last_deposit_at: string | null;
  total_deposits_count: number;
  total_deposits_amount: number;
  favorite_vertical: string | null;
  favorite_game_category: string | null;
  favorite_game_label: string | null;
  biggest_win_amount: number | null;
  biggest_win_currency: string | null;
  preferred_language: string;
}

export interface QueueItem {
  campaign_id: string;
  player_id: string;
  first_name: string;
  country: string;
  currency: string;
  cohort: string;
  risk_score: number;
  status: CampaignStatus;
  offer_json: string | null;
  script_json: string | null;
  reasoning_json: string | null;
  created_at: string | null;
  updated_at: string | null;
  player: PlayerProfile;
}

export interface ScriptScene {
  id: number;
  type: string;
  text: string;
  visual_brief: string;
}

export interface ScriptData {
  scenes: ScriptScene[];
  full_voiceover_text: string;
  estimated_duration_sec: number;
  tone: string;
  cta_text: string;
  source: string;
}

export interface OfferData {
  type: string;
  value: number;
  label: string;
  copy: string;
  terms: string;
  expiry_days: number;
  offer_band: string;
  game_label: string | null;
  cohort: string;
}

export interface QueueFilters {
  cohort?: string;
  risk_score_min?: number;
  status?: string;
}

// ── Video + Delivery types ─────────────────────────────────────────────────

export interface VideoStatus {
  campaign_id: string;
  /** 'queued' | 'generating' | 'ready' | 'failed' */
  status: string;
  video_url?: string;
  poster_url?: string;
  runway_task_ids?: string[];
}

export interface DeliveryChannel {
  channel: string;
  status: string;
  reason?: string | null;
  message_id?: string | null;
  recipient?: string | null;
}

export interface DeliveryResult {
  campaign_id: string;
  overall_status: string;
  channels: DeliveryChannel[];
}

// ── Approval API ────────────────────────────────────────────────────────────

export const approval = {
  queue(filters?: QueueFilters): Promise<QueueItem[]> {
    const qs = new URLSearchParams();
    if (filters?.cohort) qs.set('cohort', filters.cohort);
    if (filters?.risk_score_min !== undefined)
      qs.set('risk_score_min', String(filters.risk_score_min));
    if (filters?.status) qs.set('status', filters.status);
    const q = qs.toString();
    return api.get<QueueItem[]>(`/approval/queue${q ? `?${q}` : ''}`);
  },

  approve(campaignId: string) {
    return api.post<{ campaign_id: string; status: string; updated_at: string | null }>(
      `/approval/${campaignId}/approve`,
      {}
    );
  },

  reject(campaignId: string, reason: string) {
    return api.post<{
      campaign_id: string;
      status: string;
      reject_reason: string;
      updated_at: string | null;
    }>(`/approval/${campaignId}/reject`, { reason });
  },

  edit(
    campaignId: string,
    body: { offer_json?: string | null; script_json?: string | null; auto_approve?: boolean }
  ) {
    return api.post<{
      campaign_id: string;
      status: string;
      changed: string[];
      auto_approved: boolean;
      updated_at: string | null;
    }>(`/approval/${campaignId}/edit`, body);
  },

  regenerate(campaignId: string) {
    return api.post<{
      campaign_id: string;
      script: ScriptData;
      updated_at: string | null;
    }>(`/approval/${campaignId}/regenerate-script`, {});
  },

  getCampaign(campaignId: string): Promise<QueueItem> {
    return api.get<QueueItem>(`/approval/${campaignId}`);
  },
};

// ── Video API ───────────────────────────────────────────────────────────────

export const video = {
  /** Returns null when no video has been generated yet (404 from backend). */
  status(campaignId: string): Promise<VideoStatus | null> {
    return api
      .get<VideoStatus>(`/video/status/${campaignId}`)
      .catch((e: unknown) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      });
  },

  generate(campaignId: string) {
    return api.post<{ task_id: string; campaign_id: string; status: string }>(
      '/video/generate',
      { campaign_id: campaignId }
    );
  },
};

// ── Delivery API ────────────────────────────────────────────────────────────

export const delivery = {
  send(campaignId: string): Promise<DeliveryResult> {
    return api.post<DeliveryResult>('/delivery/send', { campaign_id: campaignId });
  },
};
