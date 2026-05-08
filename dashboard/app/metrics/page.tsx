'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  metrics,
  type MetricsDashboard,
  type MetricsCohortRow,
} from '../../lib/api';

// ── Formatters ────────────────────────────────────────────────────────────────

const fmtInt = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const fmtPct = (v: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'percent',
    maximumFractionDigits: 1,
  }).format(v);
const fmtUSD = (v: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(v);
const fmtX = (v: number) => `${v.toFixed(2)}×`;

// ── ROI Calculator ────────────────────────────────────────────────────────────

interface RoiParams {
  batch_size: number;
  baseline_rate: number;
  uplift: number;
  value_60d: number;
  cost_per_player: number;
}

const SCENARIOS: Record<string, RoiParams> = {
  conservative: { batch_size: 10000, baseline_rate: 0.05, uplift: 0.2, value_60d: 40, cost_per_player: 0.25 },
  base:         { batch_size: 10000, baseline_rate: 0.07, uplift: 0.3, value_60d: 58, cost_per_player: 0.25 },
  aggressive:   { batch_size: 10000, baseline_rate: 0.1,  uplift: 0.5, value_60d: 85, cost_per_player: 0.25 },
};

function calcROI(p: RoiParams) {
  const incr = p.batch_size * p.baseline_rate * p.uplift;
  const revenue = incr * p.value_60d;
  const cost = p.batch_size * p.cost_per_player;
  const net = revenue - cost;
  const roi = cost > 0 ? net / cost : 0;
  const monthly_net = net / 2;
  const payback_months = monthly_net > 0 ? cost / monthly_net : null;
  return {
    incr: Math.round(incr),
    revenue,
    cost,
    net,
    roi,
    payback_months,
    annual_net: net * 12,
    annual_cost: cost * 12,
  };
}

// ── Cohort display labels ─────────────────────────────────────────────────────

const COHORT_LABEL: Record<string, string> = {
  high_value_dormant:       'High Value',
  casual_dormant:           'Casual',
  post_event:               'Post Event',
  first_deposit_no_return:  '1st Dep. No Return',
  lapsed_loyal:             'Lapsed Loyal',
  vip_at_risk:              'VIP At Risk',
};

function cohortLabel(c: string): string {
  return COHORT_LABEL[c] ?? c.replace(/_/g, ' ');
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-graph border border-edge rounded p-4">
      <div className="text-xs text-sub font-medium mb-1 leading-tight">{label}</div>
      <div className="text-2xl font-semibold text-text tabular-nums leading-none">
        {value}
      </div>
      {sub && <div className="text-xs text-sub mt-1">{sub}</div>}
    </div>
  );
}

// ── Slider row ────────────────────────────────────────────────────────────────

function SliderRow({
  label, value, min, max, step, display, onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display: string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-baseline">
        <span className="text-xs text-sub">{label}</span>
        <span className="text-xs font-mono font-medium text-text tabular-nums">{display}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 accent-accent cursor-pointer"
        aria-label={label}
      />
    </div>
  );
}

// ── Cohort table ──────────────────────────────────────────────────────────────

