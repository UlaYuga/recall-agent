export default function SettingsPage() {
  return (
    <div className="max-w-xl space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
        <div className="px-4 py-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Environment
          </p>
          <dl className="space-y-2">
            {[
              { key: 'NEXT_PUBLIC_API_URL', value: process.env.NEXT_PUBLIC_API_URL ?? '(not set — defaults to localhost:8000)' },
            ].map(({ key, value }) => (
              <div key={key} className="flex gap-3 text-sm">
                <dt className="font-mono text-xs text-gray-500 flex-none w-52 truncate">{key}</dt>
                <dd className="text-gray-800 truncate min-w-0">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="px-4 py-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Auth
          </p>
          <p className="text-xs text-gray-500">
            Single-manager PoC auth via{' '}
            <code className="bg-gray-100 px-1 py-0.5 rounded font-mono">
              NEXT_PUBLIC_DEMO_MANAGER_PASSWORD
            </code>
            . Set in <code className="bg-gray-100 px-1 py-0.5 rounded font-mono">.env.local</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
