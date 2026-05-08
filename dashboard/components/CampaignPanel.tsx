'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';
import {
  X,
  Check,
  XCircle,
  RefreshCw,
  Pencil,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from 'lucide-react';
import {
  approval,
  type QueueItem,
  type ScriptData,
  type ScriptScene,
  type OfferData,
} from '../lib/api';

// ── Helpers ───────────────────────────────────────────────────────────────

function parseOffer(json: string | null): OfferData | null {
  if (!json) return null;
  try {
    return JSON.parse(json) as OfferData;
  } catch {
    return null;
  }
}

function parseScript(json: string | null): ScriptData | null {
  if (!json) return null;
  try {
    return JSON.parse(json) as ScriptData;
  } catch {
    return null;
  }
}

function parseReasoning(json: string | null): string[] {
  if (!json) return [];
  try {
    const data: unknown = JSON.parse(json);
    if (Array.isArray(data)) return data as string[];
    return [];
  } catch {
    return [];
  }
}

function parseRejectReason(json: string | null): string | null {
  if (!json) return null;
  try {
    const d = JSON.parse(json) as unknown;
    if (d && typeof d === 'object' && !Array.isArray(d)) {
      const r = (d as Record<string, unknown>).reject_reason;
      if (r != null) return String(r);
    }
  } catch {
    // ignore
  }
  return null;
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function fmtNum(n: number | null | undefined): string {
  if (n == null) return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n);
}

const SCENE_LABELS: Record<string, string> = {
  intro: 'Intro',
  personalized_hook: 'Hook',
  offer: 'Offer',
  cta: 'CTA',
};

const STATUS_CHIP: Record<string, string> = {
  draft:                  'bg-line text-dim',
  pending_approval:       'bg-info/10 text-info',
  approved:               'bg-pass/10 text-pass',
  rejected:               'bg-fail/10 text-fail',
  generating:             'bg-warn/10 text-warn',
  generation_failed:      'bg-fail/10 text-fail',
  ready:                  'bg-accent/10 text-accent',
  ready_blocked_delivery: 'bg-warn/10 text-warn',
  delivered:              'bg-pass/10 text-pass',
  converted:              'bg-accent/10 text-accent',
};

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draft',
  pending_approval: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  generating: 'Generating',
  generation_failed: 'Gen. Failed',
  ready: 'Ready',
  ready_blocked_delivery: 'Delivery Blocked',
  delivered: 'Delivered',
  converted: 'Converted',
};

const REJECT_OPTIONS = [
  { value: 'too_aggressive', label: 'Too aggressive' },
  { value: 'wrong_offer', label: 'Wrong offer' },
  { value: 'wrong_tone', label: 'Wrong tone' },
  { value: 'data_issue', label: 'Data issue' },
  { value: 'other', label: 'Other…' },
] as const;

const EDITABLE = new Set(['draft', 'pending_approval']);

// ── Section ───────────────────────────────────────────────────────────────

