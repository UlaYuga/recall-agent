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
    <div className="flex h-screen overflow-hidden bg-char">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-graph focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-text focus:ring-2 focus:ring-accent"
      >
        Skip to main content
      </a>

      {/* Sidebar — hidden on mobile, visible on sm+ */}
      <aside
        className="hidden sm:flex w-52 flex-none bg-ink flex-col"
        aria-label="Sidebar"
      >
        {/* Brand */}
        <div className="px-4 py-4 border-b border-edge">
          <Link
            href="/"
            className="flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-accent rounded"
          >
            <Zap size={16} className="text-accent flex-none" aria-hidden="true" />
            <span className="font-semibold text-text text-sm tracking-tight">Recall</span>
          </Link>
          <p className="text-xs text-sub mt-0.5 pl-6">CRM Dashboard</p>
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
                  'focus:outline-none focus:ring-2 focus:ring-accent',
                  active
                    ? 'bg-graph text-text'
                    : 'text-sub hover:bg-char hover:text-dim',
                ].join(' ')}
              >
                <Icon size={15} aria-hidden="true" className="flex-none" />
                <span className="truncate">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer: API URL */}
        <div className="px-4 py-3 border-t border-edge">
          <p className="text-xs text-mute truncate" title="Backend API URL">
            {process.env.NEXT_PUBLIC_API_URL ?? 'localhost:8000'}
          </p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex-none h-12 bg-ink border-b border-edge flex items-center px-4 sm:px-6 gap-3">
          {/* Brand mark — only visible on mobile where sidebar is hidden */}
          <Link
            href="/"
            className="sm:hidden flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-accent rounded flex-none"
            aria-label="Recall home"
          >
            <Zap size={14} className="text-accent flex-none" aria-hidden="true" />
            <span className="font-semibold text-text text-sm">Recall</span>
          </Link>

          <h1 className="text-sm font-semibold text-text flex-1 truncate">
            {getPageTitle(pathname)}
          </h1>

          <div className="flex items-center gap-4 flex-none">
            <span
              className="hidden sm:inline-flex items-center gap-1.5 text-xs text-sub"
              aria-label="Backend status"
            >
              <span className="w-2 h-2 rounded-full bg-mute flex-none" aria-hidden="true" />
              Backend
            </span>
            <span className="text-xs text-sub hidden sm:inline">CRM Manager</span>
          </div>
        </header>

        {/* Content — add bottom padding on mobile so content clears the bottom nav */}
        <main
          id="main-content"
          className="flex-1 overflow-auto p-4 sm:p-6 pb-20 sm:pb-6"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>

      {/* Mobile bottom navigation — only visible below sm breakpoint */}
      <nav
        className="sm:hidden fixed bottom-0 inset-x-0 z-30 bg-ink border-t border-edge flex"
        aria-label="Mobile navigation"
      >
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={[
                'flex-1 flex flex-col items-center gap-0.5 py-2.5 text-center',
                'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-accent',
                'transition-colors',
                active ? 'text-text' : 'text-sub',
              ].join(' ')}
            >
              <Icon size={18} aria-hidden="true" className="flex-none" />
              <span className="text-[10px] font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
