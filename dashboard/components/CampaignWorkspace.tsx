'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  AlertCircle,
  Loader2,
  RefreshCw,
  Play,
  Send,
  Video,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  approval,
  video,
  delivery,
  type QueueItem,
  type VideoStatus,
  type OfferData,
  type ScriptData,
  type ScriptScene,
} from '../lib/api';

// ── Constants ─────────────────────────────────────────────────────────────────

const VIDEO_POLL_STATUSES = new Set(['queued', 'generating']);

const STATUS_CHIP: Record<string, string> = {
  draft:                  'bg-line text-dim',
  pending_approval:       'bg-info/10 text-info',
  approved:               'bg-pass/10 text-pass',
  rejected:               'bg-fail/10 text-fail',
  generating:             'bg-warn/10 text-warn',
  generation_failed:      'bg-fail/10 text-fail',
  ready:                  'bg-accent/10 text-accent',
  ready_blocked_delivery: 'bg-warn/10 text-warn',
  delivered:              'bg-pass/10 text-pass',
  converted:              'bg-accent/10 text-accent',
};

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draft',
  pending_approval: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  generating: 'Generating',
  generation_failed: 'Failed',
  ready: 'Ready',
  ready_blocked_delivery: 'Blocked',
  delivered: 'Delivered',
  converted: 'Converted',
};

