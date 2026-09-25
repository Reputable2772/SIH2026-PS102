import React, { useState, useEffect } from 'react';
import {
  MessageSquareCode,
  Search,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Clock,
  AlertTriangle,
  DollarSign,
  FileText,
  Filter,
  CheckCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import clsx from 'clsx';

interface NaturalQueryResult {
  query: string;
  parsed_filters: string[];
  summary: string;
  count: number;
  metrics: {
    total_sanctioned: number;
    total_disbursed: number;
    utilization_pct: number;
    avg_turnaround_days: number;
    critical_risk_count: number;
  };
  results: {
    work_rec_id: string;
    description: string;
    state_name: string;
    district_name: string;
    mp_name: string;
    sanction_amount: number;
    total_disbursed: number;
    turnaround_days: number;
    priority: string;
    status: string;
  }[];
}

interface NaturalAnalyticsPageProps {
  onOpenDossier: (recId: string) => void;
}

export const NaturalAnalyticsPage: React.FC<NaturalAnalyticsPageProps> = ({ onOpenDossier }) => {
  const { authFetch } = useAuth();
  const { showToast } = useToast();

  const [queryInput, setQueryInput] = useState<string>('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [queryData, setQueryData] = useState<NaturalQueryResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Fetch query suggestions
    authFetch('/api/analytics/suggestions')
      .then((res: Response) => res.json())
      .then((data: string[]) => setSuggestions(data))
      .catch(() => {});

    // Run default query
    handleRunQuery('Show delayed road works in Maharashtra above 20 lakh');
  }, []);

  const handleRunQuery = async (queryString: string) => {
    if (!queryString.trim()) return;
    try {
      setLoading(true);
      setQueryInput(queryString);
      const res = await authFetch('/api/analytics/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryString }),
      });

      if (res.ok) {
        setQueryData(await res.json());
      } else {
        showToast('Query evaluation failed', 'error');
      }
    } catch {
      showToast('Error communicating with analytics core', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <MessageSquareCode className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              Natural-Language Analytics Assistant
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              Pillar 15 (JanSetu AI)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Query across 102k+ canonical works using conversational natural language prompts with instant semantic filtering.
          </p>
        </div>
      </div>

      {/* Query Bar */}
      <div className="space-y-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleRunQuery(queryInput);
          }}
          className="relative flex items-center"
        >
          <Search className="w-5 h-5 text-slate-400 absolute left-4" />
          <input
            type="text"
            placeholder="Ask anything (e.g. 'Show delayed drinking water works in Maharashtra above 15 lakh')..."
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            className="w-full pl-12 pr-28 py-3.5 bg-slate-900/90 border border-slate-700/80 rounded-2xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 shadow-xl"
          />
          <button
            type="submit"
            disabled={loading || !queryInput.trim()}
            className="absolute right-2 px-4 py-2 bg-sky-500 text-slate-950 font-bold rounded-xl text-xs hover:bg-sky-400 disabled:opacity-50 transition-all flex items-center space-x-1.5"
          >
            <span>Query</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500 font-mono flex items-center space-x-1">
            <Sparkles className="w-3 h-3 text-sky-400" />
            <span>Try:</span>
          </span>
          {suggestions.map((sug, idx) => (
            <button
              key={idx}
              onClick={() => handleRunQuery(sug)}
              className="text-xs px-2.5 py-1 bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 hover:border-sky-500/30 rounded-lg transition-all"
            >
              {sug}
            </button>
          ))}
        </div>
      </div>

      {/* Results Content Area */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center text-xs text-slate-400">
          Analyzing natural language query intent across 102k+ canonical works...
        </div>
      ) : queryData ? (
        <div className="flex-1 flex flex-col space-y-4 overflow-hidden">
          {/* Query Summary & Parsed Filters */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">
                {queryData.summary}
              </span>
              <span className="text-xs font-mono font-bold text-sky-400">
                {queryData.count} Matching Works
              </span>
            </div>

            {queryData.parsed_filters.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {queryData.parsed_filters.map((f, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-300 border border-sky-500/20 flex items-center space-x-1"
                  >
                    <Filter className="w-2.5 h-2.5" />
                    <span>{f}</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Sanctioned</span>
              <span className="text-sm font-bold text-slate-200 font-mono">
                ₹{(queryData.metrics.total_sanctioned / 100000).toFixed(1)}L
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Disbursed</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">
                ₹{(queryData.metrics.total_disbursed / 100000).toFixed(1)}L
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Utilization</span>
              <span className="text-sm font-bold text-sky-400 font-mono">
                {queryData.metrics.utilization_pct}%
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Avg Turnaround</span>
              <span className="text-sm font-bold text-slate-200 font-mono">
                {queryData.metrics.avg_turnaround_days} Days
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Critical Priority</span>
              <span className="text-sm font-bold text-red-400 font-mono">
                {queryData.metrics.critical_risk_count} Works
              </span>
            </div>
          </div>

          {/* Works Table */}
          <div className="flex-1 bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden flex flex-col">
            <div className="p-3 border-b border-slate-800 bg-slate-950/40 text-xs font-mono text-slate-400 flex items-center justify-between">
              <span>PROJECT RESULTS PREVIEW (TOP {queryData.results.length})</span>
              <span>CLICK ROW TO INSPECT DOSSIER</span>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
              {queryData.results.map((r) => (
                <div
                  key={r.work_rec_id}
                  onClick={() => onOpenDossier(r.work_rec_id)}
                  className="p-3 hover:bg-slate-800/40 cursor-pointer flex items-center justify-between transition-all group"
                >
                  <div className="space-y-1 flex-1 pr-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] font-mono text-slate-500">#{r.work_rec_id}</span>
                      <span className="text-[11px] font-semibold text-slate-400">
                        {r.district_name}, {r.state_name}
                      </span>
                      <span
                        className={clsx(
                          'text-[10px] font-mono px-1.5 py-0.2 rounded font-bold',
                          r.priority === 'CRITICAL'
                            ? 'bg-red-500/20 text-red-400'
                            : r.priority === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-slate-800 text-slate-400'
                        )}
                      >
                        {r.priority}
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 font-medium group-hover:text-sky-300 transition-colors">
                      {r.description}
                    </p>
                  </div>

                  <div className="flex items-center space-x-6 text-xs text-right shrink-0">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Sanction</span>
                      <span className="font-mono font-bold text-slate-200">
                        ₹{(r.sanction_amount / 100000).toFixed(1)}L
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Turnaround</span>
                      <span className="font-mono text-slate-400">{r.turnaround_days}d</span>
                    </div>
                    <FileText className="w-4 h-4 text-slate-500 group-hover:text-sky-400" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
