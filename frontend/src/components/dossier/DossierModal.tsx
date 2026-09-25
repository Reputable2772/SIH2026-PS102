import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../api/client';
import { GovernanceDossier, ReviewState, DetectorDefinition } from '../../types';
import { PriorityBadge } from '../common/PriorityBadge';
import { DetectorDetailModal } from '../detectors/DetectorDetailModal';
import {
  X,
  Printer,
  CheckSquare,
  Square,
  AlertTriangle,
  Building,
  Calendar,
  IndianRupee,
  User,
  MapPin,
  FileText,
  Save,
  Clock,
  ShieldAlert,
  Copy,
  Check,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';
import clsx from 'clsx';

interface DossierModalProps {
  workRecId: string | null;
  onClose: () => void;
}

export const DossierModal: React.FC<DossierModalProps> = ({ workRecId, onClose }) => {
  const { currentUser, switchPersona } = useAuth();
  const { showToast } = useToast();

  const canEditReviews =
    currentUser?.permissions?.includes('dispatch_dqm_inspection') ||
    currentUser?.permissions?.includes('manage_district_review_queue') ||
    currentUser?.role === 'CENTRAL_AUDITOR';

  const [dossier, setDossier] = useState<GovernanceDossier | null>(null);
  const [reviewState, setReviewState] = useState<ReviewState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<boolean>(false);
  const [status, setStatus] = useState<'UNDER_REVIEW' | 'DQM_DISPATCHED' | 'RESOLVED' | 'ESCALATED_TO_CAG'>('UNDER_REVIEW');
  const [checkedActions, setCheckedActions] = useState<string[]>([]);
  const [auditorNotes, setAuditorNotes] = useState<string>('');
  const [selectedRule, setSelectedRule] = useState<DetectorDefinition | null>(null);
  const [allDetectors, setAllDetectors] = useState<DetectorDefinition[]>([]);

  useEffect(() => {
    api.getDetectors().then((data) => setAllDetectors(data)).catch(() => {});
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (selectedRule) {
          setSelectedRule(null);
        } else {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, selectedRule]);

  useEffect(() => {
    if (!workRecId) return;
    setLoading(true);
    setErrorMsg(null);

    Promise.all([
      api.getDossier(workRecId),
      api.getReviewState(workRecId),
    ])
      .then(([dos, rev]) => {
        setDossier(dos);
        setReviewState(rev);
        setStatus(rev.status);
        setCheckedActions(rev.checked_actions || []);
        setAuditorNotes(rev.auditor_notes || '');
      })
      .catch((err: any) => {
        console.error('Failed to load dossier:', err);
        setErrorMsg(err.message || 'Failed to load governance dossier.');
      })
      .finally(() => setLoading(false));
  }, [workRecId]);

  const handleOpenDetectorRule = (code: string) => {
    const match = allDetectors.find((d) => d.code === code);
    if (match) {
      setSelectedRule(match);
      return;
    }
    const fallbacks: Record<string, DetectorDefinition> = {
      'COMP-D1': {
        code: 'COMP-D1',
        name: 'Sanction SLA Breach',
        phase: 'Phase 1',
        category: 'COMPLIANCE',
        description: 'Mandates that District Authority (IDA) must issue administrative sanction or formal rejection within 45 days of receiving MP recommendation.',
        legal_basis: 'MPLADS Guidelines 2023, Para 3.2.4',
        threshold: '> 45 calendar days from MP recommendation',
        formula: 'days_rec_to_sanction > 45',
        prescribed_action: 'Issue compliance notice to District Planning Officer; require written justification for delayed administrative sanction.',
      },
      'COMP-D2': {
        code: 'COMP-D2',
        name: 'Execution Delay Overrun',
        phase: 'Phase 2',
        category: 'COMPLIANCE',
        description: 'Mandates that sanctioned works must be completed within 1 statutory year (365 calendar days).',
        legal_basis: 'MPLADS Guidelines 2023, Para 3.2.12',
        threshold: '> 365 calendar days from administrative sanction without completion',
        formula: 'days_since_sanction > 365 and not is_completed',
        prescribed_action: 'Dispatch District Quality Monitor (DQM) site inspection; summon Implementing Agency executive engineer.',
      },
      'COMP-D3': {
        code: 'COMP-D3',
        name: 'Dormant Undisbursed Sanction',
        phase: 'Phase 2',
        category: 'FINANCIAL',
        description: 'Identifies sanctioned works where zero capital has been mobilized after 90 days of sanction approval.',
        legal_basis: 'Ministerial Directive & General Financial Rules (GFR)',
        threshold: '> 90 days from sanction with 0 disbursed capital',
        formula: 'days_since_sanction > 90 and total_disbursed == 0',
        prescribed_action: 'Review tender award status; issue show-cause notice to Implementing Agency for fund paralysis.',
      },
    };
    if (fallbacks[code]) {
      setSelectedRule(fallbacks[code]);
    }
  };

  if (!workRecId) return null;

  const handleCopyId = () => {
    if (!workRecId) return;
    navigator.clipboard.writeText(workRecId);
    setCopiedId(true);
    showToast('Work ID Copied', `#${workRecId} copied to clipboard`, 'info');
    setTimeout(() => setCopiedId(false), 2000);
  };

  const toggleAction = (actionText: string) => {
    if (checkedActions.includes(actionText)) {
      setCheckedActions(checkedActions.filter((a) => a !== actionText));
    } else {
      setCheckedActions([...checkedActions, actionText]);
    }
  };

  const handleSaveReview = async () => {
    setSaving(true);
    try {
      const updated = await api.updateReviewState(workRecId, {
        status,
        checked_actions: checkedActions,
        auditor_notes: auditorNotes,
        auditor_name: currentUser?.name || reviewState?.auditor_name || 'Authorized Auditor',
      });
      setReviewState(updated);
      showToast(
        'Review State Saved',
        'Checklist items and audit observations persisted to SQLite.',
        'success'
      );
    } catch (err: any) {
      console.error('Failed to save review:', err);
      showToast('Save Failed', err.message || 'Unable to persist review state.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Lifecycle milestone derivations
  const evidence = dossier?.five_questions?.q4_supporting_evidence || {};
  const daysRec = Number(evidence.days_rec_to_sanction || 0);
  const daysSanc = Number(evidence.days_since_sanction || 0);
  const sancAmt = Number(dossier?.sanction_amount || 0);
  const disbAmt = Number(dossier?.total_disbursed || 0);

  const isSanctionBreached = daysRec > 45;
  const isMobilizationStalled = daysSanc > 90 && disbAmt === 0;
  const isExecutionOverdue = daysSanc > 365;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-black/85 backdrop-blur-md animate-fadeIn"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-[#0F172A] border border-slate-700/80 rounded-2xl w-full max-w-5xl xl:max-w-6xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden relative">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#131D31]">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-red-500/15 border border-red-500/30 text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center space-x-2.5">
                <h2 className="text-base font-bold text-white font-mono flex items-center space-x-1.5">
                  <span>Governance Dossier #{workRecId}</span>
                </h2>
                <button
                  onClick={handleCopyId}
                  title="Copy Work ID"
                  className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 text-[10px] font-mono transition-colors"
                >
                  {copiedId ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy ID</span>
                    </>
                  )}
                </button>
                {dossier && <PriorityBadge priority={dossier.priority} size="sm" />}
              </div>
              <p className="text-xs text-slate-400">
                Statutory Explainable Audit Review &amp; AC-19 Vigilance File
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <a
              href={api.getDossierHtmlUrl(workRecId)}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition-colors"
            >
              <Printer className="w-3.5 h-3.5 text-sky-400" />
              <span>Print / Export HTML</span>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-20 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400 font-mono">Synthesizing 5-Question Governance Dossier...</p>
            </div>
          ) : errorMsg ? (
            <div className="py-12 px-6 max-w-lg mx-auto text-center space-y-4 bg-[#131D31] border border-slate-800 rounded-2xl">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 mx-auto">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Jurisdiction Boundary Enforced</h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Work #{workRecId} is outside your active territorial tenant boundary ({currentUser?.organization || currentUser?.role}).
                </p>
              </div>
              <div className="pt-2">
                <button
                  onClick={async () => {
                    await switchPersona('central_auditor');
                    showToast('Switched to Central Auditor', 'All-India audit clearance enabled.', 'info');
                  }}
                  className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-colors shadow-md shadow-sky-600/20"
                >
                  Switch to Central Auditor (All-India Access)
                </button>
              </div>
            </div>
          ) : dossier ? (
            <>
              {/* Project Meta Bar */}
              <div className="bg-[#131D31] border border-slate-800 rounded-xl p-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                <div>
                  <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Location</span>
                  <span className="font-semibold text-slate-200 flex items-center space-x-1 mt-0.5 font-sans">
                    <MapPin className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                    <span className="truncate">{dossier.ida_name}, {dossier.state_name}</span>
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Recommending MP</span>
                  <span className="font-semibold text-slate-200 flex items-center space-x-1 mt-0.5 font-sans">
                    <User className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                    <span className="truncate">{dossier.mp_name}</span>
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Sanction Budget</span>
                  <span className="font-semibold text-emerald-400 mt-0.5 block">
                    ₹{dossier.sanction_amount.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Total Disbursed</span>
                  <span className="font-semibold text-sky-400 mt-0.5 block">
                    ₹{dossier.total_disbursed.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Work Description */}
              <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-500 block">Official Project Description</span>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">{dossier.description}</p>
              </div>

              {/* EXPLAINABLE RISK ENGINE (0-100 Score & Diagnostic Signal Breakdown) */}
              <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center space-x-2">
                    <ShieldAlert className={clsx(
                      'w-4 h-4',
                      (dossier.risk_score ?? 0) >= 75 ? 'text-red-400' : (dossier.risk_score ?? 0) >= 50 ? 'text-orange-400' : 'text-emerald-400'
                    )} />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      Explainable Risk Diagnostics • 0–100 Assessment
                    </h3>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <span className="text-[9px] text-slate-500 uppercase font-mono block">Numerical Risk Score</span>
                      <span className={clsx(
                        'text-base font-extrabold font-mono',
                        (dossier.risk_score ?? 0) >= 75 ? 'text-red-400' : (dossier.risk_score ?? 0) >= 50 ? 'text-orange-400' : 'text-emerald-400'
                      )}>
                        {dossier.risk_score ?? 35} / 100
                      </span>
                    </div>
                    <PriorityBadge priority={dossier.priority} size="md" />
                  </div>
                </div>

                {/* Risk Progress Bar */}
                <div className="space-y-1">
                  <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800 flex">
                    <div
                      className={clsx(
                        'h-full transition-all duration-500 rounded-full',
                        (dossier.risk_score ?? 0) >= 75
                          ? 'bg-gradient-to-r from-orange-500 to-red-500'
                          : (dossier.risk_score ?? 0) >= 50
                          ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                          : 'bg-gradient-to-r from-emerald-500 to-sky-500'
                      )}
                      style={{ width: `${Math.max(5, dossier.risk_score ?? 35)}%` }}
                    />
                  </div>
                </div>

                {/* Individual Signals Contributing to Score */}
                <div className="space-y-2.5 pt-1">
                  <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
                    Diagnostic Signals Contributing to Score:
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    {(dossier.risk_signals || []).map((sig, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-[#0B1120] border border-slate-800 space-y-1.5 shadow-sm">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-200 flex items-center space-x-1.5">
                            <span className="font-mono text-amber-400 font-bold">+{sig.weight}</span>
                            <span>{sig.name}</span>
                          </span>
                          <PriorityBadge priority={sig.severity} size="sm" />
                        </div>
                        <p className="text-[11px] text-slate-400 leading-snug font-sans">{sig.explanation}</p>
                        <div className="pt-1 text-[10px] font-mono text-sky-400 flex items-start space-x-1 border-t border-slate-800/60 mt-1">
                          <span className="shrink-0 text-slate-500">Action:</span>
                          <span className="text-slate-300">{sig.action}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* STATUTORY LIFECYCLE MILESTONE STEPPER */}
              <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-sky-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      Statutory Lifecycle Progression &amp; SLA Milestones
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">
                    MPLADS 2023 Guidelines Rules
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-1">
                  {/* Step 1: MP Recommendation */}
                  <div className="p-3 rounded-lg bg-[#0B1120] border border-slate-800 space-y-1 relative">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 font-mono">1. Recom</span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    </div>
                    <p className="text-xs font-semibold text-slate-200 truncate">Hon. MP Letter</p>
                    <span className="text-[10px] text-slate-500 font-mono block">Formally Issued</span>
                  </div>

                  {/* Step 2: Administrative Sanction */}
                  <div
                    onClick={() => isSanctionBreached && handleOpenDetectorRule('COMP-D1')}
                    className={clsx(
                      'p-3 rounded-lg border space-y-1 relative transition-all',
                      isSanctionBreached
                        ? 'bg-red-500/10 border-red-500/40 hover:border-red-400 hover:bg-red-500/20 cursor-pointer shadow-sm'
                        : 'bg-[#0B1120] border-slate-800'
                    )}
                    title={isSanctionBreached ? 'Click to inspect statutory COMP-D1 rule' : undefined}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 font-mono">2. Sanction</span>
                      {isSanctionBreached ? (
                        <div className="flex items-center space-x-1">
                          <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-red-500/20 text-red-300 font-bold">
                            COMP-D1 →
                          </span>
                          <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                        </div>
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                    </div>
                    <p className="text-xs font-semibold text-slate-200 font-mono">{daysRec}d to Sanction</p>
                    <span className={clsx('text-[10px] font-mono block', isSanctionBreached ? 'text-red-400 font-bold' : 'text-emerald-400')}>
                      {isSanctionBreached ? `SLA Breached (+${daysRec - 45}d)` : 'Within 45d SLA'}
                    </span>
                  </div>

                  {/* Step 3: Mobilization */}
                  <div
                    onClick={() => isMobilizationStalled && handleOpenDetectorRule('COMP-D3')}
                    className={clsx(
                      'p-3 rounded-lg border space-y-1 relative transition-all',
                      isMobilizationStalled
                        ? 'bg-amber-500/10 border-amber-500/40 hover:border-amber-400 hover:bg-amber-500/20 cursor-pointer shadow-sm'
                        : 'bg-[#0B1120] border-slate-800'
                    )}
                    title={isMobilizationStalled ? 'Click to inspect statutory COMP-D3 rule' : undefined}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 font-mono">3. Mobilize</span>
                      {isMobilizationStalled ? (
                        <div className="flex items-center space-x-1">
                          <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                            COMP-D3 →
                          </span>
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        </div>
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                    </div>
                    <p className="text-xs font-semibold text-slate-200 font-mono">
                      {disbAmt > 0 ? 'Disbursed' : 'Dormant'}
                    </p>
                    <span className={clsx('text-[10px] font-mono block', isMobilizationStalled ? 'text-amber-400 font-bold' : 'text-slate-400')}>
                      {isMobilizationStalled ? 'Stalled >90d' : 'Mobilized'}
                    </span>
                  </div>

                  {/* Step 4: Execution */}
                  <div
                    onClick={() => isExecutionOverdue && handleOpenDetectorRule('COMP-D2')}
                    className={clsx(
                      'p-3 rounded-lg border space-y-1 relative transition-all',
                      isExecutionOverdue
                        ? 'bg-red-500/10 border-red-500/40 hover:border-red-400 hover:bg-red-500/20 cursor-pointer shadow-sm'
                        : 'bg-[#0B1120] border-slate-800'
                    )}
                    title={isExecutionOverdue ? 'Click to inspect statutory COMP-D2 rule' : undefined}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 font-mono">4. Execution</span>
                      {isExecutionOverdue ? (
                        <div className="flex items-center space-x-1">
                          <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-red-500/20 text-red-300 font-bold">
                            COMP-D2 →
                          </span>
                          <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                        </div>
                      ) : (
                        <Clock className="w-3.5 h-3.5 text-sky-400" />
                      )}
                    </div>
                    <p className="text-xs font-semibold text-slate-200 font-mono">{daysSanc}d Active</p>
                    <span className={clsx('text-[10px] font-mono block', isExecutionOverdue ? 'text-red-400 font-bold' : 'text-sky-400')}>
                      {isExecutionOverdue ? 'Overdue (>365d)' : 'In Execution'}
                    </span>
                  </div>

                  {/* Step 5: Handover */}
                  <div className="p-3 rounded-lg bg-[#0B1120] border border-slate-800 space-y-1 relative">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-400 font-mono">5. Handover</span>
                      <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                    <p className="text-xs font-semibold text-slate-200 truncate">Social Audit</p>
                    <span className="text-[10px] text-slate-500 font-mono block">Asset Geotag</span>
                  </div>
                </div>
              </div>

              {/* 5 Core Governance Questions */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-xs font-bold text-sky-400 uppercase tracking-wider font-mono">
                  <FileText className="w-4 h-4" />
                  <span>The 5 Core Statutory Governance Questions</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Q1 */}
                  <div className="bg-[#131D31] border border-slate-800 rounded-xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">Q1: What was detected?</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-mono">Deviation</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed bg-[#0B1120] p-3 rounded-lg border border-slate-800">
                      {dossier.five_questions.q1_what_happened}
                    </p>
                  </div>

                  {/* Q2 */}
                  <div className="bg-[#131D31] border border-slate-800 rounded-xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">Q2: Why is it unusual?</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono">Variance</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed bg-[#0B1120] p-3 rounded-lg border border-slate-800">
                      {dossier.five_questions.q2_why_unusual}
                    </p>
                  </div>

                  {/* Q3 */}
                  <div className="bg-[#131D31] border border-slate-800 rounded-xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">Q3: Compared with what baseline?</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 font-mono">Statutory Baseline</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed bg-[#0B1120] p-3 rounded-lg border border-slate-800">
                      {dossier.five_questions.q3_compared_with_what}
                    </p>
                  </div>

                  {/* Q4 / Q5: Analytical Limitations */}
                  <div className="bg-[#131D31] border border-slate-800 rounded-xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">Q4: Analytical Limitations</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">Boundaries</span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed bg-[#0B1120] p-3 rounded-lg border border-slate-800">
                      {dossier.five_questions.q5_limitations}
                    </p>
                  </div>
                </div>
              </div>

              {/* AC-19 Action Checklist */}
              <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckSquare className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-bold text-white">
                      {canEditReviews
                        ? 'Prescribed AC-19 Action Checklist for Reviewing Authority'
                        : 'Public Milestone & Social Audit Verification Checklist'}
                    </h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-400">Status:</span>
                    {canEditReviews ? (
                      <select
                        value={status}
                        onChange={(e) => setStatus(e.target.value as any)}
                        className="bg-slate-900 text-xs font-medium text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1 focus:ring-1 focus:ring-sky-500 cursor-pointer"
                      >
                        <option value="UNDER_REVIEW">UNDER REVIEW</option>
                        <option value="DQM_DISPATCHED">DQM INSPECTION DISPATCHED</option>
                        <option value="RESOLVED">RESOLVED / VERIFIED OK</option>
                        <option value="ESCALATED_TO_CAG">ESCALATED TO STATE / CAG</option>
                      </select>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full bg-sky-500/15 text-sky-400 border border-sky-500/30 text-xs font-mono font-bold">
                        {status.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  {dossier.next_review_actions.map((action, idx) => {
                    const isChecked = checkedActions.includes(action);
                    return (
                      <div
                        key={idx}
                        onClick={() => canEditReviews && toggleAction(action)}
                        className={clsx(
                          'flex items-start space-x-3 p-3 rounded-lg border transition-colors',
                          canEditReviews ? 'cursor-pointer hover:border-slate-600' : 'cursor-default',
                          isChecked
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                            : 'bg-[#0B1120] border-slate-800 text-slate-300'
                        )}
                      >
                        <div className="mt-0.5">
                          {isChecked ? (
                            <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-500 shrink-0" />
                          )}
                        </div>
                        <span className="text-xs leading-relaxed select-none">{action}</span>
                      </div>
                    );
                  })}
                </div>

                {canEditReviews ? (
                  <>
                    {/* Auditor Notes Field */}
                    <div className="space-y-2 pt-2">
                      <label className="text-xs font-medium text-slate-400 block">
                        Reviewing Officer Findings &amp; Remarks (Persisted to SQLite):
                      </label>
                      <textarea
                        rows={2}
                        value={auditorNotes}
                        onChange={(e) => setAuditorNotes(e.target.value)}
                        placeholder="Enter inspection findings, measurement book cross-check notes, or justification..."
                        className="w-full bg-[#0B1120] border border-slate-700/80 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 resize-none font-sans"
                      />
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        onClick={handleSaveReview}
                        disabled={saving}
                        className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-lg shadow-sky-600/20 transition-all disabled:opacity-50"
                      >
                        <Save className="w-3.5 h-3.5" />
                        <span>{saving ? 'Saving...' : 'Save Review Action to SQLite'}</span>
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 font-mono">
                    ℹ️ Public Citizen / Parliamentary View: Formal administrative milestone sign-offs and DQM dispatch orders are reserved for authorized District Authorities &amp; State Oversight Officers.
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-slate-400">Failed to load dossier record.</div>
          )}
        </div>
      </div>

      {/* Explanatory Statutory Detector Rule Modal */}
      {selectedRule && (
        <DetectorDetailModal
          detector={selectedRule}
          onClose={() => setSelectedRule(null)}
        />
      )}
    </div>
  );
};
