import { ClipboardList } from 'lucide-react';

// T-13 will implement the full queue with API wiring (/approval/queue).
// This scaffold shows the intended table structure and empty/loading states.

export default function CampaignsPage() {
  return (
    <div className="space-y-4 max-w-5xl">
      {/* Filters bar — scaffold */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex gap-1">
          {(['All', 'Pending', 'Approved', 'Rejected'] as const).map((f) => (
            <button
              key={f}
              className={[
                'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
                f === 'All'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50',
              ].join(' ')}
              aria-pressed={f === 'All'}
              disabled
            >
              {f}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-gray-400 italic">API wiring in T-13</span>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Player
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Cohort
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Risk
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Offer
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Status
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Created
              </th>
              <th className="px-4 py-2.5 w-24">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={7} className="py-16">
                <div className="flex flex-col items-center gap-3 text-center px-6">
                  <ClipboardList size={28} className="text-gray-300" aria-hidden="true" />
                  <p className="text-sm font-medium text-gray-500">Queue is empty</p>
                  <p className="text-xs text-gray-400 max-w-xs">
                    POST /agent/scan to generate campaign drafts, then they will appear here.
                  </p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