const SCENE_LABELS: Record<string, string> = {
  intro: 'Intro',
  personalized_hook: 'Hook',
  offer: 'Offer',
  cta: 'CTA',
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function parseOffer(json: string | null): OfferData | null {
  if (!json) return null;
  try {
    return JSON.parse(json) as OfferData;
  } catch {
    return null;
  }
}

function parseScript(json: string | null): ScriptData | null {
  if (!json) return null;
  try {
    return JSON.parse(json) as ScriptData;
  } catch {
    return null;
  }
}

function parseReasoning(json: string | null): string[] {
  if (!json) return [];
  try {
    const data: unknown = JSON.parse(json);
    if (Array.isArray(data)) return data as string[];
    return [];
  } catch {
    return [];
  }
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function fmtNum(n: number | null | undefined): string {
  if (n == null) return '—';
  return n.toLocaleString('en-US', { maximumFractionDigits: 2 });
}

function cohortLabel(c: string): string {
  return c.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

function riskClass(score: number): string {
  if (score >= 70) return 'text-fail font-semibold';
  if (score >= 40) return 'text-warn font-medium';
  return 'text-pass';
}

// ── Section ───────────────────────────────────────────────────────────────────

function Section({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const id = `ws-section-${title.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className="bg-graph border border-edge rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={id}
        className="flex w-full items-center justify-between px-5 py-3 text-xs font-semibold text-sub uppercase tracking-wide hover:bg-char focus:outline-none focus:ring-2 focus:ring-inset focus:ring-accent transition-colors"
      >
        <span>{title}</span>
        {open ? (
          <ChevronUp size={13} aria-hidden="true" />
        ) : (
          <ChevronDown size={13} aria-hidden="true" />
        )}
      </button>
      {open && (
        <div id={id} className="px-5 pb-5 pt-1 border-t border-edge">
          {children}
        </div>
      )}
    </div>
  );
}

// ── ProfileRow ────────────────────────────────────────────────────────────────

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-sub">{label}</dt>
      <dd className="text-text font-medium truncate" title={value}>
        {value}
      </dd>
    </>
  );
}

// ── SceneCard ─────────────────────────────────────────────────────────────────

function SceneCard({ scene }: { scene: ScriptScene }) {
  return (
    <div className="space-y-0.5">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-sub">
        {SCENE_LABELS[scene.type] ?? scene.type}
      </span>
      <p className="text-xs text-text leading-relaxed">{scene.text}</p>
      <p className="text-[10px] text-sub leading-relaxed">Visual: {scene.visual_brief}</p>
    </div>
  );
}

// ── VideoSection ──────────────────────────────────────────────────────────────

interface VideoSectionProps {
  campaignId: string;
  campaignStatus: string;
}

function VideoSection({ campaignId, campaignStatus }: VideoSectionProps) {
  const [actionError, setActionError] = useState<string | null>(null);
  const [deliveryResult, setDeliveryResult] = useState<string | null>(null);
  const qc = useQueryClient();

  const canGenerate = campaignStatus === 'approved';
  const canDeliver = campaignStatus === 'ready';
  const isBlockedDelivery = campaignStatus === 'ready_blocked_delivery';
  const isDelivered = campaignStatus === 'delivered' || campaignStatus === 'converted';

  const {
    data: vs,
    isLoading: vsLoading,
    isError: vsError,
    refetch: vsRefetch,
    isFetching: vsFetching,
  } = useQuery({
    queryKey: ['video-status', campaignId],
    queryFn: () => video.status(campaignId),
    refetchInterval: (query) => {
      const d = query.state.data;
      if (d && VIDEO_POLL_STATUSES.has(d.status)) return 5_000;
      return false;
    },
  });

  const generateM = useMutation({
    mutationFn: () => video.generate(campaignId),
    onSuccess: () => {
      setActionError(null);
      void qc.invalidateQueries({ queryKey: ['video-status', campaignId] });
      void qc.invalidateQueries({ queryKey: ['campaign', campaignId] });
    },
    onError: (e) => setActionError(e instanceof Error ? e.message : 'Generate failed'),
  });

  const deliverM = useMutation({
    mutationFn: () => delivery.send(campaignId),
    onSuccess: (res) => {
      setActionError(null);
      const ch = res.channels[0];
      setDeliveryResult(
        ch
          ? `${ch.channel || 'Delivery'}: ${ch.status}${ch.reason ? ` — ${ch.reason}` : ''}`
          : `Overall: ${res.overall_status}`
      );
      void qc.invalidateQueries({ queryKey: ['campaign', campaignId] });
    },
    onError: (e) => setActionError(e instanceof Error ? e.message : 'Delivery failed'),
  });

  const videoReady = vs?.status === 'ready' && !!vs.video_url;
  const videoGenerating = vs?.status === 'queued' || vs?.status === 'generating';

  return (
    <div className="bg-graph border border-edge rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-edge">
        <div className="flex items-center gap-2 text-xs font-semibold text-sub uppercase tracking-wide">
          <Video size={13} aria-hidden="true" />
          Video
        </div>
        <div className="flex items-center gap-2">
          {vs && (
            <span
              className={[
                'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                vs.status === 'ready'
                  ? 'bg-pass/10 text-pass'
                  : vs.status === 'failed'
                    ? 'bg-fail/10 text-fail'
                    : vs.status === 'queued' || vs.status === 'generating'
                      ? 'bg-warn/10 text-warn'
                      : 'bg-line text-dim',
              ].join(' ')}
            >
              {vs.status}
            </span>
          )}
          <button
            type="button"
            onClick={() => void vsRefetch()}
            disabled={vsFetching || vsLoading}
            aria-label="Refresh video status"
            className="p-1 rounded text-sub hover:text-dim hover:bg-char focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-40 transition-colors"
          >
            <RefreshCw
              size={13}
              className={vsFetching ? 'animate-spin' : ''}
              aria-hidden="true"
            />
          </button>
        </div>
      </div>

      <div className="px-5 py-4 space-y-4">
        {/* Loading */}
        {vsLoading && (
          <div className="flex items-center gap-2 text-xs text-sub">
            <Loader2 size={13} className="animate-spin" aria-hidden="true" />
            Checking video status…
          </div>
        )}

        {/* Error */}
        {vsError && (
          <p className="text-xs text-warn">Could not load video status.</p>
        )}

        {/* No video yet */}
        {!vsLoading && !vs && !vsError && (
          <p className="text-xs text-sub italic">No video generated yet.</p>
        )}

        {/* Generating indicator */}
        {videoGenerating && (
          <div className="flex items-center gap-2 text-xs text-warn">
            <Loader2 size={13} className="animate-spin" aria-hidden="true" />
            Generation in progress — polling every 5 s…
          </div>
        )}

        {/* Video failed */}
        {vs?.status === 'failed' && (
          <div className="flex items-center gap-2 text-xs text-fail">
            <AlertCircle size={13} aria-hidden="true" />
            Generation failed.
          </div>
        )}

        {/* Video ready — player */}
        {videoReady && (
          <div className="rounded-lg overflow-hidden bg-ink aspect-video">
            <video
              src={vs.video_url}
              poster={vs.poster_url ?? undefined}
              controls
              className="w-full h-full object-contain"
              aria-label="Generated campaign video"
            />
          </div>
        )}

        {/* Poster only */}
        {!videoReady && vs?.poster_url && (
          <div className="rounded-lg overflow-hidden bg-ink aspect-video">
            <img
              src={vs.poster_url}
              alt="Video poster"
              className="w-full h-full object-contain"
            />
          </div>
        )}

        {/* Errors / results */}
        {actionError && (
          <div
            role="alert"
            className="flex items-start gap-2 text-xs text-fail bg-fail/10 border border-fail/20 rounded px-3 py-2"
          >
            <AlertCircle size={13} className="flex-none mt-0.5" aria-hidden="true" />
            <span>{actionError}</span>
          </div>
        )}

        {deliveryResult && !actionError && (
          <div className="text-xs text-pass bg-pass/10 border border-pass/20 rounded px-3 py-2">
            {deliveryResult}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-1">
          {canGenerate && (
            <button
              type="button"
              disabled={generateM.isPending || videoGenerating}
              onClick={() => {
                setActionError(null);
                generateM.mutate();
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-accent text-ink hover:bg-accent/80 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
            >
              {generateM.isPending || videoGenerating ? (
                <Loader2 size={12} className="animate-spin" aria-hidden="true" />
              ) : (
                <Play size={12} aria-hidden="true" />
              )}
              {videoGenerating ? 'Generating…' : vs ? 'Regenerate Video' : 'Generate Video'}
            </button>
          )}

          {(canDeliver || isDelivered) && (
            <button
              type="button"
              disabled={deliverM.isPending || isDelivered || !videoReady}
              onClick={() => {
                setActionError(null);
                setDeliveryResult(null);
                deliverM.mutate();
              }}
              title={!videoReady ? 'Video must be ready before delivery' : undefined}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-pass text-ink hover:bg-pass/80 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-pass transition-colors"
            >
              {deliverM.isPending ? (
                <Loader2 size={12} className="animate-spin" aria-hidden="true" />
              ) : (
                <Send size={12} aria-hidden="true" />
              )}
              {isDelivered ? 'Delivered' : 'Send Delivery'}
            </button>
          )}

          {isBlockedDelivery && (
            <p className="text-xs text-warn bg-warn/10 border border-warn/20 rounded px-3 py-1.5">
              Delivery is blocked by consent or channel eligibility.
            </p>
          )}

          {!canGenerate && !canDeliver && !isBlockedDelivery && !isDelivered && (
            <p className="text-xs text-sub italic">
              Campaign must be <span className="font-medium text-dim">approved</span> before video generation.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface CampaignWorkspaceProps {
  campaignId: string;
}

export function CampaignWorkspace({ campaignId }: CampaignWorkspaceProps) {
  const {
    data: campaign,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<QueueItem>({
    queryKey: ['campaign', campaignId],
    queryFn: () => approval.getCampaign(campaignId),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-center">
        <Loader2 size={28} className="text-info animate-spin" aria-hidden="true" />
        <p className="text-sm text-sub">Loading campaign…</p>
      </div>
    );
  }

  if (isError || !campaign) {
    return (
      <div className="space-y-4 max-w-xl">
        <Link
          href="/campaigns"
          className="inline-flex items-center gap-1.5 text-sm text-sub hover:text-dim focus:outline-none focus:underline"
        >
          <ArrowLeft size={14} aria-hidden="true" />
          Back to Queue
        </Link>
        <div className="bg-graph border border-edge rounded-lg p-8 flex flex-col items-center gap-3 text-center">
          <AlertCircle size={24} className="text-fail" aria-hidden="true" />
          <p className="text-sm font-medium text-fail">Failed to load campaign</p>
          <p className="text-xs text-sub">
            {error instanceof Error ? error.message : `Campaign ${campaignId} not found`}
          </p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-1 text-xs text-accent hover:underline focus:outline-none focus:ring-1 focus:ring-accent rounded"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const offer = parseOffer(campaign.offer_json);
  const script = parseScript(campaign.script_json);
  const reasoning = parseReasoning(campaign.reasoning_json);
  const p = campaign.player;

  return (
    <div className="space-y-4 max-w-3xl">
      {/* ── Back + header ──────────────────────────────────────────────────── */}
      <div className="flex items-start gap-3">
        <Link
          href="/campaigns"
          className="flex-none mt-0.5 inline-flex items-center gap-1.5 text-sm text-sub hover:text-dim focus:outline-none focus:underline"
        >
          <ArrowLeft size={14} aria-hidden="true" />
          Back to Queue
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-base font-semibold text-text">{p.first_name}</h1>
            <span
              className={[
                'inline-flex items-center rounded px-2 py-0.5 text-xs font-medium',
                STATUS_CHIP[campaign.status] ?? 'bg-line text-dim',
              ].join(' ')}
            >
              {STATUS_LABEL[campaign.status] ?? campaign.status}
            </span>
            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-line text-dim">
              {cohortLabel(campaign.cohort)}
            </span>
            <span className={['text-xs tabular-nums', riskClass(campaign.risk_score)].join(' ')}>
              Risk {Math.round(campaign.risk_score)}
            </span>
          </div>
          <p className="text-xs text-sub mt-0.5">
            {p.country} · {p.currency} · {campaign.player_id} · {campaign.campaign_id}
          </p>
        </div>
      </div>

      {/* ── Video section ──────────────────────────────────────────────────── */}
      <VideoSection campaignId={campaign.campaign_id} campaignStatus={campaign.status} />

      {/* ── Player profile ─────────────────────────────────────────────────── */}
      <Section title="Player Profile">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs mt-1">
          <ProfileRow label="LTV segment" value={p.ltv_segment || '—'} />
          <ProfileRow
            label="Deposits"
            value={`${p.total_deposits_count} × ${p.currency} ${fmtNum(p.total_deposits_amount)}`}
          />
          <ProfileRow label="Last login" value={fmtDate(p.last_login_at)} />
          <ProfileRow label="Last deposit" value={fmtDate(p.last_deposit_at)} />
          {p.favorite_vertical && (
            <ProfileRow label="Vertical" value={p.favorite_vertical} />
          )}
          {p.favorite_game_category && (
            <ProfileRow label="Game category" value={p.favorite_game_category} />
          )}
          {p.favorite_game_label && (
            <ProfileRow label="Game label" value={p.favorite_game_label} />
          )}
          {p.biggest_win_amount != null && (
            <ProfileRow
              label="Biggest win"
              value={`${p.biggest_win_currency ?? p.currency} ${fmtNum(p.biggest_win_amount)}`}
            />
          )}
          <ProfileRow label="Language" value={p.preferred_language} />
        </dl>
      </Section>

      {/* ── Classifier reasoning ───────────────────────────────────────────── */}
      <Section title="Classifier Reasoning" defaultOpen={false}>
        {reasoning.length === 0 ? (
          <p className="text-xs text-sub italic mt-1">No reasoning recorded.</p>
        ) : (
          <ul className="space-y-1.5 mt-1">
            {reasoning.map((r, i) => (
              <li key={i} className="flex gap-2 text-xs text-dim">
                <span className="text-info flex-none mt-0.5" aria-hidden="true">›</span>
                {r}
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* ── Offer ──────────────────────────────────────────────────────────── */}
      <Section title="Offer">
        {!offer ? (
          <p className="text-xs text-sub italic mt-1">Offer data unavailable.</p>
        ) : (
          <div className="space-y-2 text-xs mt-1">
            <div className="flex gap-3">
              <span className="bg-line text-dim rounded px-2 py-0.5 font-medium uppercase text-[10px] tracking-wide">
                {offer.type}
              </span>
              <span className="font-semibold text-text">{offer.label}</span>
            </div>
            <p className="text-dim leading-relaxed">{offer.copy}</p>
            <p className="text-sub leading-relaxed border-l-2 border-edge pl-2">
              {offer.terms}
            </p>
            <div className="flex gap-4 text-sub pt-0.5">
              <span>
                Value: <span className="font-medium text-text">{offer.value}</span>
              </span>
              <span>
                Expires: <span className="font-medium text-text">{offer.expiry_days}d</span>
              </span>
              {offer.game_label && (
                <span>
                  Game: <span className="font-medium text-text">{offer.game_label}</span>
                </span>
              )}
            </div>
          </div>
        )}
      </Section>

      {/* ── Script ─────────────────────────────────────────────────────────── */}
      <Section title="Script (4 Scenes)">
        {!script ? (
          <p className="text-xs text-sub italic mt-1">Script not generated yet.</p>
        ) : (
          <div className="space-y-3 mt-1">
            {script.scenes.map((scene) => (
              <SceneCard key={scene.id} scene={scene} />
            ))}
            <div className="pt-2 border-t border-edge space-y-1">
              <p className="text-xs text-sub leading-relaxed">
                <span className="font-medium">Voiceover</span> (~{script.estimated_duration_sec}s ·{' '}
                {script.tone}):{' '}
                <span className="text-dim">{script.full_voiceover_text}</span>
              </p>
              <p className="text-xs text-sub">
                <span className="font-medium">CTA:</span>{' '}
                <span className="text-dim">{script.cta_text}</span>
              </p>
              <p className="text-[10px] text-sub">Source: {script.source}</p>
            </div>
          </div>
        )}
      </Section>

      {/* ── Meta footer ────────────────────────────────────────────────────── */}
      <div className="text-[10px] text-sub pb-4">
        Created {fmtDate(campaign.created_at)}
        {campaign.updated_at && campaign.updated_at !== campaign.created_at && (
          <> · Updated {fmtDate(campaign.updated_at)}</>
        )}
      </div>
    </div>
  );
}
