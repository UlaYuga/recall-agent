'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ClipboardList, Filter, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { approval, type QueueItem, type QueueFilters, type OfferData } from '../../lib/api';
import { CampaignPanel } from '../../components/CampaignPanel';

// ── Constants ─────────────────────────────────────────────────────────────

const ALL_COHORTS = [
  'casual_dormant',
  'high_value_dormant',
  'post_event',
  'first_deposit_no_return',
  'vip_at_risk',
  'lapsed_loyal',
] as const;

type StatusTab = null | 'all' | 'approved' | 'rejected';

// null → no param → API returns draft+pending_approval (queue default)
const STATUS_TABS: { value: StatusTab; label: string }[] = [
  { value: null, label: 'Pending' },
  { value: 'all', label: 'All' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
];

// ── Visual helpers ────────────────────────────────────────────────────────

const COHORT_CHIP: Record<string, string> = {
  vip_at_risk:              'bg-accent/10 text-accent',
  high_value_dormant:       'bg-fail/10 text-fail',
  lapsed_loyal:             'bg-warn/10 text-warn',
  post_event:               'bg-info/10 text-info',
  first_deposit_no_return:  'bg-pass/10 text-pass',
  casual_dormant:           'bg-line text-dim',
};

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

function cohortLabel(c: string): string {
  return c.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

function riskClass(score: number): string {
  if (score >= 70) return 'text-fail font-semibold';
  if (score >= 40) return 'text-warn font-medium';
  return 'text-pass';
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function parseOfferLabel(json: string | null): string {
  if (!json) return '—';
  try {
    const d = JSON.parse(json) as OfferData;
    return d.label ?? '—';
  } catch {
    return '—';
  }
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function CampaignsPage() {
  const [statusTab, setStatusTab] = useState<StatusTab>(null);
  const [cohortFilter, setCohortFilter] = useState('');
  const [riskMin, setRiskMin] = useState<number | ''>('');
  const [selected, setSelected] = useState<QueueItem | null>(null);

  const filters: QueueFilters = {
    status: statusTab ?? undefined,
    cohort: cohortFilter || undefined,
    risk_score_min: riskMin !== '' ? riskMin : undefined,
  };

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['approval-queue', filters],
    queryFn: () => approval.queue(filters),
  });

  const items = data ?? [];

  return (
    <div className="space-y-3 max-w-7xl">
      {/* ── Toolbar ──────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Status tabs */}
        <div className="flex gap-1" role="group" aria-label="Status filter">
          {STATUS_TABS.map((tab) => {
            const active = statusTab === tab.value;
            return (
              <button
                key={String(tab.value)}
                type="button"
                onClick={() => setStatusTab(tab.value)}
                aria-pressed={active}
                className={[
                  'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-accent',
                  active
                    ? 'bg-accent text-ink font-semibold'
                    : 'bg-char border border-edge text-dim hover:bg-graph',
                ].join(' ')}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Cohort select */}
        <div className="flex items-center gap-1.5">
          <Filter size={13} className="text-sub flex-none" aria-hidden="true" />
          <label htmlFor="cohort-filter" className="sr-only">
            Filter by cohort
          </label>
          <select
            id="cohort-filter"
            value={cohortFilter}
            onChange={(e) => setCohortFilter(e.target.value)}
            className="text-xs border border-edge rounded px-2 py-1.5 bg-char text-dim focus:outline-none focus:ring-2 focus:ring-accent"
          >
            <option value="">All cohorts</option>
            {ALL_COHORTS.map((c) => (
              <option key={c} value={c}>
                {cohortLabel(c)}
              </option>
            ))}
          </select>
        </div>

        {/* Min risk */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="risk-min" className="text-xs text-sub whitespace-nowrap">
            Min risk
          </label>
          <input
            id="risk-min"
            type="number"
            min={0}
            max={100}
            step={5}
            placeholder="0"
            value={riskMin}
            onChange={(e) =>
              setRiskMin(e.target.value === '' ? '' : Number(e.target.value))
            }
            className="w-16 text-xs border border-edge rounded px-2 py-1.5 bg-char text-dim focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        {/* Count + refresh */}
        <div className="ml-auto flex items-center gap-2">
          {!isLoading && !isError && (
            <span className="text-xs text-sub">
              {items.length} item{items.length !== 1 ? 's' : ''}
            </span>
          )}
          <button
            type="button"
            onClick={() => void refetch()}
            disabled={isFetching}
            aria-label="Refresh queue"
            className="p-1.5 rounded text-sub hover:text-dim hover:bg-graph focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-40 transition-colors"
          >
            <RefreshCw
              size={14}
              className={isFetching ? 'animate-spin' : ''}
              aria-hidden="true"
            />
          </button>
        </div>
      </div>

      {/* ── Table ────────────────────────────────────────────────── */}
      <div className="bg-graph border border-edge rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[680px]">
            <thead>
              <tr className="bg-ink border-b border-edge">
                {(
                  ['Player', 'Cohort', 'Risk', 'Offer', 'Status', 'Created', ''] as const
                ).map((h, i) => (
                  <th
                    key={i}
                    scope="col"
                    className="text-left px-4 py-2.5 text-xs font-semibold text-sub uppercase tracking-wide whitespace-nowrap"
                  >
                    {h || <span className="sr-only">Review</span>}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody className="divide-y divide-edge">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-14 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2
                        size={24}
                        className="text-info animate-spin"
                        aria-hidden="true"
                      />
                      <span className="text-xs text-sub">Loading campaigns…</span>
                    </div>
                  </td>
                </tr>
              ) : isError ? (
                <tr>
                  <td colSpan={7} className="py-12">
                    <div className="flex flex-col items-center gap-2 text-center px-6">
                      <AlertCircle
                        size={24}
                        className="text-fail"
                        aria-hidden="true"
                      />
                      <p className="text-sm font-medium text-fail">
                        Failed to load queue
                      </p>
                      <p className="text-xs text-sub max-w-xs">
                        {error instanceof Error ? error.message : 'Unknown error'}
                      </p>
                      <button
                        type="button"
                        onClick={() => void refetch()}
                        className="mt-1 text-xs text-accent hover:underline focus:outline-none focus:ring-1 focus:ring-accent rounded"
                      >
                        Retry
                      </button>
                    </div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16">
                    <div className="flex flex-col items-center gap-3 text-center px-6">
                      <ClipboardList
                        size={28}
                        className="text-mute"
                        aria-hidden="true"
                      />
                      <p className="text-sm font-medium text-dim">Queue is empty</p>
                      <p className="text-xs text-sub max-w-xs">
                        POST /agent/scan to generate campaign drafts, then they will
                        appear here.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const isSelected = selected?.campaign_id === item.campaign_id;
                  return (
                    <tr
                      key={item.campaign_id}
                      onClick={() => setSelected(item)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelected(item);
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`Review campaign for ${item.first_name}`}
                      aria-pressed={isSelected}
                      className={[
                        'cursor-pointer transition-colors',
                        'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-accent',
                        isSelected ? 'bg-graph' : 'hover:bg-ink',
                      ].join(' ')}
                    >
                      {/* Player */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-xs font-medium text-text">
                          {item.first_name}
                        </div>
                        <div className="text-xs text-sub">
                          {item.country} · {item.currency}
                        </div>
                      </td>

                      {/* Cohort */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={[
                            'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                            COHORT_CHIP[item.cohort] ?? 'bg-line text-dim',
                          ].join(' ')}
                        >
                          {cohortLabel(item.cohort)}
                        </span>
                      </td>

                      {/* Risk */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={['text-xs tabular-nums', riskClass(item.risk_score)].join(
                            ' '
                          )}
                        >
                          {Math.round(item.risk_score)}
                        </span>
                      </td>

                      {/* Offer */}
                      <td className="px-4 py-3 max-w-[160px]">
                        <span className="text-xs text-dim truncate block">
                          {parseOfferLabel(item.offer_json)}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={[
                            'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                            STATUS_CHIP[item.status] ?? 'bg-line text-dim',
                          ].join(' ')}
                        >
                          {STATUS_LABEL[item.status] ?? item.status}
                        </span>
                      </td>

                      {/* Created */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-xs text-sub">
                          {fmtDate(item.created_at)}
                        </span>
                      </td>

                      {/* Arrow */}
                      <td className="px-4 py-3 w-8 text-mute text-right">›</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Side panel ───────────────────────────────────────────── */}
      {selected && (
        <CampaignPanel
          item={selected}
          onClose={() => setSelected(null)}
          onMutated={() => {
            setSelected(null);
            void refetch();
          }}
        />
      )}
    </div>
  );
}
