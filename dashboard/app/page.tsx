import Link from 'next/link';
import { ClipboardList, CheckCircle, Film, Send } from 'lucide-react';

const STATUS_CARDS = [
  {
    label: 'Pending Review',
    value: '–',
    icon: ClipboardList,
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    desc: 'Awaiting CRM manager approval',
  },
  {
    label: 'Approved',
    value: '–',
    icon: CheckCircle,
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    desc: 'Ready for video generation',
  },
  {
    label: 'Generating',
    value: '–',
    icon: Film,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    desc: 'Runway pipeline in progress',
  },
  {
    label: 'Sent',
    value: '–',
    icon: Send,
    color: 'text-gray-600',
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    desc: 'Delivered to player',
  },
] as const;

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-5xl">
      {/* Status summary */}
      <section aria-labelledby="status-heading">
        <h2
          id="status-heading"
          className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3"
        >
          Pipeline Status
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {STATUS_CARDS.map(({ label, value, icon: Icon, color, bg, border, desc }) => (
            <div
              key={label}
              className={`${bg} ${border} border rounded-lg p-4 flex flex-col gap-2`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium text-gray-600 truncate">{label}</span>
                <Icon size={15} className={`${color} flex-none`} aria-hidden="true" />
              </div>
              <p className={`text-2xl font-bold ${color}`} aria-label={`${label}: ${value}`}>
                {value}
              </p>
              <p className="text-xs text-gray-500 truncate">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Approval queue preview */}
      <section aria-labelledby="queue-heading">
        <div className="flex items-center justify-between mb-3">
          <h2
            id="queue-heading"
            className="text-xs font-semibold text-gray-500 uppercase tracking-wider"
          >
            Approval Queue
          </h2>
          <Link
            href="/campaigns"
            className="text-xs text-blue-600 hover:text-blue-700 font-medium focus:outline-none focus:underline"
          >
            View all →
          </Link>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          {/* Table header */}
          <div
            className="grid grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto] gap-3 px-4 py-2.5 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide"
            aria-hidden="true"
          >
            <span>Player</span>
            <span>Cohort</span>
            <span>Risk</span>
            <span>LTV</span>
            <span>Created</span>
            <span className="w-20">Actions</span>
          </div>

          {/* Empty state */}
          <div className="py-16 flex flex-col items-center gap-3 text-center px-6">
            <ClipboardList size={28} className="text-gray-300" aria-hidden="true" />
            <p className="text-sm font-medium text-gray-500">No campaigns pending review</p>
            <p className="text-xs text-gray-400 max-w-xs">
              Run <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">POST /agent/scan</code> to
              classify dormant players and generate campaign drafts.
            </p>
          </div>
        </div>
      </section>

      {/* Quick actions */}
      <section aria-labelledby="actions-heading">
        <h2
          id="actions-heading"
          className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3"
        >
          Quick Start
        </h2>
        <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
          {[
            {
              step: '1',
              title: 'Run agent scan',
              desc: 'POST /agent/scan — classify dormant players and create campaign drafts',
            },
            {
              step: '2',
              title: 'Review approval queue',
              desc: 'Review, edit, and approve or reject campaign drafts',
              href: '/campaigns',
            },
            {
              step: '3',
              title: 'Video generation',
              desc: 'Approved campaigns trigger Runway video pipeline automatically',
            },
            {
              step: '4',
              title: 'Monitor metrics',
              desc: 'Track reactivation rates and ROI on the Metrics page',
              href: '/metrics',
            },
          ].map(({ step, title, desc, href }) => (
            <div key={step} className="flex items-start gap-4 px-4 py-3">
              <span className="flex-none w-6 h-6 rounded-full bg-gray-100 text-gray-500 text-xs font-semibold flex items-center justify-center mt-0.5">
                {step}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {href ? (
                    <Link href={href} className="hover:text-blue-600 focus:outline-none focus:underline">
                      {title}
                    </Link>
                  ) : (
                    title
                  )}
                </p>
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
