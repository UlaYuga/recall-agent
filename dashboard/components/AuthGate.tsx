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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white border border-gray-200 rounded-lg p-8 w-full max-w-sm shadow-sm">
          <div className="mb-6">
            <h1 className="text-lg font-semibold text-gray-900">Recall</h1>
            <p className="text-sm text-gray-500 mt-0.5">CRM Manager Access</p>
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
              className="block text-sm font-medium text-gray-700 mb-1"
              htmlFor="pw"
            >
              Password
            </label>
            <input
              id="pw"
              name="manager-password"
              type="password"
              autoComplete="current-password"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError('');
              }}
            />
            {error && (
              <p className="text-red-600 text-xs mt-1" role="alert">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
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