function CohortTable({ rows }: { rows: MetricsCohortRow[] }) {
  if (rows.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-sm text-sub">
        No campaigns yet
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-edge">
            {['Cohort', 'Total', 'Approved', 'Delivered', 'Conv.', 'Rate'].map((h, i) => (
              <th
                key={h}
                className={`py-1.5 font-medium text-sub ${i === 0 ? 'text-left pr-3' : 'text-right px-2'}`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const rate = row.delivered > 0 ? row.converted / row.delivered : 0;
            return (
              <tr key={row.cohort} className="border-b border-edge hover:bg-ink">
                <td className="py-1.5 pr-3 text-text font-medium">
                  {cohortLabel(row.cohort)}
                </td>
                <td className="py-1.5 px-2 text-right tabular-nums text-dim">{row.count}</td>
                <td className="py-1.5 px-2 text-right tabular-nums text-dim">{row.approved}</td>
                <td className="py-1.5 px-2 text-right tabular-nums text-dim">{row.delivered}</td>
                <td className="py-1.5 px-2 text-right tabular-nums text-dim">{row.converted}</td>
                <td className="py-1.5 pl-2 text-right tabular-nums text-dim">{fmtPct(rate)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function MetricsPage() {
  const { data, isLoading, isError, error } = useQuery<MetricsDashboard>({
    queryKey: ['metrics-dashboard'],
    queryFn: metrics.dashboard,
    refetchInterval: 30_000,
  });

  const [scenario, setScenario] = useState<string>('base');
  const [params, setParams] = useState<RoiParams>(SCENARIOS.base);

  function applyScenario(key: string) {
    setScenario(key);
    setParams(SCENARIOS[key]);
  }

  function setParam(k: keyof RoiParams, v: number) {
    setScenario('custom');
    setParams((p) => ({ ...p, [k]: v }));
  }

  const roi = calcROI(params);

  if (isLoading) {
    return (
      <div className="max-w-6xl space-y-4">
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-20 bg-graph rounded animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-graph rounded animate-pulse" />
        <div className="h-48 bg-graph rounded animate-pulse" />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className="bg-fail/10 border border-fail/20 rounded p-4 text-sm text-fail"
        role="alert"
      >
        Failed to load metrics:{' '}
        {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  if (!data) return null;

  const { funnel, kpis, cohort_breakdown } = data;
  const isEmpty = funnel.scanned === 0;

  const funnelData = [
    { stage: 'Scanned',   count: funnel.scanned },
    { stage: 'Approved',  count: funnel.approved },
    { stage: 'Delivered', count: funnel.delivered },
    { stage: 'Played',    count: funnel.played },
    { stage: 'Clicked',   count: funnel.clicked },
    { stage: 'Deposited', count: funnel.deposited },
  ];

  return (
    <div className="max-w-6xl space-y-6">

      {/* ── KPI row ─────────────────────────────────────────────────────────── */}
      <section aria-label="Key metrics">
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          <Stat label="Players Analyzed"  value={fmtInt.format(kpis.total_players)} />
          <Stat label="Campaigns Created" value={fmtInt.format(kpis.campaigns_created)} />
          <Stat
            label="Approval Rate"
            value={fmtPct(kpis.approval_rate)}
            sub="approved / scanned"
          />
          <Stat label="Videos Delivered" value={fmtInt.format(kpis.videos_delivered)} />
          <Stat
            label="Avg CTR"
            value={fmtPct(kpis.avg_ctr)}
            sub="clicks / plays"
          />
          <Stat
            label="Reactivation Rate"
            value={fmtPct(kpis.reactivation_rate)}
            sub="converted / delivered"
          />
        </div>
      </section>

      {/* ── Funnel + Cohort table ──────────────────────────────────────────── */}
      <section aria-label="Funnel and cohort breakdown">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Funnel */}
          <div className="bg-graph border border-edge rounded p-4">
            <h2 className="text-xs font-semibold text-sub mb-3 uppercase tracking-wide">
              Reactivation Funnel
            </h2>
            {isEmpty ? (
              <div className="h-52 flex items-center justify-center text-sm text-sub">
                No campaigns yet — run{' '}
                <code className="mx-1 bg-line text-text px-1.5 py-0.5 rounded text-xs font-mono">
                  POST /agent/scan
                </code>{' '}
                to populate
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={228}>
                <BarChart
                  data={funnelData}
                  layout="vertical"
                  margin={{ top: 0, right: 40, bottom: 0, left: 76 }}
                >
                  <XAxis
                    type="number"
                    tick={{ fontSize: 10, fill: '#9a9aa1' }}
                    tickFormatter={(v: number) => fmtInt.format(v)}
                  />
                  <YAxis
                    dataKey="stage"
                    type="category"
                    width={76}
                    tick={{ fontSize: 11, fill: '#9a9aa1' }}
                  />
                  <Tooltip
                    formatter={(v: number) => [fmtInt.format(v), 'campaigns']}
                    contentStyle={{
                      background: '#15151a',
                      border: '1px solid #1d1d23',
                      color: '#ededee',
                      fontSize: 12,
                      borderRadius: '6px',
                    }}
                  />
                  <Bar dataKey="count" fill="#c5ff3d" radius={[0, 2, 2, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Cohort breakdown */}
          <div className="bg-graph border border-edge rounded p-4">
            <h2 className="text-xs font-semibold text-sub mb-3 uppercase tracking-wide">
              Cohort Breakdown
            </h2>
            <CohortTable rows={cohort_breakdown} />
          </div>

        </div>
      </section>

      {/* ── ROI Calculator ──────────────────────────────────────────────────── */}
      <section aria-label="ROI calculator">
        <div className="bg-graph border border-edge rounded p-4">

          <div className="flex flex-wrap items-baseline gap-3 mb-4">
            <h2 className="text-xs font-semibold text-sub uppercase tracking-wide">
              ROI Calculator
            </h2>
            <span
              className="text-xs text-sub border border-edge rounded px-1.5 py-0.5 cursor-help"
              title="Simulation based on industry benchmarks (Engagehut, Idomoo/Entain). Actual results vary by operator, market, and player segment."
            >
              Industry benchmarks
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

            {/* Inputs */}
            <div className="lg:col-span-3 space-y-5">
              {/* Scenario presets */}
              <div className="flex flex-wrap gap-2">
                {(['conservative', 'base', 'aggressive'] as const).map((key) => (
                  <button
                    key={key}
                    onClick={() => applyScenario(key)}
                    className={[
                      'px-3 py-1 text-xs font-medium rounded border transition-colors capitalize',
                      scenario === key
                        ? 'bg-accent text-ink border-accent font-semibold'
                        : 'bg-char text-dim border-edge hover:border-line',
                    ].join(' ')}
                  >
                    {key}
                  </button>
                ))}
                {scenario === 'custom' && (
                  <span className="self-center text-xs text-sub">custom</span>
                )}
              </div>

              {/* Sliders */}
              <div className="space-y-4">
                <SliderRow
                  label="Batch size (targeted players)"
                  value={params.batch_size}
                  min={100}
                  max={100000}
                  step={100}
                  display={fmtInt.format(params.batch_size)}
                  onChange={(v) => setParam('batch_size', v)}
                />
                <SliderRow
                  label="Baseline reactivation rate"
                  value={params.baseline_rate}
                  min={0.03}
                  max={0.15}
                  step={0.001}
                  display={fmtPct(params.baseline_rate)}
                  onChange={(v) => setParam('baseline_rate', v)}
                />
                <SliderRow
                  label="AI video uplift (relative)"
                  value={params.uplift}
                  min={0.1}
                  max={1.0}
                  step={0.01}
                  display={`+${Math.round(params.uplift * 100)}%`}
                  onChange={(v) => setParam('uplift', v)}
                />
                <SliderRow
                  label="60-day value per reactivated player"
                  value={params.value_60d}
                  min={20}
                  max={150}
                  step={1}
                  display={fmtUSD(params.value_60d)}
                  onChange={(v) => setParam('value_60d', v)}
                />
                <SliderRow
                  label="Cost per targeted player"
                  value={params.cost_per_player}
                  min={0.1}
                  max={0.5}
                  step={0.01}
                  display={fmtUSD(params.cost_per_player)}
                  onChange={(v) => setParam('cost_per_player', v)}
                />
              </div>
            </div>

            {/* Outputs */}
            <div className="lg:col-span-2 space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-ink rounded p-3">
                  <div className="text-xs text-sub mb-0.5">Incr. reactivated</div>
                  <div className="text-lg font-semibold tabular-nums text-text">
                    {fmtInt.format(roi.incr)}
                  </div>
                  <div className="text-xs text-sub">players</div>
                </div>
                <div className="bg-ink rounded p-3">
                  <div className="text-xs text-sub mb-0.5">Campaign cost</div>
                  <div className="text-lg font-semibold tabular-nums text-text">
                    {fmtUSD(roi.cost)}
                  </div>
                  <div className="text-xs text-sub">60-day window</div>
                </div>
                <div className={`rounded p-3 ${roi.net >= 0 ? 'bg-pass/10' : 'bg-fail/10'}`}>
                  <div className="text-xs text-sub mb-0.5">Net lift</div>
                  <div
                    className={`text-lg font-semibold tabular-nums ${
                      roi.net >= 0 ? 'text-pass' : 'text-fail'
                    }`}
                  >
                    {fmtUSD(roi.net)}
                  </div>
                  <div className="text-xs text-sub">revenue − cost</div>
                </div>
                <div className={`rounded p-3 ${roi.roi >= 0 ? 'bg-pass/10' : 'bg-fail/10'}`}>
                  <div className="text-xs text-sub mb-0.5">ROI</div>
                  <div
                    className={`text-lg font-semibold tabular-nums ${
                      roi.roi >= 0 ? 'text-pass' : 'text-fail'
                    }`}
                  >
                    {fmtX(roi.roi)}
                  </div>
                  <div className="text-xs text-sub">net / cost</div>
                </div>
              </div>

              <div className="bg-info/10 rounded p-3 space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-sub">Payback period</span>
                  <span className="font-medium text-text tabular-nums">
                    {roi.payback_months !== null
                      ? roi.payback_months < 1
                        ? `${Math.round(roi.payback_months * 30.5)} days`
                        : `${roi.payback_months.toFixed(1)} mo`
                      : '—'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-sub">Annual net lift (×12 batches)</span>
                  <span className="font-medium text-text tabular-nums">
                    {fmtUSD(roi.annual_net)}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-sub">Annual pipeline cost</span>
                  <span className="font-medium text-text tabular-nums">
                    {fmtUSD(roi.annual_cost)}
                  </span>
                </div>
              </div>

              <p className="text-xs text-sub leading-relaxed">
                Simulation based on industry benchmarks. Actual results vary by
                operator, market, and player segment.
              </p>
            </div>

          </div>
        </div>
      </section>

    </div>
  );
}
