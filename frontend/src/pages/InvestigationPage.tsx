import React, { useState, useEffect } from 'react';
import {
  Kanban,
  AlertCircle,
  Clock,
  MapPin,
  ChevronRight,
  ChevronLeft,
  FileText,
  User,
  Shield,
  MessageSquare,
  Sparkles,
  Search,
  CheckCircle,
  ExternalLink,
  X,
  Plus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import clsx from 'clsx';

interface EvidenceNote {
  author: string;
  text: string;
  timestamp: string;
}

interface CaseHistory {
  id: number;
  from_stage: string | null;
  to_stage: string;
  changed_by: string;
  notes: string;
  created_at: string;
}

interface InvestigationCase {
  case_id: string;
  work_rec_id: string;
  title: string;
  stage: string;
  risk_score: number;
  priority: string;
  assigned_to: string;
  assigned_agency: string;
  state_name: string;
  district_name: string;
  category: string;
  sanction_amount: number;
  evidence_notes: EvidenceNote[];
  findings: string;
  calibration_feedback: string;
  created_at: string;
  updated_at: string;
  history?: CaseHistory[];
}

const STAGES = [
  { id: 'FLAGGED', label: 'Flagged', color: 'border-red-500/50 bg-red-500/5 text-red-400' },
  { id: 'UNDER_REVIEW', label: 'Under Review', color: 'border-amber-500/50 bg-amber-500/5 text-amber-400' },
  { id: 'FIELD_VERIFICATION', label: 'Field Verify', color: 'border-sky-500/50 bg-sky-500/5 text-sky-400' },
  { id: 'ESCALATED', label: 'Escalated (CAG)', color: 'border-purple-500/50 bg-purple-500/5 text-purple-400' },
  { id: 'RESOLVED_CLEARED', label: 'Cleared', color: 'border-emerald-500/50 bg-emerald-500/5 text-emerald-400' },
  { id: 'CLOSED', label: 'Closed', color: 'border-slate-600 bg-slate-800/40 text-slate-400' },
];

interface InvestigationPageProps {
  onOpenDossier: (recId: string) => void;
}

export const InvestigationPage: React.FC<InvestigationPageProps> = ({ onOpenDossier }) => {
  const { authFetch, currentUser } = useAuth();
  const { showToast } = useToast();

  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCase, setSelectedCase] = useState<InvestigationCase | null>(null);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);

  // Note & calibration state
  const [newNote, setNewNote] = useState<string>('');
  const [calibFeedback, setCalibFeedback] = useState<string>('CONFIRMED_ANOMALY');
  const [calibFindings, setCalibFindings] = useState<string>('');

  const fetchCases = async () => {
    try {
      setLoading(true);
      const [casesRes, sumRes] = await Promise.all([
        authFetch('/api/investigations'),
        authFetch('/api/investigations/summary'),
      ]);

      if (casesRes.ok) setCases(await casesRes.json());
      if (sumRes.ok) setSummary(await sumRes.json());
    } catch (err) {
      showToast('Failed to load investigation cases', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleStageTransition = async (caseId: string, toStage: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      const res = await authFetch(`/api/investigations/${caseId}/stage`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_stage: toStage,
          notes: `Transitioned stage to ${toStage} by ${currentUser?.name || 'auditor'}`,
        }),
      });

      if (res.ok) {
        const updated = await res.json();
        showToast(`Case moved to ${toStage}`, 'success');
        setCases((prev) => prev.map((c) => (c.case_id === caseId ? { ...c, stage: toStage } : c)));
        if (selectedCase && selectedCase.case_id === caseId) {
          setSelectedCase(updated);
        }
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to update stage', 'error');
      }
    } catch (err) {
      showToast('Error changing case stage', 'error');
    }
  };

  const handleAddNote = async () => {
    if (!selectedCase || !newNote.trim()) return;
    try {
      const res = await authFetch(`/api/investigations/${selectedCase.case_id}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: newNote }),
      });
      if (res.ok) {
        const updated = await res.json();
        showToast('Evidence note added', 'success');
        setSelectedCase(updated);
        setNewNote('');
        setCases((prev) => prev.map((c) => (c.case_id === updated.case_id ? updated : c)));
      }
    } catch (err) {
      showToast('Failed to add evidence note', 'error');
    }
  };

  const handleCalibrateModel = async () => {
    if (!selectedCase || !calibFindings.trim()) return;
    try {
      const res = await authFetch(`/api/investigations/${selectedCase.case_id}/calibrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feedback: calibFeedback,
          findings: calibFindings,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        showToast('AI Risk calibration submitted! Model feedback recorded.', 'success');
        setSelectedCase(updated);
        setCalibFindings('');
        setCases((prev) => prev.map((c) => (c.case_id === updated.case_id ? updated : c)));
        // Refresh summary
        const sumRes = await authFetch('/api/investigations/summary');
        if (sumRes.ok) setSummary(await sumRes.json());
      }
    } catch (err) {
      showToast('Failed to submit model calibration', 'error');
    }
  };

  const openCaseDetail = async (c: InvestigationCase) => {
    try {
      const res = await authFetch(`/api/investigations/${c.case_id}`);
      if (res.ok) {
        setSelectedCase(await res.json());
      } else {
        setSelectedCase(c);
      }
    } catch {
      setSelectedCase(c);
    }
    setDrawerOpen(true);
  };

  const filteredCases = cases.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.title.toLowerCase().includes(q) ||
      c.work_rec_id.includes(q) ||
      c.district_name.toLowerCase().includes(q) ||
      c.assigned_to.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 space-y-4">
      {/* Header & Pipeline KPI Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Kanban className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              Investigation Center & Kanban Workflow
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              Pillars 7, 9, 17, 18 (Nirikshak AI / Sentinel)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Detect &rarr; Explain &rarr; Review &rarr; Field Verify &rarr; Resolve lifecycle with continuous human-in-the-loop AI model calibration.
          </p>
        </div>

        {summary && (
          <div className="flex items-center space-x-3 overflow-x-auto">
            <div className="px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl">
              <p className="text-[10px] text-slate-400 uppercase font-mono">Active Cases</p>
              <p className="text-sm font-bold text-slate-100">{summary.total_active_cases}</p>
            </div>
            <div className="px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl">
              <p className="text-[10px] text-slate-400 uppercase font-mono">Funds Under Review</p>
              <p className="text-sm font-bold text-amber-400">
                ₹{(summary.total_funds_under_investigation / 100000).toFixed(1)}L
              </p>
            </div>
            {summary.model_calibration && (
              <div className="px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl">
                <p className="text-[10px] text-slate-400 uppercase font-mono">AI Calibration Precision</p>
                <p className="text-sm font-bold text-emerald-400">
                  {summary.model_calibration.precision_rate_pct}% ({summary.model_calibration.confirmed_anomalies} confirmed)
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        <input
          type="text"
          placeholder="Filter by title, Rec ID, district, or assigned officer..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-3 py-1.5 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
        />
      </div>

      {/* Kanban Board 6-Stage Columns */}
      <div className="flex-1 flex gap-4 overflow-x-auto pb-2">
        {STAGES.map((col, colIdx) => {
          const stageCases = filteredCases.filter((c) => c.stage === col.id);

          return (
            <div
              key={col.id}
              className="w-72 shrink-0 flex flex-col bg-slate-900/50 border border-slate-800/80 rounded-2xl overflow-hidden"
            >
              {/* Column Header */}
              <div className={clsx('p-3 border-b flex items-center justify-between', col.color)}>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-xs uppercase tracking-wider">{col.label}</span>
                  <span className="text-[11px] font-mono px-1.5 py-0.2 rounded-full bg-slate-950/60 font-semibold">
                    {stageCases.length}
                  </span>
                </div>
              </div>

              {/* Column Cards Container */}
              <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5">
                {stageCases.map((c) => (
                  <div
                    key={c.case_id}
                    onClick={() => openCaseDetail(c)}
                    className="p-3 bg-slate-950/70 border border-slate-800 hover:border-slate-700 rounded-xl space-y-2.5 cursor-pointer transition-all shadow-sm hover:shadow-md group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-slate-500">#{c.work_rec_id}</span>
                      <span
                        className={clsx(
                          'text-[10px] font-mono font-bold px-1.5 py-0.5 rounded',
                          c.risk_score >= 85
                            ? 'bg-red-500/20 text-red-400'
                            : c.risk_score >= 70
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-sky-500/20 text-sky-400'
                        )}
                      >
                        RISK {Math.round(c.risk_score)}
                      </span>
                    </div>

                    <p className="text-xs text-slate-200 font-medium line-clamp-2 leading-snug">
                      {c.title}
                    </p>

                    <div className="space-y-1 text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
                      <div className="flex items-center justify-between">
                        <span>₹{(c.sanction_amount / 100000).toFixed(1)}L</span>
                        <span className="text-slate-500">{c.district_name}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-slate-500 truncate">
                        <User className="w-3 h-3 shrink-0" />
                        <span className="truncate">{c.assigned_to}</span>
                      </div>
                    </div>

                    {/* Quick Move Chevron Controls */}
                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/40 opacity-70 group-hover:opacity-100 transition-opacity">
                      {colIdx > 0 ? (
                        <button
                          onClick={(e) => handleStageTransition(c.case_id, STAGES[colIdx - 1].id, e)}
                          title={`Move back to ${STAGES[colIdx - 1].label}`}
                          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                        >
                          <ChevronLeft className="w-3.5 h-3.5" />
                        </button>
                      ) : <div />}

                      {colIdx < STAGES.length - 1 ? (
                        <button
                          onClick={(e) => handleStageTransition(c.case_id, STAGES[colIdx + 1].id, e)}
                          title={`Advance to ${STAGES[colIdx + 1].label}`}
                          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-sky-300"
                        >
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      ) : <div />}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Case Detail & Evidence Drawer */}
      {drawerOpen && selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full flex flex-col p-6 overflow-y-auto space-y-5">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs font-mono text-slate-500">{selectedCase.case_id}</span>
                <h2 className="text-base font-bold text-slate-100">{selectedCase.title}</h2>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Actions & Status */}
            <div className="flex items-center justify-between bg-slate-950/60 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Current Stage</span>
                <span className="text-xs font-bold text-sky-400 font-mono">{selectedCase.stage}</span>
              </div>
              <button
                onClick={() => onOpenDossier(selectedCase.work_rec_id)}
                className="px-3 py-1.5 rounded-lg bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs font-semibold flex items-center space-x-1.5 hover:bg-sky-500/30"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Open Work Dossier</span>
              </button>
            </div>

            {/* Stage Mover */}
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-slate-300 font-mono">Transition Case Stage:</span>
              <div className="grid grid-cols-3 gap-2">
                {STAGES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleStageTransition(selectedCase.case_id, s.id)}
                    className={clsx(
                      'text-xs py-1.5 px-2 rounded-lg border font-medium transition-all text-center',
                      selectedCase.stage === s.id
                        ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                        : 'bg-slate-950/40 text-slate-400 border-slate-800 hover:text-slate-200'
                    )}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Evidence Notes Feed */}
            <div className="space-y-2.5">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-sky-400" />
                <span>Investigation Evidence Notes</span>
              </h3>

              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {selectedCase.evidence_notes?.map((n, idx) => (
                  <div key={idx} className="p-2.5 bg-slate-950/40 border border-slate-800 rounded-lg space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                      <span className="text-sky-400 font-semibold">{n.author}</span>
                      <span>{new Date(n.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-xs text-slate-300">{n.text}</p>
                  </div>
                ))}
              </div>

              {/* Add Note Input */}
              <div className="flex space-x-2 pt-1">
                <input
                  type="text"
                  placeholder="Add site observation or evidence note..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                  className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
                <button
                  onClick={handleAddNote}
                  className="px-3 py-1.5 bg-sky-500 text-slate-950 font-bold rounded-lg text-xs hover:bg-sky-400"
                >
                  Post Note
                </button>
              </div>
            </div>

            {/* Continuous Learning AI Model Calibration Box */}
            <div className="bg-slate-950/80 border border-purple-500/30 rounded-xl p-4 space-y-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-purple-300 font-mono uppercase">
                  Continuous AI Calibration (Pillar 18)
                </h3>
              </div>
              <p className="text-[11px] text-slate-400">
                Ground-truth feedback from investigators recalibrates the multi-vector risk engine weights.
              </p>

              <div className="flex space-x-2">
                {['CONFIRMED_ANOMALY', 'FALSE_POSITIVE', 'POLICY_EXEMPTION'].map((fb) => (
                  <button
                    key={fb}
                    onClick={() => setCalibFeedback(fb)}
                    className={clsx(
                      'text-[11px] px-2.5 py-1 rounded-lg border font-mono',
                      calibFeedback === fb
                        ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                        : 'bg-slate-900 text-slate-400 border-slate-800'
                    )}
                  >
                    {fb.replace('_', ' ')}
                  </button>
                ))}
              </div>

              <textarea
                rows={2}
                placeholder="Ground audit findings (e.g. physical works delayed due to land acquisition dispute)..."
                value={calibFindings}
                onChange={(e) => setCalibFindings(e.target.value)}
                className="w-full p-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />

              <button
                onClick={handleCalibrateModel}
                disabled={!calibFindings.trim()}
                className="w-full py-1.5 rounded-lg bg-purple-600 text-white font-semibold text-xs hover:bg-purple-500 disabled:opacity-50 transition-all"
              >
                Submit Ground Truth & Recalibrate Engine
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
