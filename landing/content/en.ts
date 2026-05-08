/**
 * EN content — primary copy for international iGaming / consumer subscription.
 * Generic subscription framing available where noted (Runway compliance mode).
 */
export const en = {
  /* ── Meta ──────────────────────────────────────────────────────────── */
  metaTitle: "Recall — AI Retention Agent",
  metaDescription:
    "Event-driven agent that identifies churn risk, generates personalized motion-graphics video with Runway, routes through human approval, and delivers to dormant players.",

  /* ── Nav ────────────────────────────────────────────────────────────── */
  logoLabel: "Recall",
  navGithub: "GitHub",
  navDashboard: "Dashboard",
  langSwitch: "RU",
  langSwitchHref: "?lang=ru",

  /* ── Hero ───────────────────────────────────────────────────────────── */
  badge: "Built with Runway Gen-4.5 · ElevenLabs TTS",
  heroHeadline: "AI Retention Agent",
  heroSubhead:
    "Identifies dormant players, generates a personalized motion-graphics video message, routes it through a CRM approval gate, and delivers through Telegram — tracked to conversion.",
  heroCta: "See the pipeline",
  heroCtaSecondary: "GitHub →",

  /* ── Stats ──────────────────────────────────────────────────────────── */
  stats: [
    { value: "3.87×", label: "ROI base scenario", note: "10K players, 60-day window" },
    { value: "6.2%", label: "break-even uplift", note: "vs. industry baseline 20–50%" },
    { value: "$116K", label: "annual net lift", note: "base scenario, 120K players/yr" },
  ],

  /* ── How It Works ───────────────────────────────────────────────────── */
  pipelineTitle: "End-to-End Pipeline",
  pipelineSubtitle:
    "Six deterministic steps from a dormant signal to a tracked conversion — no black-box scoring.",
  steps: [
    {
      n: "01",
      title: "Detect",
      body: "APScheduler polls the event bus. Players inactive beyond cohort thresholds are flagged as dormant candidates.",
    },
    {
      n: "02",
      title: "Classify",
      body: "Rule-based classifier assigns one of six cohorts — vip_at_risk, high_value_dormant, lapsed_loyal, post_event, first_deposit_no_return, casual_dormant — with a risk score.",
    },
    {
      n: "03",
      title: "Script + Offer",
      body: "Claude Sonnet generates a 4-scene script with a personalized offer. Forbidden terms are stripped by the prompt-safety layer before any Runway call.",
    },
    {
      n: "04",
      title: "Approve",
      body: "CRM manager reviews cohort, script, and offer in the approval dashboard. Can edit inline, regenerate, or reject with a reason. No video is generated without approval.",
    },
    {
      n: "05",
      title: "Generate Video",
      body: "Runway Gen-4.5 generates motion-graphics clips per scene, ElevenLabs TTS voices the script, ffmpeg stitches them into a 30–45 s mp4 with poster.",
    },
    {
      n: "06",
      title: "Deliver & Track",
      body: "Telegram delivers poster + video with an inline CTA button. The reactivation landing tracks play, click, and deposit. Dashboard shows ROI in real time.",
    },
  ],

  /* ── Demo Video ─────────────────────────────────────────────────────── */
  demoTitle: "Demo",
  demoSubtitle: "End-to-end pipeline walkthrough · ~2 min",
  demoPlaceholder: "Demo video will appear here",
  demoNote: "Recorded pipeline run across 7 mock players — 6 cohort archetypes, 4 currencies.",

  /* ── ROI ────────────────────────────────────────────────────────────── */
  roiTitle: "The Business Case",
  roiSubtitle:
    "Production-scale model. Hackathon free credits excluded. Parameters replaceable with operator CRM data.",
  roiScenarioHeader: "Scenario",
  roiTableHeaders: ["Metric", "Conservative", "Base", "Aggressive"],
  roiRows: [
    ["Baseline reactivation rate", "5%", "7%", "10%"],
    ["AI video uplift (relative)", "+20%", "+30%", "+50%"],
    ["60-day value per player", "$40", "$58", "$85"],
    ["Incremental reactivated (10K)", "100", "210", "500"],
    ["Net lift (10K players)", "$1,500", "$9,680", "$40,000"],
    ["ROI", "0.60×", "3.87×", "16.0×"],
    ["Payback period", "~2 months", "~2 weeks", "~4 days"],
  ],
  roiCritical: "Break-even at just 6.2% uplift — 3× headroom before losing money.",
  roiSource:
    "Sources: Engagehut dormant player benchmarks · Idomoo/Entain iGaming case (conservative 20–50% vs reported 100%+) · iGaming international mid-tier LTV $40–85 · Runway API pricing $0.01/credit",

  /* ── Safety & Compliance ────────────────────────────────────────────── */
  safetyTitle: "Safety & Compliance by Design",
  safetySubtitle:
    "Not retrofitted. Every pipeline stage has an explicit guard, not just the output.",
  safetyPoints: [
    {
      icon: "👤",
      title: "Human approval before every video",
      body: "No generation without CRM manager sign-off. Reject with structured reason (too_aggressive, wrong_offer, wrong_tone, data_issue). Script and offer editable inline.",
    },
    {
      icon: "🛡️",
      title: "Prompt safety layer",
      body: "50+ forbidden brand names and 20+ game titles stripped before Runway calls. No faces, no logos, no real provider names in visual prompts. Abstract motion-graphics mode only.",
    },
    {
      icon: "✅",
      title: "Two-layer consent gate",
      body: "Generation consent (data_processing + video_personalization) gates the pipeline. Delivery consent (marketing_comms + channel-specific) gates sending. A ready video never delivers without consent.",
    },
    {
      icon: "🔄",
      title: "Provider-agnostic architecture",
      body: "VideoProviderProtocol wraps Runway. Swappable to Veo, Kling, Luma, or Pika in ~1 hour. No vendor lock-in in the core agent logic.",
    },
  ],

  /* ── CTA ────────────────────────────────────────────────────────────── */
  ctaTitle: "Built in 3 days for the Runway Hackathon",
  ctaBody:
    "Full FastAPI backend · Next.js approval dashboard · Telegram delivery · conversion tracking · ROI simulation.",
  ctaGithub: "View on GitHub",
  ctaDashboard: "Open Dashboard",

  /* ── Footer ─────────────────────────────────────────────────────────── */
  footerNote: "Simulation based on industry benchmarks — actual results vary by operator, market, and player segment.",
  footerBy: "Built with Runway Gen-4.5, ElevenLabs TTS via Runway, Claude Sonnet, FastAPI, Next.js.",
};

export type LandingContent = typeof en;
