import type { Metadata } from 'next';
import './globals.css';
import { Providers } from '../components/Providers';
import { AppShell } from '../components/AppShell';
import { AuthGate } from '../components/AuthGate';

export const metadata: Metadata = {
  title: 'Recall Dashboard',
  description: 'Internal CRM approval and metrics dashboard for Recall',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AuthGate>
            <AppShell>{children}</AppShell>
          </AuthGate>
        </Providers>
      </body>
    </html>
  );
}
