/**
 * Landing page — server component.
 *
 * Language selection: ?lang=ru shows Russian copy, default is EN.
 * All content lives in /content/en.ts and /content/ru.ts.
 *
 * Background motion strategy:
 *   - Hero: CSS gradient animation (no media files required)
 *   - Demo section: video element pointing to /demo/hero.mp4 (not committed;
 *     drop the file into /public/demo/ to activate it)
 *   - No GIFs, no heavy 60fps assets.
 */
import type { Metadata } from "next";
import { en } from "../content/en";
import { ru } from "../content/ru";
import type { LandingContent } from "../content/en";

/* ── Metadata (dynamic for lang) ─────────────────────────────────────── */
export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<{ lang?: string }>;
}): Promise<Metadata> {
  const { lang } = await searchParams;
  const c = lang === "ru" ? ru : en;
  return { title: c.metaTitle, description: c.metaDescription };
}

/* ── Page ─────────────────────────────────────────────────────────────── */
export default async function LandingPage({
  searchParams,
}: {
  searchParams: Promise<{ lang?: string }>;
}) {
  const { lang } = await searchParams;
  const c: LandingContent = lang === "ru" ? ru : en;

  return (
    <div className="min-h-screen bg-night text-prose">
      <Nav c={c} />
      <Hero c={c} />
      <Pipeline c={c} />
      <DemoSection c={c} />
      <RoiSection c={c} />
      <SafetySection c={c} />
      <CtaSection c={c} />
      <Footer c={c} />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   NAV
═══════════════════════════════════════════════════════════════════════ */
function Nav({ c }: { c: LandingContent }) {
  return (
    <header className="sticky top-0 z-50 border-b border-night-600 bg-night/80 backdrop-blur-md">
      <div className="mx-auto max-w-5xl flex items-center justify-between px-4 sm:px-6 py-3">
        {/* Logo */}
        <a
          href="/"
          className="text-xl font-bold tracking-tight text-gold hover:text-gold-light transition-colors"
        >
          {c.logoLabel}
        </a>

        {/* Links */}
        <nav className="flex items-center gap-4 sm:gap-6 text-sm">
          <a
            href={c.langSwitchHref}
            className="text-prose-muted hover:text-gold transition-colors font-medium"
          >
            {c.langSwitch}
          </a>
          <a
            href="https://github.com/UlaYuga/recall-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="text-prose-muted hover:text-prose transition-colors"
          >
            {c.navGithub}
          </a>
          <a
            href={
              process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3001"
            }
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-gold/10 border border-gold/30 px-3 py-1.5 text-gold text-sm font-medium hover:bg-gold/20 transition-colors"
          >
            {c.navDashboard}
          </a>
        </nav>
      </div>
    </header>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   HERO
═══════════════════════════════════════════════════════════════════════ */
function Hero({ c }: { c: LandingContent }) {
  return (
    <section
      className="hero-animated-bg relative overflow-hidden"
      aria-label="Hero"
    >
      {/* Decorative glows */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-40 -left-32 w-96 h-96 rounded-full bg-accent/10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-10 right-0 w-80 h-80 rounded-full bg-gold/5 blur-3xl"
      />

      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-20 sm:py-28 lg:py-36">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-gold/30 bg-gold-subtle px-4 py-1.5 text-xs sm:text-sm text-gold mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse inline-block" />
          {c.badge}
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight tracking-tight mb-6">
          <span className="text-gold-shimmer">{c.heroHeadline}</span>
        </h1>

        {/* Subhead */}
        <p className="text-prose-muted text-lg sm:text-xl max-w-2xl leading-relaxed mb-10">
          {c.heroSubhead}
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap gap-4 mb-16">
          <a
            href="#pipeline"
            className="rounded-lg bg-gold px-6 py-3 text-night font-semibold text-sm sm:text-base hover:bg-gold-light transition-colors shadow-gold-sm"
          >
            {c.heroCta}
          </a>
          <a
            href="https://github.com/UlaYuga/recall-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-night-500 px-6 py-3 text-prose-muted text-sm sm:text-base hover:border-gold/50 hover:text-prose transition-colors"
          >
            {c.heroCtaSecondary}
          </a>
        </div>

        {/* Stats row */}
        <StatsRow c={c} />
      </div>
    </section>
  );
}

function StatsRow({ c }: { c: LandingContent }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-0 sm:divide-x sm:divide-night-600 border border-night-600 rounded-xl overflow-hidden bg-night-800/60">
      {c.stats.map((s, i) => (
        <div key={i} className="px-6 py-5">
          <div className="text-2xl sm:text-3xl font-bold text-gold mb-1">
            {s.value}
          </div>
          <div className="text-sm font-medium text-prose mb-0.5">{s.label}</div>
          <div className="text-xs text-prose-faint">{s.note}</div>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   PIPELINE
═══════════════════════════════════════════════════════════════════════ */
function Pipeline({ c }: { c: LandingContent }) {
  return (
    <section id="pipeline" className="py-20 sm:py-28 border-t border-night-600">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <SectionLabel>{c.pipelineTitle}</SectionLabel>
        <p className="text-prose-muted text-base sm:text-lg max-w-2xl mb-14 leading-relaxed">
          {c.pipelineSubtitle}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {c.steps.map((step, i) => (
            <PipelineCard key={i} step={step} />
          ))}
        </div>
      </div>
    </section>
  );
}

function PipelineCard({
  step,
}: {
  step: { n: string; title: string; body: string };
}) {
  return (
    <div className="rounded-xl border border-night-600 bg-night-800 p-6 hover:border-gold/30 transition-colors group">
      <div className="text-xs font-mono text-gold/60 mb-3 group-hover:text-gold/80 transition-colors">
        {step.n}
      </div>
      <h3 className="text-base font-semibold text-prose mb-2">{step.title}</h3>
      <p className="text-sm text-prose-muted leading-relaxed">{step.body}</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   DEMO VIDEO
═══════════════════════════════════════════════════════════════════════ */
function DemoSection({ c }: { c: LandingContent }) {
  return (
    <section
      id="demo"
      className="py-20 sm:py-28 border-t border-night-600 bg-night-900"
    >
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <SectionLabel>{c.demoTitle}</SectionLabel>
        <p className="text-prose-muted text-base sm:text-lg max-w-xl mb-10 leading-relaxed">
          {c.demoSubtitle}
        </p>

        {/*
          Video element. Poster + sources will be served from /public/demo/.
          Until those files are added, the placeholder div shows.
          Strategy: CSS gradient background + CSS-only animation.
          No GIF, no 60fps asset committed.
        */}
        <div className="relative aspect-video rounded-2xl overflow-hidden border border-gold/20 shadow-card demo-placeholder">
          {/* Actual video — hidden until /public/demo/hero.mp4 exists */}
          <video
            autoPlay
            muted
            loop
            playsInline
            poster="/demo/poster.jpg"
            className="absolute inset-0 w-full h-full object-cover opacity-0 [&[data-loaded]]:opacity-100"
            aria-label={c.demoPlaceholder}
          >
            <source src="/demo/hero.mp4" type="video/mp4" />
            <source src="/demo/hero.webm" type="video/webm" />
          </video>

          {/* Placeholder overlay */}
          <div className="relative z-10 flex flex-col items-center justify-center h-full gap-5">
            {/* Play icon */}
            <div className="w-16 h-16 rounded-full border-2 border-gold/60 flex items-center justify-center bg-night-700/80">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-7 h-7 text-gold ml-0.5"
                aria-hidden="true"
              >
                <path d="M8 5v14l11-7L8 5z" />
              </svg>
            </div>
            <p className="text-prose-muted text-sm text-center px-4 max-w-xs">
              {c.demoPlaceholder}
            </p>
          </div>
        </div>

        <p className="mt-4 text-xs text-prose-faint text-center">{c.demoNote}</p>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   ROI
═══════════════════════════════════════════════════════════════════════ */
function RoiSection({ c }: { c: LandingContent }) {
  return (
    <section id="roi" className="py-20 sm:py-28 border-t border-night-600">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <SectionLabel>{c.roiTitle}</SectionLabel>
        <p className="text-prose-muted text-base sm:text-lg max-w-2xl mb-12 leading-relaxed">
          {c.roiSubtitle}
        </p>

        {/* Table */}
        <div className="rounded-xl border border-night-600 overflow-x-auto mb-8 shadow-card">
          <table className="roi-table w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-night-600 bg-night-800">
                {c.roiTableHeaders.map((h, i) => (
                  <th
                    key={i}
                    className={`px-4 py-3 text-left font-medium text-xs uppercase tracking-wide ${
                      i === 0
                        ? "text-prose-muted"
                        : i === 2
                        ? "text-gold"
                        : "text-prose-muted"
                    }`}
                  >
                    {i === 2 ? (
                      <span className="flex items-center gap-1">
                        {h}{" "}
                        <span className="text-gold text-xs normal-case font-normal">
                          ★
                        </span>
                      </span>
                    ) : (
                      h
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {c.roiRows.map((row, ri) => (
                <tr
                  key={ri}
                  className={`border-b border-night-600/60 transition-colors hover:bg-night-800/40 ${
                    ri === c.roiRows.length - 1
                      ? "bg-night-800/30"
                      : ""
                  }`}
                >
                  {row.map((cell, ci) => (
                    <td
                      key={ci}
                      className={`px-4 py-3 ${
                        ci === 0
                          ? "text-prose-muted text-xs"
                          : ci === 2
                          ? "text-gold font-semibold"
                          : "text-prose"
                      }`}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Critical insight */}
        <div className="rounded-xl border border-gold/25 bg-gold-subtle px-6 py-4 mb-6">
          <p className="text-gold text-sm font-medium">{c.roiCritical}</p>
        </div>

        {/* Source */}
        <p className="text-xs text-prose-faint leading-relaxed">{c.roiSource}</p>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   SAFETY & COMPLIANCE
═══════════════════════════════════════════════════════════════════════ */
function SafetySection({ c }: { c: LandingContent }) {
  return (
    <section
      id="safety"
      className="py-20 sm:py-28 border-t border-night-600 bg-night-900"
    >
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <SectionLabel>{c.safetyTitle}</SectionLabel>
        <p className="text-prose-muted text-base sm:text-lg max-w-2xl mb-12 leading-relaxed">
          {c.safetySubtitle}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {c.safetyPoints.map((point, i) => (
            <div
              key={i}
              className="rounded-xl border border-night-600 bg-night-800 p-6 hover:border-gold/20 transition-colors"
            >
              <div className="text-2xl mb-3" aria-hidden="true">
                {point.icon}
              </div>
              <h3 className="text-sm font-semibold text-prose mb-2">
                {point.title}
              </h3>
              <p className="text-xs text-prose-muted leading-relaxed">
                {point.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   CTA
═══════════════════════════════════════════════════════════════════════ */
function CtaSection({ c }: { c: LandingContent }) {
  return (
    <section id="cta" className="py-20 sm:py-28 border-t border-night-600">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 text-center">
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4 leading-tight">
          {c.ctaTitle}
        </h2>
        <p className="text-prose-muted text-base sm:text-lg max-w-xl mx-auto mb-10 leading-relaxed">
          {c.ctaBody}
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a
            href="https://github.com/UlaYuga/recall-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-cta-gradient px-8 py-3.5 text-white font-semibold text-sm sm:text-base hover:opacity-90 transition-opacity"
          >
            {c.ctaGithub}
          </a>
          <a
            href={
              process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3001"
            }
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-night-500 px-8 py-3.5 text-prose-muted text-sm sm:text-base hover:border-gold/50 hover:text-prose transition-colors"
          >
            {c.ctaDashboard}
          </a>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   FOOTER
═══════════════════════════════════════════════════════════════════════ */
function Footer({ c }: { c: LandingContent }) {
  return (
    <footer className="border-t border-night-600 bg-night-900 py-10">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 text-center space-y-2">
        <p className="text-xs text-prose-faint">{c.footerNote}</p>
        <p className="text-xs text-prose-faint">{c.footerBy}</p>
      </div>
    </footer>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   SHARED UI
═══════════════════════════════════════════════════════════════════════ */
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4 leading-tight">
      {children}
    </h2>
  );
}
