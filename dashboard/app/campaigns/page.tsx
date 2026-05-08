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

type StatusTab = null | 'approved' | 'rejected';

// null → no param → API returns draft+pending_approval (queue default)
const STATUS_TABS: { value: StatusTab; label: string }[] = [
  { value: null, label: 'Queue' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
];

// ── Visual helpers ────────────────────────────────────────────────────────

const COHORT_CHIP: Record<string, string> = {
  vip_at_risk: 'bg-purple-100 text-purple-800',
  high_value_dormant: 'bg-red-100 text-red-700',
  lapsed_loyal: 'bg-amber-100 text-amber-800',
  post_event: 'bg-blue-100 text-blue-700',
  first_deposit_no_return: 'bg-teal-100 text-teal-700',
  casual_dormant: 'bg-gray-100 text-gray-600',
};

const STATUS_CHIP: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  pending_approval: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-600',
  generating: 'bg-yellow-100 text-yellow-700',
  generation_failed: 'bg-red-100 text-red-600',
  ready: 'bg-green-100 text-green-700',
  ready_blocked_delivery: 'bg-orange-100 text-orange-700',
  delivered: 'bg-teal-100 text-teal-700',
  converted: 'bg-emerald-100 text-emerald-800',
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
  if (score >= 70) return 'text-red-600 font-semibold';
  if (score >= 40) return 'text-amber-600 font-medium';
  return 'text-green-600';
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
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
                  active
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50',
                ].join(' ')}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Cohort select */}
        <div className="flex items-center gap-1.5">
          <Filter size={13} className="text-gray-400 flex-none" aria-hidden="true" />
          <label htmlFor="cohort-filter" className="sr-only">
            Filter by cohort
          </label>
          <select
            id="cohort-filter"
            value={cohortFilter}
            onChange={(e) => setCohortFilter(e.target.value)}
            className="text-xs border border-gray-200 rounded px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          <label htmlFor="risk-min" className="text-xs text-gray-500 whitespace-nowrap">
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
            className="w-16 text-xs border border-gray-200 rounded px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Count + refresh */}
        <div className="ml-auto flex items-center gap-2">
          {!isLoading && !isError && (
            <span className="text-xs text-gray-400">
              {items.length} item{items.length !== 1 ? 's' : ''}
            </span>
          )}
          <button
            type="button"
            onClick={() => void refetch()}
            disabled={isFetching}
            aria-label="Refresh queue"
            className="p-1.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-40 transition-colors"
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
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[680px]">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {(
                  ['Player', 'Cohort', 'Risk', 'Offer', 'Status', 'Created', ''] as const
                ).map((h, i) => (
                  <th
                    key={i}
                    scope="col"
                    className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                  >
                    {h || <span className="sr-only">Review</span>}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-14 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Loader2
                        size={24}
                        className="text-blue-400 animate-spin"
                        aria-hidden="true"
                      />
                      <span className="text-xs text-gray-400">Loading campaigns…</span>
                    </div>
                  </td>
                </tr>
              ) : isError ? (
                <tr>
                  <td colSpan={7} className="py-12">
                    <div className="flex flex-col items-center gap-2 text-center px-6">
                      <AlertCircle
                        size={24}
                        className="text-red-400"
                        aria-hidden="true"
                      />
                      <p className="text-sm font-medium text-red-600">
                        Failed to load queue
                      </p>
                      <p className="text-xs text-gray-400 max-w-xs">
                        {error instanceof Error ? error.message : 'Unknown error'}
                      </p>
                      <button
                        type="button"
                        onClick={() => void refetch()}
                        className="mt-1 text-xs text-blue-600 hover:underline focus:outline-none focus:ring-1 focus:ring-blue-500 rounded"
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
                        className="text-gray-300"
                        aria-hidden="true"
                      />
                      <p className="text-sm font-medium text-gray-500">Queue is empty</p>
                      <p className="text-xs text-gray-400 max-w-xs">
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
                        'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500',
                        isSelected ? 'bg-blue-50' : 'hover:bg-gray-50',
                      ].join(' ')}
                    >
                      {/* Player */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-xs font-medium text-gray-900">
                          {item.first_name}
                        </div>
                        <div className="text-xs text-gray-400">
                          {item.country} · {item.currency}
                        </div>
                      </td>

                      {/* Cohort */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={[
                            'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                            COHORT_CHIP[item.cohort] ?? 'bg-gray-100 text-gray-600',
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
                        <span className="text-xs text-gray-700 truncate block">
                          {parseOfferLabel(item.offer_json)}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={[
                            'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                            STATUS_CHIP[item.status] ?? 'bg-gray-100 text-gray-600',
                          ].join(' ')}
                        >
                          {STATUS_LABEL[item.status] ?? item.status}
                        </span>
                      </td>

                      {/* Created */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-xs text-gray-400">
                          {fmtDate(item.created_at)}
                        </span>
                      </td>

                      {/* Arrow */}
                      <td className="px-4 py-3 w-8 text-gray-300 text-right">›</td>
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
