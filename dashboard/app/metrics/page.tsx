import { BarChart2 } from 'lucide-react';

// T-29 will implement the full metrics dashboard with recharts (already installed).
// Expected: big numbers row, funnel chart, cohort table, ROI calculator.

export default function MetricsPage() {
  return (
    <div className="max-w-5xl space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg py-16 flex flex-col items-center gap-3 text-center px-6">
        <BarChart2 size={28} className="text-gray-300" aria-hidden="true" />
        <p className="text-sm font-medium text-gray-500">Metrics dashboard</p>
        <p className="text-xs text-gray-400 max-w-xs">
          Full implementation in T-29. Will show reactivation rates, funnel, cohort breakdown,
          and ROI calculator backed by{' '}
          <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">
            GET /metrics/dashboard
          </code>
          .
        </p>
      </div>
    </div>
  );
}