function Section({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const id = `panel-section-${title.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className="border-b border-edge last:border-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={id}
        className="flex w-full items-center justify-between px-5 py-2.5 text-xs font-semibold text-sub uppercase tracking-wide hover:bg-graph focus:outline-none focus:ring-2 focus:ring-inset focus:ring-accent transition-colors"
      >
        <span>{title}</span>
        {open ? (
          <ChevronUp size={13} aria-hidden="true" />
        ) : (
          <ChevronDown size={13} aria-hidden="true" />
        )}
      </button>
      {open && (
        <div id={id} className="px-5 pb-4 pt-1">
          {children}
        </div>
      )}
    </div>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────

export interface CampaignPanelProps {
  item: QueueItem;
  onClose: () => void;
  /** Called after any successful mutation so the parent can refresh the queue. */
  onMutated: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────

export function CampaignPanel({ item, onClose, onMutated }: CampaignPanelProps) {
  const [local, setLocal] = useState<QueueItem>(item);
  useEffect(() => setLocal(item), [item]);

  const [editMode, setEditMode] = useState(false);
  const [editedScenes, setEditedScenes] = useState<ScriptScene[]>([]);
  const [editedCta, setEditedCta] = useState('');

  const [rejectMode, setRejectMode] = useState(false);
  const [rejectKey, setRejectKey] = useState('');
  const [rejectNotes, setRejectNotes] = useState('');

  const [actionError, setActionError] = useState<string | null>(null);

  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const canEdit = EDITABLE.has(local.status);

  // ── Derived data ─────────────────────────────────────────────────────────
  const offer = parseOffer(local.offer_json);
  const script = parseScript(local.script_json);
  const reasoning = parseReasoning(local.reasoning_json);
  const rejectReason = local.status === 'rejected' ? parseRejectReason(local.reasoning_json) : null;
  const p = local.player;

  // ── Edit mode ─────────────────────────────────────────────────────────────
  function enterEdit() {
    if (!script) return;
    setEditedScenes(script.scenes.map((s) => ({ ...s })));
    setEditedCta(script.cta_text);
    setEditMode(true);
    setActionError(null);
  }

  function cancelEdit() {
    setEditMode(false);
    setEditedScenes([]);
    setActionError(null);
  }

  function cancelReject() {
    setRejectMode(false);
    setRejectKey('');
    setRejectNotes('');
    setActionError(null);
  }

  // Effective reason sent to the API
  const effectiveRejectReason =
    rejectKey === 'other' ? rejectNotes.trim() || 'other' : rejectKey;
  const canSubmitReject =
    Boolean(rejectKey) && (rejectKey !== 'other' || Boolean(rejectNotes.trim()));

  // ── Mutations ─────────────────────────────────────────────────────────────
  const approveM = useMutation({
    mutationFn: () => approval.approve(local.campaign_id),
    onSuccess: (res) => {
      setLocal((prev) => ({
        ...prev,
        status: res.status as QueueItem['status'],
        updated_at: res.updated_at,
      }));
      setActionError(null);
      onMutated();
      onClose();
    },
    onError: (e) => setActionError(e instanceof Error ? e.message : 'Approve failed'),
  });

  const rejectM = useMutation({
    mutationFn: () => approval.reject(local.campaign_id, effectiveRejectReason),
    onSuccess: (res) => {
      setLocal((prev) => ({
        ...prev,
        status: res.status as QueueItem['status'],
        updated_at: res.updated_at,
      }));
      cancelReject();
      onMutated();
      onClose();
    },
    onError: (e) => setActionError(e instanceof Error ? e.message : 'Reject failed'),
  });

  const editM = useMutation({
    mutationFn: () => {
      if (!script) throw new Error('No script to edit');
      const updatedScript: ScriptData = {
        ...script,
        scenes: editedScenes,
        cta_text: editedCta,
      };
      return approval.edit(local.campaign_id, {
        script_json: JSON.stringify(updatedScript),
      });
    },
    onSuccess: (res) => {
      const updatedScript: ScriptData = {
        ...(script as ScriptData),
        scenes: editedScenes,
        cta_text: editedCta,
      };
      setLocal((prev) => ({
        ...prev,
        status: res.status as QueueItem['status'],
        script_json: JSON.stringify(updatedScript),
        updated_at: res.updated_at,
      }));
      setEditMode(false);
      setEditedScenes([]);
      setActionError(null);
      onMutated();
    },
    onError: (e) => setActionError(e instanceof Error ? e.message : 'Save failed'),
  });

  const regenerateM = useMutation({
    mutationFn: () => approval.regenerate(local.campaign_id),
    onSuccess: (res) => {
      setLocal((prev) => ({
        ...prev,
        script_json: JSON.stringify(res.script),
        updated_at: res.updated_at,
      }));
      setEditMode(false);
      setActionError(null);
      onMutated();
    },
    onError: (e) => setActionError(e instanceof Error ? e.message : 'Regenerate failed'),
  });

  const isBusy =
    approveM.isPending || rejectM.isPending || editM.isPending || regenerateM.isPending;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-30"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Panel */}
      <aside
        ref={panelRef}
        role="complementary"
        aria-label={`Campaign detail for ${local.first_name}`}
        className="fixed inset-y-0 right-0 w-[500px] max-w-full bg-char shadow-2xl z-40 flex flex-col focus:outline-none drawer-in"
        tabIndex={-1}
      >
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="flex-none flex items-center gap-3 px-5 h-14 border-b border-edge bg-ink">
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-text text-sm truncate">
              {local.first_name}
            </p>
            <p className="text-xs text-sub truncate">
              {local.country} · {local.currency} · {local.player_id}
            </p>
          </div>
          <span
            className={[
              'flex-none inline-flex items-center rounded px-2 py-0.5 text-xs font-medium',
              STATUS_CHIP[local.status] ?? 'bg-line text-dim',
            ].join(' ')}
          >
            {STATUS_LABEL[local.status] ?? local.status}
          </span>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Close panel"
            className="flex-none p-1.5 rounded text-sub hover:text-dim hover:bg-graph focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        {/* ── Scrollable body ─────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto">
          {/* Player Profile */}
          <Section title="Player Profile">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <ProfileRow label="LTV segment" value={p.ltv_segment || '—'} />
              <ProfileRow
                label="Deposits"
                value={`${p.total_deposits_count} × ${p.currency} ${fmtNum(p.total_deposits_amount)}`}
              />
              <ProfileRow label="Last login" value={fmtDate(p.last_login_at)} />
              <ProfileRow label="Last deposit" value={fmtDate(p.last_deposit_at)} />
              {p.favorite_vertical && (
                <ProfileRow label="Vertical" value={p.favorite_vertical} />
              )}
              {p.favorite_game_category && (
                <ProfileRow label="Game category" value={p.favorite_game_category} />
              )}
              {p.favorite_game_label && (
                <ProfileRow label="Game label" value={p.favorite_game_label} />
              )}
              {p.biggest_win_amount != null && (
                <ProfileRow
                  label="Biggest win"
                  value={`${p.biggest_win_currency ?? p.currency} ${fmtNum(p.biggest_win_amount)}`}
                />
              )}
              <ProfileRow label="Language" value={p.preferred_language} />
            </dl>
          </Section>

          {/* Classifier Reasoning */}
          <Section title="Classifier Reasoning">
            {/* Reject reason banner */}
            {rejectReason && (
              <div className="mb-3 flex items-start gap-2 text-xs text-fail bg-fail/10 border border-fail/20 rounded px-3 py-2">
                <XCircle size={13} className="flex-none mt-0.5" aria-hidden="true" />
                <span>
                  Rejected — <span className="font-medium">{rejectReason}</span>
                </span>
              </div>
            )}

            {reasoning.length === 0 ? (
              <p className="text-xs text-sub italic">No reasoning recorded.</p>
            ) : (
              <ul className="space-y-1.5">
                {reasoning.map((r, i) => (
                  <li key={i} className="flex gap-2 text-xs text-dim">
                    <span className="text-info flex-none mt-0.5" aria-hidden="true">
                      ›
                    </span>
                    {r}
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-3 flex gap-4 text-xs">
              <span className="text-sub">
                Cohort:{' '}
                <span className="font-medium text-text">
                  {local.cohort.replace(/_/g, ' ')}
                </span>
              </span>
              <span className="text-sub">
                Risk:{' '}
                <span
                  className={[
                    'font-semibold tabular-nums',
                    local.risk_score >= 70
                      ? 'text-fail'
                      : local.risk_score >= 40
                        ? 'text-warn'
                        : 'text-pass',
                  ].join(' ')}
                >
                  {Math.round(local.risk_score)}
                </span>
              </span>
            </div>
          </Section>

          {/* Offer */}
          <Section title="Offer">
            {!offer ? (
              <p className="text-xs text-sub italic">Offer data unavailable.</p>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="flex gap-3">
                  <span className="bg-line text-dim rounded px-2 py-0.5 font-medium uppercase text-[10px] tracking-wide">
                    {offer.type}
                  </span>
                  <span className="font-semibold text-text">{offer.label}</span>
                </div>
                <p className="text-dim leading-relaxed">{offer.copy}</p>
                <p className="text-sub leading-relaxed border-l-2 border-edge pl-2">
                  {offer.terms}
                </p>
                <div className="flex gap-4 text-sub pt-0.5">
                  <span>Value: <span className="font-medium text-text">{offer.value}</span></span>
                  <span>Expires: <span className="font-medium text-text">{offer.expiry_days}d</span></span>
                  {offer.game_label && (
                    <span>Game: <span className="font-medium text-text">{offer.game_label}</span></span>
                  )}
                </div>
              </div>
            )}
          </Section>

          {/* Script */}
          <Section title="Script (4 Scenes)">
            {!script ? (
              <p className="text-xs text-sub italic">Script not generated yet.</p>
            ) : editMode ? (
              <div className="space-y-3">
                {editedScenes.map((scene, idx) => (
                  <div key={scene.id} className="space-y-1">
                    <label
                      htmlFor={`scene-text-${scene.id}`}
                      className="block text-xs font-medium text-dim"
                    >
                      {SCENE_LABELS[scene.type] ?? scene.type}
                    </label>
                    <textarea
                      id={`scene-text-${scene.id}`}
                      value={scene.text}
                      rows={3}
                      onChange={(e) => {
                        const updated = editedScenes.map((s, i) =>
                          i === idx ? { ...s, text: e.target.value } : s
                        );
                        setEditedScenes(updated);
                      }}
                      className="w-full text-xs border border-edge rounded px-2.5 py-1.5 bg-ink text-text focus:outline-none focus:ring-2 focus:ring-accent resize-y"
                    />
                    <p className="text-sub text-[10px] leading-relaxed">
                      Visual: {scene.visual_brief}
                    </p>
                  </div>
                ))}
                <div className="space-y-1">
                  <label
                    htmlFor="scene-cta"
                    className="block text-xs font-medium text-dim"
                  >
                    CTA text
                  </label>
                  <input
                    id="scene-cta"
                    type="text"
                    value={editedCta}
                    onChange={(e) => setEditedCta(e.target.value)}
                    className="w-full text-xs border border-edge rounded px-2.5 py-1.5 bg-ink text-text focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
                <p className="text-xs text-sub italic pt-1 border-t border-edge">
                  Voiceover (~{script.estimated_duration_sec}s · {script.tone}):{' '}
                  {script.full_voiceover_text}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {script.scenes.map((scene) => (
                  <div key={scene.id} className="space-y-0.5">
                    <span className="text-[10px] font-semibold uppercase tracking-wide text-sub">
                      {SCENE_LABELS[scene.type] ?? scene.type}
                    </span>
                    <p className="text-xs text-text leading-relaxed">{scene.text}</p>
                    <p className="text-[10px] text-sub leading-relaxed">
                      Visual: {scene.visual_brief}
                    </p>
                  </div>
                ))}
                <div className="pt-2 border-t border-edge space-y-1">
                  <p className="text-xs text-sub leading-relaxed">
                    <span className="font-medium">Voiceover</span>{' '}
                    (~{script.estimated_duration_sec}s · {script.tone}):{' '}
                    <span className="text-dim">{script.full_voiceover_text}</span>
                  </p>
                  <p className="text-xs text-sub">
                    <span className="font-medium">CTA:</span>{' '}
                    <span className="text-dim">{script.cta_text}</span>
                  </p>
                  <p className="text-[10px] text-sub">
                    Source: {script.source}
                  </p>
                </div>
              </div>
            )}
          </Section>
        </div>

        {/* ── Actions footer ──────────────────────────────────────────────── */}
        <div className="flex-none border-t border-edge bg-graph px-5 py-3 space-y-2.5">
          {/* Error */}
          {actionError && (
            <div
              role="alert"
              className="flex items-start gap-2 text-xs text-fail bg-fail/10 border border-fail/20 rounded px-3 py-2"
            >
              <AlertCircle size={13} className="flex-none mt-0.5" aria-hidden="true" />
              <span>{actionError}</span>
            </div>
          )}

          {/* Reject form */}
          {rejectMode && (
            <div className="space-y-2">
              <div className="space-y-1.5">
                <label htmlFor="reject-reason-select" className="block text-xs font-medium text-dim">
                  Reject reason <span className="text-fail" aria-hidden="true">*</span>
                </label>
                <select
                  id="reject-reason-select"
                  value={rejectKey}
                  onChange={(e) => setRejectKey(e.target.value)}
                  className="w-full text-xs border border-edge rounded px-2.5 py-1.5 bg-ink text-text focus:outline-none focus:ring-2 focus:ring-fail"
                  autoFocus
                >
                  <option value="">Select a reason…</option>
                  {REJECT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              {rejectKey === 'other' && (
                <div className="space-y-1">
                  <label htmlFor="reject-notes" className="block text-xs font-medium text-dim">
                    Details
                  </label>
                  <textarea
                    id="reject-notes"
                    value={rejectNotes}
                    onChange={(e) => setRejectNotes(e.target.value)}
                    rows={2}
                    placeholder="Describe the issue…"
                    className="w-full text-xs border border-edge rounded px-2.5 py-1.5 bg-ink text-text focus:outline-none focus:ring-2 focus:ring-fail resize-none"
                  />
                </div>
              )}
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={!canSubmitReject || rejectM.isPending}
                  onClick={() => {
                    setActionError(null);
                    rejectM.mutate();
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded text-xs font-medium bg-fail text-white hover:bg-fail/80 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-fail transition-colors"
                >
                  {rejectM.isPending ? (
                    <Loader2 size={12} className="animate-spin" aria-hidden="true" />
                  ) : (
                    <XCircle size={12} aria-hidden="true" />
                  )}
                  Confirm Reject
                </button>
                <button
                  type="button"
                  onClick={cancelReject}
                  className="px-3 py-1.5 rounded text-xs font-medium border border-edge text-dim hover:bg-char focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Edit save/cancel row */}
          {editMode && !rejectMode && (
            <div className="flex gap-2">
              <button
                type="button"
                disabled={editM.isPending}
                onClick={() => {
                  setActionError(null);
                  editM.mutate();
                }}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded text-xs font-medium bg-accent text-ink hover:bg-accent/80 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
              >
                {editM.isPending ? (
                  <Loader2 size={12} className="animate-spin" aria-hidden="true" />
                ) : (
                  <Check size={12} aria-hidden="true" />
                )}
                Save Changes
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                className="px-3 py-1.5 rounded text-xs font-medium border border-edge text-dim hover:bg-char focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Primary actions row */}
          {!editMode && !rejectMode && (
            <div className="space-y-2">
              {canEdit ? (
                <div className="flex gap-2 flex-wrap">
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => {
                      setActionError(null);
                      approveM.mutate();
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-pass text-ink hover:bg-pass/80 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-pass transition-colors"
                  >
                    {approveM.isPending ? (
                      <Loader2 size={12} className="animate-spin" aria-hidden="true" />
                    ) : (
                      <Check size={12} aria-hidden="true" />
                    )}
                    Approve
                  </button>

                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => {
                      setActionError(null);
                      setRejectMode(true);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-fail text-white hover:bg-fail/80 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-fail transition-colors"
                  >
                    <XCircle size={12} aria-hidden="true" />
                    Reject
                  </button>

                  {script && (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={enterEdit}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border border-edge bg-char text-dim hover:bg-graph disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
                    >
                      <Pencil size={12} aria-hidden="true" />
                      Edit Script
                    </button>
                  )}

                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => {
                      setActionError(null);
                      regenerateM.mutate();
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border border-edge bg-char text-dim hover:bg-graph disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
                  >
                    {regenerateM.isPending ? (
                      <Loader2 size={12} className="animate-spin" aria-hidden="true" />
                    ) : (
                      <RefreshCw size={12} aria-hidden="true" />
                    )}
                    Regenerate
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-sub">
                    Status:{' '}
                    <span
                      className={[
                        'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium',
                        STATUS_CHIP[local.status] ?? 'bg-line text-dim',
                      ].join(' ')}
                    >
                      {STATUS_LABEL[local.status] ?? local.status}
                    </span>
                  </p>
                  <Link
                    href={`/campaigns/${local.campaign_id}`}
                    onClick={onClose}
                    className="inline-flex items-center gap-1 text-xs text-accent hover:text-accent/70 hover:underline focus:outline-none focus:ring-1 focus:ring-accent rounded whitespace-nowrap"
                  >
                    Open workspace
                    <ExternalLink size={11} aria-hidden="true" />
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Updated at */}
          {local.updated_at && (
            <p className="text-[10px] text-sub">
              Updated {fmtDate(local.updated_at)}
            </p>
          )}
        </div>
      </aside>
    </>
  );
}

// ── Small presentational helpers ──────────────────────────────────────────

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-sub">{label}</dt>
      <dd className="text-text font-medium truncate" title={value}>
        {value}
      </dd>
    </>
  );
}
