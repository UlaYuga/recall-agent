'use client';

/**
 * /r/[campaign_id] — player-facing reactivation landing page.
 *
 * Fetches minimal campaign card from GET /public/r/{campaign_id}.
 * Tracks: play (once per session), CTA click, mock deposit.
 * Language: preferred_language from campaign; overridable via ?lang= param.
 *
 * States handled:
 *   loading | error | not_found | preparing | failed | ready
 */

import { useEffect, useRef, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { pickCopy, type ReactivationCopy } from '../../../content/reactivation';
import { trackPlay, trackClick, trackDeposit } from '../../../lib/tracking';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CampaignCard {
  campaign_id: string;
  status: string;
  cohort: string;
  first_name: string;
  preferred_language: string;
  currency: string;
  offer_json: string | null;
  video_url: string | null;
  poster_url: string | null;
}

interface OfferData {
  type: string;
  value: number;
  label: string;
  copy: string;
  terms: string;
  expiry_days: number;
  game_label: string | null;
}

type PageState = 'loading' | 'error' | 'not_found' | 'preparing' | 'failed' | 'ready';

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function resolveMediaUrl(url: string | null): string | null {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API_BASE}${url}`;
}

function parseOffer(json: string | null): OfferData | null {
  if (!json) return null;
  try {
    return JSON.parse(json) as OfferData;
  } catch {
    return null;
  }
}

function campaignPageState(status: string): PageState {
  if (['ready', 'ready_blocked_delivery', 'delivered', 'converted'].includes(status)) {
    return 'ready';
  }
  if (status === 'generation_failed') return 'failed';
  return 'preparing';
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Logo() {
  return (
    <a
      href="/"
      className="text-gold hover:text-gold-light font-bold text-xl tracking-tight transition-colors"
      aria-label="Recall home"
    >
      Recall
    </a>
  );
}

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-night text-prose flex flex-col">
      <header className="border-b border-night-600 bg-night/80 backdrop-blur-md px-4 py-3">
        <div className="mx-auto max-w-lg flex items-center justify-between">
          <Logo />
        </div>
      </header>
      <main className="flex-1 flex flex-col items-center justify-start px-4 py-8 sm:py-12">
        <div className="w-full max-w-lg">{children}</div>
      </main>
      <footer className="border-t border-night-600 px-4 py-4 text-center">
        <p className="text-xs text-prose-faint">Powered by Recall AI</p>
      </footer>
    </div>
  );
}

function StateCard({
  icon,
  headline,
  body,
}: {
  icon: string;
  headline: string;
  body: string;
}) {
  return (
    <div className="bg-night-800 border border-night-600 rounded-2xl p-8 text-center space-y-3">
      <div className="text-4xl" aria-hidden="true">{icon}</div>
      <h1 className="text-lg font-semibold text-prose">{headline}</h1>
      <p className="text-sm text-prose-muted leading-relaxed">{body}</p>
    </div>
  );
}

// ── Video player ──────────────────────────────────────────────────────────────

interface VideoPlayerProps {
  videoUrl: string | null;
  posterUrl: string | null;
  campaignId: string;
  altText: string;
}

function VideoPlayer({ videoUrl, posterUrl, campaignId, altText }: VideoPlayerProps) {
  const playTracked = useRef(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  function handlePlay() {
    if (!playTracked.current) {
      playTracked.current = true;
      const watched = videoRef.current ? Math.round(videoRef.current.currentTime) : 0;
      trackPlay(campaignId, watched);
    }
  }

  if (videoUrl) {
    return (
      <div className="relative rounded-xl overflow-hidden bg-black aspect-video shadow-card">
        <video
          ref={videoRef}
          src={videoUrl}
          poster={posterUrl ?? undefined}
          controls
          playsInline
          className="w-full h-full object-contain"
          aria-label={altText}
          onPlay={handlePlay}
        />
      </div>
    );
  }

  if (posterUrl) {
    return (
      <div className="relative rounded-xl overflow-hidden bg-night-700 aspect-video shadow-card">
        <img
          src={posterUrl}
          alt={altText}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <div className="text-prose-muted text-xs text-center px-4">
            {/* poster-only state — video not yet available */}
            <div className="w-12 h-12 rounded-full border-2 border-prose-muted/40 flex items-center justify-center mx-auto mb-2">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-prose-muted/60">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

// ── Offer card ────────────────────────────────────────────────────────────────

function OfferCard({ offer, c }: { offer: OfferData; c: ReactivationCopy }) {
  return (
    <div className="bg-night-800 border border-gold/30 rounded-xl p-5 space-y-3 shadow-gold">
      <div className="flex items-start gap-3">
        <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-gold/20 text-gold flex-none">
          {offer.type.replace(/_/g, ' ')}
        </span>
        <p className="text-sm font-semibold text-prose leading-snug">{offer.label}</p>
      </div>
      <p className="text-sm text-prose-muted leading-relaxed">{offer.copy}</p>
      <div className="flex flex-wrap gap-3 text-xs text-prose-faint pt-1 border-t border-night-600">
        <span>Expires in <span className="text-prose-muted font-medium">{offer.expiry_days} days</span></span>
        {offer.game_label && (
          <span>Game: <span className="text-prose-muted font-medium">{offer.game_label}</span></span>
        )}
      </div>
    </div>
  );
}

// ── Deposit form ──────────────────────────────────────────────────────────────

type DepositState = 'idle' | 'submitting' | 'success' | 'error';

interface DepositFormProps {
  campaignId: string;
  currency: string;
  c: ReactivationCopy;
}

function DepositForm({ campaignId, currency, c }: DepositFormProps) {
  const [amount, setAmount] = useState('');
  const [state, setState] = useState<DepositState>('idle');
  const [fieldError, setFieldError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = parseFloat(amount);
    if (!parsed || parsed < 10) {
      setFieldError(c.depositMin);
      return;
    }
    setFieldError('');
    setState('submitting');
    try {
      trackDeposit(campaignId, parsed, currency);
      await new Promise((r) => setTimeout(r, 600)); // brief UI feedback delay
      setState('success');
    } catch {
      setState('error');
    }
  }

  if (state === 'success') {
    return (
      <div className="bg-night-800 border border-green-500/30 rounded-xl p-5 text-center space-y-2">
        <div className="text-3xl" aria-hidden="true">🎉</div>
        <p className="text-sm font-semibold text-green-400">{c.depositSuccess}</p>
      </div>
    );
  }

  return (
    <div className="bg-night-800 border border-night-600 rounded-xl p-5 space-y-3">
      <h2 className="text-sm font-semibold text-prose">{c.depositHeadline}</h2>
      <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-3">
        <div>
          <label htmlFor="deposit-amount" className="block text-xs text-prose-muted mb-1">
            {c.depositAmountLabel} ({currency})
          </label>
          <div className="flex gap-2">
            <input
              id="deposit-amount"
              name="deposit_amount"
              type="number"
              inputMode="decimal"
              autoComplete="off"
              min="10"
              step="1"
              placeholder={c.depositAmountPlaceholder}
              value={amount}
              onChange={(e) => {
                setAmount(e.target.value);
                setFieldError('');
              }}
              className="flex-1 bg-night-700 border border-night-500 rounded-lg px-3 py-2 text-sm text-prose placeholder-prose-faint focus:outline-none focus:ring-2 focus:ring-gold/60 focus:border-gold/60"
              aria-describedby={fieldError ? 'deposit-error' : undefined}
            />
            <button
              type="submit"
              disabled={state === 'submitting'}
              className="px-4 py-2 rounded-lg text-sm font-semibold bg-gold text-night hover:bg-gold-light disabled:opacity-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gold"
            >
              {state === 'submitting' ? '…' : c.depositSubmit}
            </button>
          </div>
          {fieldError && (
            <p id="deposit-error" role="alert" className="text-xs text-red-400 mt-1">
              {fieldError}
            </p>
          )}
          {state === 'error' && (
            <p role="alert" className="text-xs text-red-400 mt-1">
              Something went wrong. Please try again.
            </p>
          )}
        </div>
      </form>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ReactivationPage() {
  const params = useParams<{ campaign_id: string }>();
  const searchParams = useSearchParams();
  const campaignId = params.campaign_id;
  const langParam = searchParams.get('lang') ?? undefined;

  const [card, setCard] = useState<CampaignCard | null>(null);
  const [pageState, setPageState] = useState<PageState>('loading');
  const [ctaClicked, setCtaClicked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setPageState('loading');

    fetch(`${API_BASE}/public/r/${encodeURIComponent(campaignId)}`)
      .then(async (res) => {
        if (cancelled) return;
        if (res.status === 404) {
          setPageState('not_found');
          return;
        }
        if (!res.ok) {
          setPageState('error');
          return;
        }
        const data = (await res.json()) as CampaignCard;
        if (cancelled) return;
        setCard(data);
        setPageState(campaignPageState(data.status));
      })
      .catch(() => {
        if (!cancelled) setPageState('error');
      });

    return () => {
      cancelled = true;
    };
  }, [campaignId]);

  // Derive copy from card language or URL param
  const c = pickCopy(card?.preferred_language ?? 'en', langParam);

  // ── Loading ─────────────────────────────────────────────────────────────────
  if (pageState === 'loading') {
    return (
      <PageShell>
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <div
            className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin"
            role="status"
            aria-label="Loading"
          />
          <p className="text-sm text-prose-muted">Loading your offer…</p>
        </div>
      </PageShell>
    );
  }

  // ── Not found ───────────────────────────────────────────────────────────────
  if (pageState === 'not_found') {
    return (
      <PageShell>
        <StateCard icon="🔗" headline={c.notFoundHeadline} body={c.notFoundBody} />
      </PageShell>
    );
  }

  // ── Error ───────────────────────────────────────────────────────────────────
  if (pageState === 'error') {
    return (
      <PageShell>
        <StateCard icon="⚠️" headline={c.errorHeadline} body={c.errorBody} />
      </PageShell>
    );
  }

  // ── Video failed ─────────────────────────────────────────────────────────────
  if (pageState === 'failed') {
    return (
      <PageShell>
        <StateCard icon="🎬" headline={c.failedHeadline} body={c.failedBody} />
      </PageShell>
    );
  }

  // ── Preparing (draft / pending / approved / generating) ──────────────────────
  if (pageState === 'preparing') {
    return (
      <PageShell>
        <div className="space-y-4">
          <div className="bg-night-800 border border-night-600 rounded-2xl p-8 text-center space-y-4">
            <div
              className="w-10 h-10 rounded-full border-2 border-gold border-t-transparent animate-spin mx-auto"
              aria-hidden="true"
            />
            <h1 className="text-lg font-semibold text-prose">{c.preparingHeadline}</h1>
            <p className="text-sm text-prose-muted leading-relaxed">{c.preparingBody}</p>
          </div>
          {/* Show poster if available while video is generating */}
          {card?.poster_url && (
            <div className="rounded-xl overflow-hidden bg-night-700 aspect-video shadow-card">
              <img
                src={resolveMediaUrl(card.poster_url) ?? ''}
                alt={c.videoUnavailableAlt}
                className="w-full h-full object-cover"
              />
            </div>
          )}
        </div>
      </PageShell>
    );
  }

  // ── Ready ────────────────────────────────────────────────────────────────────
  if (!card) return null;

  const offer = parseOffer(card.offer_json);
  const videoUrl = resolveMediaUrl(card.video_url);
  const posterUrl = resolveMediaUrl(card.poster_url);

  function handleCta() {
    trackClick(card!.campaign_id, 'main_cta');
    setCtaClicked(true);
  }

  return (
    <PageShell>
      <div className="space-y-5">
        {/* ── Welcome headline ─────────────────────────────────────── */}
        <div className="space-y-1">
          <h1 className="text-2xl sm:text-3xl font-bold text-prose leading-snug">
            {c.welcomeBack(card.first_name)}
          </h1>
          <p className="text-sm text-prose-muted">{c.yourOffer}</p>
        </div>

        {/* ── Video player ─────────────────────────────────────────── */}
        {(videoUrl || posterUrl) && (
          <div className="space-y-2">
            <p className="text-xs text-prose-muted">{c.watchVideo}</p>
            <VideoPlayer
              videoUrl={videoUrl}
              posterUrl={posterUrl}
              campaignId={card.campaign_id}
              altText={c.videoUnavailableAlt}
            />
          </div>
        )}

        {/* ── Offer ────────────────────────────────────────────────── */}
        {offer && <OfferCard offer={offer} c={c} />}

        {/* ── CTA / Thank-you / Deposit ─────────────────────────────── */}
        {!ctaClicked ? (
          <button
            type="button"
            onClick={handleCta}
            className="w-full py-3.5 rounded-xl text-base font-bold bg-cta-gradient text-white hover:opacity-90 active:scale-[0.98] transition-[opacity,transform] shadow-card focus:outline-none focus-visible:ring-2 focus-visible:ring-gold"
          >
            {c.ctaLabel}
          </button>
        ) : (
          <div className="space-y-4">
            <div className="bg-night-800 border border-gold/20 rounded-xl p-5 text-center space-y-1">
              <p className="text-base font-semibold text-gold">{c.thankYouHeadline}</p>
              <p className="text-sm text-prose-muted">{c.thankYouBody}</p>
            </div>
            <DepositForm
              campaignId={card.campaign_id}
              currency={card.currency}
              c={c}
            />
          </div>
        )}

        {/* ── Legal / terms ─────────────────────────────────────────── */}
        <p className="text-[11px] text-prose-faint leading-relaxed text-center">
          {c.termsNote}
        </p>
      </div>
    </PageShell>
  );
}
