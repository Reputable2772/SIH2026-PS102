import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  FileText,
  Copy,
  Printer,
  CheckCircle2,
  AlertCircle,
  Building2,
  Users,
  DollarSign,
  Filter,
  Send,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import clsx from 'clsx';

interface PriorityRecommendation {
  recommendation_id: string;
  title: string;
  category: string;
  target_demographic: string;
  quota_tag: string;
  urgency_score: number;
  priority_tier: string;
  estimated_budget: number;
  estimated_beneficiaries: number;
  district_name: string;
  state_name: string;
  rationale: string;
  statutory_compliance_clause: string;
}

interface DraftLetter {
  ref_no: string;
  date: string;
  mp_name: string;
  constituency: string;
  district_authority: string;
  total_recommended_amount: number;
  itemized_works: any[];
  full_text: string;
}

export const RecommendationsPage: React.FC = () => {
  const { authFetch, currentUser } = useAuth();
  const { showToast } = useToast();

  const [recommendations, setRecommendations] = useState<PriorityRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [quotaFilter, setQuotaFilter] = useState<string>('ALL');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [draftLetter, setDraftLetter] = useState<DraftLetter | null>(null);
  const [letterModalOpen, setLetterModalOpen] = useState<boolean>(false);
  const [generatingLetter, setGeneratingLetter] = useState<boolean>(false);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const url = quotaFilter === 'ALL'
        ? '/api/recommendations'
        : `/api/recommendations?quota_focus=${quotaFilter}`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data);
        if (selectedIds.length === 0 && data.length > 0) {
          // Pre-select top 2 by default
          setSelectedIds([data[0].recommendation_id, data[1]?.recommendation_id].filter(Boolean));
        }
      }
    } catch {
      showToast('Failed to load AI recommendations', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [quotaFilter]);

  const toggleSelect = (recId: string) => {
    setSelectedIds((prev) =>
      prev.includes(recId) ? prev.filter((id) => id !== recId) : [...prev, recId]
    );
  };

  const handleGenerateLetter = async () => {
    if (selectedIds.length === 0) {
      showToast('Please select at least one recommendation to include', 'error');
      return;
    }
    try {
      setGeneratingLetter(true);
      const res = await authFetch('/api/recommendations/draft-letter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_rec_ids: selectedIds,
          mp_name: currentUser?.name || 'Hon. Supriya Sule, MP',
          constituency: currentUser?.constituency || 'Baramati (Maharashtra)',
          district_authority_name: 'District Magistrate & Collector, Pune',
        }),
      });

      if (res.ok) {
        const letter = await res.json();
        setDraftLetter(letter);
        setLetterModalOpen(true);
      } else {
        showToast('Failed to generate draft recommendation letter', 'error');
      }
    } catch {
      showToast('Error generating letter', 'error');
    } finally {
      setGeneratingLetter(false);
    }
  };

  const handleCopyLetter = () => {
    if (!draftLetter) return;
    navigator.clipboard.writeText(draftLetter.full_text);
    showToast('Official recommendation letter copied to clipboard!', 'success');
  };

  const selectedTotalBudget = recommendations
    .filter((r) => selectedIds.includes(r.recommendation_id))
    .reduce((sum, r) => sum + r.estimated_budget, 0);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Sparkles className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              AI Priority Recommendations & MP Form 2B Generator
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              Pillars 12, 13, 14 (JanSetu AI / e-SAKSHI)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Synthesizes citizen demand hotspots, unspent entitlements, and statutory SC/ST quotas into high-ROI actionable project recommendations.
          </p>
        </div>

        {/* Action Panel */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Selected Allocation</span>
            <span className="text-xs font-bold text-emerald-400 font-mono">
              ₹{(selectedTotalBudget / 100000).toFixed(1)}L ({selectedIds.length} Works)
            </span>
          </div>
          <button
            onClick={handleGenerateLetter}
            disabled={generatingLetter || selectedIds.length === 0}
            className="px-4 py-2 bg-sky-500 text-slate-950 font-bold rounded-xl text-xs hover:bg-sky-400 flex items-center space-x-2 transition-all shadow-lg shadow-sky-500/10 disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            <span>Generate Official Draft Letter</span>
          </button>
        </div>
      </div>

      {/* Filter Chips */}
      <div className="flex items-center space-x-2">
        <Filter className="w-3.5 h-3.5 text-slate-500" />
        <span className="text-xs font-mono text-slate-400">Demographic Quota Focus:</span>
        {['ALL', 'SC', 'ST', 'GENERAL'].map((q) => (
          <button
            key={q}
            onClick={() => setQuotaFilter(q)}
            className={clsx(
              'text-xs px-3 py-1 rounded-lg border font-medium transition-all',
              quotaFilter === q
                ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            )}
          >
            {q === 'ALL' ? 'All Sectors' : `${q} Quota`}
          </button>
        ))}
      </div>

      {/* Recommendations Cards Grid */}
      <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
        {loading ? (
          <div className="col-span-full text-center py-12 text-xs text-slate-400">
            Synthesizing local infrastructure gaps and citizen demand...
          </div>
        ) : (
          recommendations.map((rec) => {
            const isSelected = selectedIds.includes(rec.recommendation_id);

            return (
              <div
                key={rec.recommendation_id}
                onClick={() => toggleSelect(rec.recommendation_id)}
                className={clsx(
                  'p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-3',
                  isSelected
                    ? 'bg-sky-500/10 border-sky-500/40 shadow-sm'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                )}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span
                      className={clsx(
                        'text-[10px] font-mono font-bold px-2 py-0.5 rounded-full',
                        rec.urgency_score >= 90
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      )}
                    >
                      URGENCY {rec.urgency_score} / 100
                    </span>

                    <span
                      className={clsx(
                        'text-[10px] font-mono px-2 py-0.5 rounded-full uppercase font-bold',
                        rec.quota_tag === 'SC'
                          ? 'bg-sky-500/20 text-sky-300'
                          : rec.quota_tag === 'ST'
                          ? 'bg-purple-500/20 text-purple-300'
                          : 'bg-slate-800 text-slate-400'
                      )}
                    >
                      {rec.quota_tag} QUOTA
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100 leading-snug">
                    {rec.title}
                  </h3>

                  <p className="text-xs text-slate-400 leading-relaxed">
                    {rec.rationale}
                  </p>
                </div>

                <div className="space-y-2 pt-2 border-t border-slate-800/60">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Est. Allocation</span>
                      <span className="font-bold text-emerald-400 font-mono">
                        ₹{(rec.estimated_budget / 100000).toFixed(2)} Lakhs
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Beneficiaries</span>
                      <span className="font-bold text-slate-300 font-mono">
                        {rec.estimated_beneficiaries.toLocaleString()} Citizens
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-500 font-mono">{rec.recommendation_id}</span>
                    <div className="flex items-center space-x-1.5 text-xs">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // handled by card onClick
                        className="rounded accent-sky-500"
                      />
                      <span className={clsx('font-medium', isSelected ? 'text-sky-400' : 'text-slate-400')}>
                        {isSelected ? 'Included' : 'Select'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Official Form 2B Letter Modal */}
      {letterModalOpen && draftLetter && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-sky-400" />
                <h2 className="text-sm font-bold text-slate-100 font-mono uppercase">
                  MPLADS Form 2B — Official Recommendation Letter
                </h2>
              </div>
              <button
                onClick={() => setLetterModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Letter Body Preview */}
            <div className="flex-1 overflow-y-auto p-6 font-mono text-xs bg-slate-950/80 text-slate-300 whitespace-pre-wrap leading-relaxed select-text">
              {draftLetter.full_text}
            </div>

            {/* Modal Actions */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                Ref: {draftLetter.ref_no}
              </span>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleCopyLetter}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-semibold flex items-center space-x-1.5 transition-all"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Letter</span>
                </button>
                <button
                  onClick={() => window.print()}
                  className="px-3.5 py-1.5 rounded-lg bg-sky-500 text-slate-950 font-bold text-xs hover:bg-sky-400 flex items-center space-x-1.5 transition-all"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print / Export PDF</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
