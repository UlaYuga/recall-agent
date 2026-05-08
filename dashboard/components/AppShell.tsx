'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutGrid, BarChart2, Settings, Zap } from 'lucide-react';

const NAV_ITEMS = [
  { href: '/campaigns', label: 'Campaigns', icon: LayoutGrid },
  { href: '/metrics', label: 'Metrics', icon: BarChart2 },
  { href: '/settings', label: 'Settings', icon: Settings },
] as const;

function getPageTitle(pathname: string): string {
  if (pathname === '/') return 'Overview';
  if (pathname === '/campaigns') return 'Approval Queue';
  if (pathname.startsWith('/campaigns/')) return 'Campaign Detail';
  if (pathname === '/metrics') return 'Metrics';
  if (pathname === '/settings') return 'Settings';
  return 'Recall';
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-gray-900 focus:ring-2 focus:ring-blue-500"
      >
        Skip to main content
      </a>

      {/* Sidebar */}
      <aside
        className="w-52 flex-none bg-gray-900 flex flex-col"
        aria-label="Sidebar"
      >
        {/* Brand */}
        <div className="px-4 py-4 border-b border-gray-800">
          <Link
            href="/"
            className="flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-blue-400 rounded"
          >
            <Zap size={16} className="text-blue-400 flex-none" aria-hidden="true" />
            <span className="font-semibold text-white text-sm tracking-tight">Recall</span>
          </Link>
          <p className="text-xs text-gray-500 mt-0.5 pl-6">CRM Dashboard</p>
        </div>

        {/* Nav */}
        <nav
          className="flex-1 px-2 py-3 space-y-0.5"
          aria-label="Main navigation"
        >
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active =
              pathname === href || pathname.startsWith(href + '/');
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? 'page' : undefined}
                className={[
                  'flex items-center gap-2.5 px-3 py-2 rounded text-sm font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-blue-400',
                  active
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100',
                ].join(' ')}
              >
                <Icon size={15} aria-hidden="true" className="flex-none" />
                <span className="truncate">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer: API URL */}
        <div className="px-4 py-3 border-t border-gray-800">
          <p className="text-xs text-gray-600 truncate" title="Backend API URL">
            {process.env.NEXT_PUBLIC_API_URL ?? 'localhost:8000'}
          </p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex-none h-12 bg-white border-b border-gray-200 flex items-center px-6 gap-4">
          <h1 className="text-sm font-semibold text-gray-900 flex-1 truncate">
            {getPageTitle(pathname)}
          </h1>
          <div className="flex items-center gap-4 flex-none">
            <span
              className="inline-flex items-center gap-1.5 text-xs text-gray-500"
              aria-label="Backend status"
            >
              <span className="w-2 h-2 rounded-full bg-gray-300 flex-none" aria-hidden="true" />
              Backend
            </span>
            <span className="text-xs text-gray-500">CRM Manager</span>
          </div>
        </header>

        {/* Content */}
        <main
          id="main-content"
          className="flex-1 overflow-auto p-6"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
