'use client';

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'recall_auth';
// Wire to NEXT_PUBLIC_DEMO_MANAGER_PASSWORD at build time; falls back to "demo" for local dev.
const REQUIRED_PW = process.env.NEXT_PUBLIC_DEMO_MANAGER_PASSWORD ?? 'demo';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setAuthed(localStorage.getItem(STORAGE_KEY) === '1');
  }, []);

  // Avoid hydration mismatch — render nothing until client confirms state.
  if (authed === null) return null;

  if (!authed) {
    return (
      <div className="min-h-screen bg-char flex items-center justify-center p-4">
        <div className="bg-graph border border-edge rounded-lg p-8 w-full max-w-sm">
          <div className="mb-6">
            <h1 className="text-lg font-semibold text-text tracking-tight">Recall</h1>
            <p className="text-sm text-sub mt-0.5">CRM Manager Access</p>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (password === REQUIRED_PW) {
                localStorage.setItem(STORAGE_KEY, '1');
                setAuthed(true);
              } else {
                setError('Incorrect password');
              }
            }}
          >
            <label
              className="block text-sm font-medium text-dim mb-1"
              htmlFor="pw"
            >
              Password
            </label>
            <input
              id="pw"
              name="manager-password"
              type="password"
              autoComplete="current-password"
              className="w-full border border-edge rounded px-3 py-2 text-sm bg-ink text-text focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError('');
              }}
            />
            {error && (
              <p className="text-fail text-xs mt-1" role="alert">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="mt-4 w-full bg-accent hover:bg-accent/80 text-ink text-sm font-semibold py-2 rounded focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
            >
              Sign in
            </button>
          </form>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
