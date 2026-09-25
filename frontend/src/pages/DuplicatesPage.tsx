import React, { useState, useEffect } from 'react';
import {
  CopyCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Search,
  Sliders,
  DollarSign,
  Layers,
  ArrowRight,
  ShieldAlert,
  Calendar,
  Building2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import clsx from 'clsx';

interface DuplicateProject {
  work_rec_id: string;
  description: string;
  category: string;
  sanction_amount: number;
  total_disbursed: number;
  mp_name: string;
  ida_name: string;
  vendor_name: string;
  priority: string;
  recommendation_date: string;
}

interface DuplicatePair {
  pair_id: string;
  similarity_pct: number;
  text_similarity_pct: number;
  amount_similarity_pct: number;
  state_name: string;
  district_name: string;
  category: string;
  signals: string[];
  status: string;
  project_a: DuplicateProject;
  project_b: DuplicateProject;
}

interface DuplicatesPageProps {
  onOpenDossier: (recId: string) => void;
}

export const DuplicatesPage: React.FC<DuplicatesPageProps> = ({ onOpenDossier }) => {
  const { authFetch, currentUser } = useAuth();
  const { showToast } = useToast();

  const [pairs, setPairs] = useState<DuplicatePair[]>([]);
  const [stats, setStats] = useState<{
    total_pairs_flagged: number;
    pending_review: number;
    confirmed_duplicates: number;
    marked_legitimate: number;
    potential_duplicate_funds_at_risk: number;
    high_confidence_count: number;
  } | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [minSimilarity, setMinSimilarity] = useState<number>(70);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedPair, setSelectedPair] = useState<DuplicatePair | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const canResolve = currentUser?.role === 'CENTRAL_AUDITOR' || currentUser?.role === 'DISTRICT_AUTHORITY';

  const fetchData = async () => {
    try {
      setLoading(true);
      const [pairsRes, statsRes] = await Promise.all([
        authFetch(`/api/duplicates?min_similarity=${minSimilarity}&limit=100`),
        authFetch('/api/duplicates/stats'),
      ]);

      if (pairsRes.ok) {
        const data = await pairsRes.json();
        setPairs(data);
        if (data.length > 0 && !selectedPair) {
          setSelectedPair(data[0]);
        }
      }
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
    } catch (err) {
      showToast('Failed to load duplicate works data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [minSimilarity, currentUser]);

  const handleResolve = async (pairId: string, decision: 'CONFIRMED_DUPLICATE' | 'MARKED_LEGITIMATE') => {
    try {
      setResolvingId(pairId);
      const res = await authFetch(`/api/duplicates/${pairId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          notes: resolutionNotes || `Investigation completed: marked ${decision}`,
        }),
      });

      if (res.ok) {
        showToast(
          decision === 'CONFIRMED_DUPLICATE'
            ? 'Ghost / duplicate work confirmed. Audit log updated.'
            : 'Marked legitimate (false positive). Pair resolved.',
          'success'
        );
        setResolutionNotes('');
        // Update local state
        setPairs((prev) =>
          prev.map((p) => (p.pair_id === pairId ? { ...p, status: decision } : p))
        );
        if (selectedPair && selectedPair.pair_id === pairId) {
          setSelectedPair((prev) => (prev ? { ...prev, status: decision } : null));
        }
        // Refresh summary stats
        const statsRes = await authFetch('/api/duplicates/stats');
        if (statsRes.ok) setStats(await statsRes.json());
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to record decision', 'error');
      }
    } catch (err) {
      showToast('Error recording resolution', 'error');
    } finally {
      setResolvingId(null);
    }
  };

  const filteredPairs = pairs.filter((p) => {
    if (statusFilter !== 'ALL' && p.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchA = p.project_a.description.toLowerCase().includes(q) || p.project_a.work_rec_id.includes(q);
      const matchB = p.project_b.description.toLowerCase().includes(q) || p.project_b.work_rec_id.includes(q);
      const matchDist = p.district_name.toLowerCase().includes(q);
      if (!matchA && !matchB && !matchDist) return false;
    }
    return true;
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 space-y-5">
      {/* Header & KPI Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
              <CopyCheck className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              Duplicate & Ghost Work Detection Hub
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              Pillar 4 (MPLADS Sentinel / Nirikshak AI)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Detects suspected identical works funded twice or overlapping physical assets across multi-vector attributes.
          </p>
        </div>

        {stats && (
          <div className="flex items-center space-x-3 overflow-x-auto pb-1">
            <div className="px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-mono">Flagged Pairs</p>
                <p className="text-sm font-bold text-slate-100">{stats.total_pairs_flagged}</p>
              </div>
            </div>
            <div className="px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center space-x-2">
              <DollarSign className="w-4 h-4 text-amber-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-mono">Funds at Risk</p>
                <p className="text-sm font-bold text-amber-400">
                  ₹{(stats.potential_duplicate_funds_at_risk / 100000).toFixed(1)}L
                </p>
              </div>
            </div>
            <div className="px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-mono">Confirmed</p>
                <p className="text-sm font-bold text-emerald-400">{stats.confirmed_duplicates}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-3 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search description, work ID, district..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>
          <div className="flex items-center space-x-2 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <span className="text-slate-400 font-mono">Min Similarity:</span>
            <input
              type="range"
              min="60"
              max="95"
              step="5"
              value={minSimilarity}
              onChange={(e) => setMinSimilarity(Number(e.target.value))}
              className="w-20 accent-sky-500 cursor-pointer"
            />
            <span className="font-bold text-sky-400 font-mono w-8">{minSimilarity}%</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {['ALL', 'PENDING_REVIEW', 'CONFIRMED_DUPLICATE', 'MARKED_LEGITIMATE'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-lg border transition-all font-medium',
                statusFilter === st
                  ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                  : 'bg-slate-950/40 text-slate-400 border-slate-800 hover:text-slate-200'
              )}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main Split-Screen Layout */}
      <div className="flex-1 flex gap-5 overflow-hidden">
        {/* Left Side: Pairs List */}
        <div className="w-1/3 flex flex-col bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-3 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>SUSPECTED PAIRS ({filteredPairs.length})</span>
            <span>SIMILARITY</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">Scanning project clusters...</div>
            ) : filteredPairs.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">No matching duplicate pairs found.</div>
            ) : (
              filteredPairs.map((p) => {
                const isSelected = selectedPair?.pair_id === p.pair_id;
                return (
                  <div
                    key={p.pair_id}
                    onClick={() => setSelectedPair(p)}
                    className={clsx(
                      'p-3.5 cursor-pointer transition-all hover:bg-slate-800/40 space-y-2',
                      isSelected ? 'bg-sky-500/10 border-l-4 border-sky-500' : ''
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono text-slate-400 font-semibold">
                        {p.district_name}, {p.state_name}
                      </span>
                      <span
                        className={clsx(
                          'text-xs font-bold font-mono px-2 py-0.5 rounded-full',
                          p.similarity_pct >= 85
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        )}
                      >
                        {p.similarity_pct}% MATCH
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 font-medium line-clamp-2">
                      {p.project_a.description}
                    </p>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                      <span>₹{(p.project_a.sanction_amount / 100000).toFixed(1)}L vs ₹{(p.project_b.sanction_amount / 100000).toFixed(1)}L</span>
                      <span
                        className={clsx(
                          'text-[10px] px-1.5 py-0.5 rounded uppercase font-mono font-medium',
                          p.status === 'CONFIRMED_DUPLICATE'
                            ? 'bg-red-500/20 text-red-400'
                            : p.status === 'MARKED_LEGITIMATE'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-slate-800 text-slate-400'
                        )}
                      >
                        {p.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Side: Side-by-Side Detailed Comparison Inspector */}
        <div className="flex-1 flex flex-col bg-slate-900/60 border border-slate-800 rounded-2xl overflow-y-auto p-5 space-y-5">
          {selectedPair ? (
            <>
              {/* Comparison Header & Signals Bar */}
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono text-slate-500 uppercase">
                      Forensic Pair Investigation: {selectedPair.pair_id}
                    </span>
                    <h2 className="text-base font-bold text-slate-200">
                      Multi-Vector Similarity: {selectedPair.similarity_pct}%
                    </h2>
                  </div>

                  <div className="flex items-center space-x-2">
                    <div className="text-right">
                      <span className="text-[11px] text-slate-400 font-mono block">Text Overlap</span>
                      <span className="text-xs font-bold text-sky-400 font-mono">
                        {selectedPair.text_similarity_pct}%
                      </span>
                    </div>
                    <div className="h-6 w-px bg-slate-800" />
                    <div className="text-right">
                      <span className="text-[11px] text-slate-400 font-mono block">Budget Match</span>
                      <span className="text-xs font-bold text-emerald-400 font-mono">
                        {selectedPair.amount_similarity_pct}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Flagged Signals */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {selectedPair.signals.map((sig, idx) => (
                    <span
                      key={idx}
                      className="text-[11px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-300 border border-red-500/20 flex items-center space-x-1"
                    >
                      <AlertTriangle className="w-3 h-3 text-red-400" />
                      <span>{sig}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Side-by-Side Project Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Project A */}
                <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <span className="text-xs font-mono font-bold text-sky-400">PROJECT RECORD A</span>
                    <button
                      onClick={() => onOpenDossier(selectedPair.project_a.work_rec_id)}
                      className="text-[11px] text-sky-400 hover:text-sky-300 flex items-center space-x-1"
                    >
                      <FileText className="w-3 h-3" />
                      <span>View Full Dossier</span>
                    </button>
                  </div>

                  <div className="space-y-1">
                    <p className="text-[11px] text-slate-500 font-mono">
                      REC ID: #{selectedPair.project_a.work_rec_id}
                    </p>
                    <p className="text-xs text-slate-200 leading-relaxed font-medium">
                      {selectedPair.project_a.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Sanction Amount</span>
                      <span className="font-bold text-slate-200 font-mono">
                        ₹{selectedPair.project_a.sanction_amount.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Disbursed</span>
                      <span className="font-bold text-slate-200 font-mono">
                        ₹{selectedPair.project_a.total_disbursed.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Category</span>
                      <span className="text-slate-300">{selectedPair.project_a.category}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Contractor</span>
                      <span className="text-slate-300 truncate block">{selectedPair.project_a.vendor_name}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">MP</span>
                      <span className="text-slate-300">{selectedPair.project_a.mp_name}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">District (IDA)</span>
                      <span className="text-slate-300">{selectedPair.project_a.ida_name}</span>
                    </div>
                  </div>
                </div>

                {/* Project B */}
                <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <span className="text-xs font-mono font-bold text-indigo-400">PROJECT RECORD B</span>
                    <button
                      onClick={() => onOpenDossier(selectedPair.project_b.work_rec_id)}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                    >
                      <FileText className="w-3 h-3" />
                      <span>View Full Dossier</span>
                    </button>
                  </div>

                  <div className="space-y-1">
                    <p className="text-[11px] text-slate-500 font-mono">
                      REC ID: #{selectedPair.project_b.work_rec_id}
                    </p>
                    <p className="text-xs text-slate-200 leading-relaxed font-medium">
                      {selectedPair.project_b.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Sanction Amount</span>
                      <span className="font-bold text-slate-200 font-mono">
                        ₹{selectedPair.project_b.sanction_amount.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Disbursed</span>
                      <span className="font-bold text-slate-200 font-mono">
                        ₹{selectedPair.project_b.total_disbursed.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Category</span>
                      <span className="text-slate-300">{selectedPair.project_b.category}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Contractor</span>
                      <span className="text-slate-300 truncate block">{selectedPair.project_b.vendor_name}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">MP</span>
                      <span className="text-slate-300">{selectedPair.project_b.mp_name}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">District (IDA)</span>
                      <span className="text-slate-300">{selectedPair.project_b.ida_name}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Investigator Action Panel */}
              {canResolve && (
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                    Investigator Adjudication
                  </h3>
                  <textarea
                    rows={2}
                    placeholder="Enter audit findings, site inspection notes, or justification..."
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    className="w-full p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  />

                  <div className="flex items-center justify-end space-x-3">
                    <button
                      disabled={resolvingId === selectedPair.pair_id}
                      onClick={() => handleResolve(selectedPair.pair_id, 'MARKED_LEGITIMATE')}
                      className="px-3.5 py-1.5 rounded-lg border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 text-xs font-semibold flex items-center space-x-1.5 transition-all"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Mark Legitimate (False Positive)</span>
                    </button>

                    <button
                      disabled={resolvingId === selectedPair.pair_id}
                      onClick={() => handleResolve(selectedPair.pair_id, 'CONFIRMED_DUPLICATE')}
                      className="px-3.5 py-1.5 rounded-lg bg-red-500/20 text-red-300 border border-red-500/40 hover:bg-red-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-all"
                    >
                      <XCircle className="w-3.5 h-3.5 text-red-400" />
                      <span>Confirm Ghost / Duplicate Work</span>
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 space-y-2">
              <CopyCheck className="w-8 h-8 opacity-40" />
              <p className="text-xs">Select a suspected pair from the left panel to inspect.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
