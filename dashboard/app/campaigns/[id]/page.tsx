import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

// T-14 will implement the full campaign workspace with approve/reject/edit flow.

interface Props {
  params: Promise<{ id: string }>;
}

export default async function CampaignDetailPage({ params }: Props) {
  const { id } = await params;

  return (
    <div className="max-w-4xl space-y-4">
      <Link
        href="/campaigns"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 focus:outline-none focus:underline"
      >
        <ArrowLeft size={14} aria-hidden="true" />
        Back to queue
      </Link>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <p className="text-sm text-gray-500">
          Campaign detail workspace for{' '}
          <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">{id}</code> —
          full approval flow coming in T-14.
        </p>
      </div>
    </div>
  );
}
