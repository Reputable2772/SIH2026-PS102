import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileCheck2,
  Clock,
  Ban,
  TrendingDown,
  Info,
  Building,
  FileText,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import clsx from 'clsx';

interface StatutoryChecklistItem {
  rule: string;
  status: string;
  value: string;
  clause: string;
}

interface ProhibitedWork {
  work_rec_id: string;
  description: string;
  sanction_amount: number;
  state_name: string;
  district_name: string;
  rule_violated: string;
  guideline_ref: string;
  severity: string;
}

interface ComplianceData {
  overall_compliance_score: number;
  overall_status: string;
  total_works_evaluated: number;
  total_sanction_evaluated: number;
  sc_allocation: {
    target_pct: number;
    actual_pct: number;
    actual_amount: number;
    status: string;
    deficit_pct: number;
    deficit_amount: number;
    guideline_ref: string;
  };
  st_allocation: {
    target_pct: number;
    actual_pct: number;
    actual_amount: number;
    status: string;
    deficit_pct: number;
    deficit_amount: number;
    guideline_ref: string;
  };
  sla_performance: {
    sanction_adherence_pct: number;
    within_sla_count: number;
    breached_sla_count: number;
    statutory_limit_days: number;
    guideline_ref: string;
  };
  prohibited_items: {
    total_flagged: number;
    flagged_works: ProhibitedWork[];
    guideline_ref: string;
  };
  statutory_checklist: StatutoryChecklistItem[];
}

interface CompliancePageProps {
  onOpenDossier?: (recId: string) => void;
}

export const CompliancePage: React.FC<CompliancePageProps> = ({ onOpenDossier }) => {
  const { authFetch } = useAuth();
  const { showToast } = useToast();

  const [data, setData] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchCompliance = async () => {
    try {
      setLoading(true);
      const res = await authFetch('/api/compliance');
      if (res.ok) {
        setData(await res.json());
      } else {
        showToast('Failed to load compliance radar', 'error');
      }
    } catch {
      showToast('Error connecting to compliance radar', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompliance();
  }, []);

  if (loading || !data) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-xs text-slate-400">
        Evaluating statutory guidelines compliance radar...
      </div>
    );
  }

  const isScDeficit = data.sc_allocation.actual_pct < data.sc_allocation.target_pct;
  const isStDeficit = data.st_allocation.actual_pct < data.st_allocation.target_pct;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              Statutory Compliance Radar
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              Pillar 11 (MoSPI Guidelines 2023)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Monitors mandatory 15% SC & 7.5% ST habitation quotas (Para 2.5), 45-day sanction SLA, and Annexure-II ineligible work prohibitions.
          </p>
        </div>

        {/* Overall Score Badge */}
        <div className="flex items-center space-x-3 bg-slate-900/80 border border-slate-800 px-4 py-2 rounded-2xl">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Overall Radar Score</span>
            <span
              className={clsx(
                'text-lg font-black font-mono',
                data.overall_compliance_score >= 85
                  ? 'text-emerald-400'
                  : data.overall_compliance_score >= 65
                  ? 'text-amber-400'
                  : 'text-red-400'
              )}
            >
              {data.overall_compliance_score} / 100
            </span>
          </div>
          <span
            className={clsx(
              'text-xs font-bold font-mono px-2 py-1 rounded-lg',
              data.overall_status === 'COMPLIANT'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
            )}
          >
            {data.overall_status}
          </span>
        </div>
      </div>

      {/* Primary Statutory Quotas Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* SC Allocation Quota Card (Para 2.5) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-sky-400">PARA 2.5: SC ALLOCATION</span>
            <span
              className={clsx(
                'text-[10px] font-mono font-bold px-2 py-0.5 rounded-full',
                isScDeficit ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
              )}
            >
              {isScDeficit ? 'DEFICIT SHORTFALL' : 'STATUTORY PASS'}
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-black font-mono text-slate-100">
                {data.sc_allocation.actual_pct}%
              </span>
              <span className="text-xs text-slate-400 ml-2 font-mono">
                of ₹{(data.total_sanction_evaluated / 100000).toFixed(1)}L
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Mandatory Target</span>
              <span className="text-xs font-bold text-slate-300 font-mono">15.0% Min</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-500',
                isScDeficit ? 'bg-amber-500' : 'bg-emerald-500'
              )}
              style={{ width: `${Math.min(100, (data.sc_allocation.actual_pct / 15) * 100)}%` }}
            />
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            {isScDeficit ? (
              <span className="text-amber-300">
                Shortfall of {data.sc_allocation.deficit_pct}% (approx ₹{(data.sc_allocation.deficit_amount / 100000).toFixed(1)}L). Recommended to prioritize works in SC habitations.
              </span>
            ) : (
              <span className="text-emerald-300">
                Meets statutory 15% quota threshold under revised MoSPI 2023 guidelines.
              </span>
            )}
          </p>
        </div>

        {/* ST Allocation Quota Card (Para 2.5) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-purple-400">PARA 2.5: ST ALLOCATION</span>
            <span
              className={clsx(
                'text-[10px] font-mono font-bold px-2 py-0.5 rounded-full',
                isStDeficit ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
              )}
            >
              {isStDeficit ? 'DEFICIT SHORTFALL' : 'STATUTORY PASS'}
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-black font-mono text-slate-100">
                {data.st_allocation.actual_pct}%
              </span>
              <span className="text-xs text-slate-400 ml-2 font-mono">
                of ₹{(data.total_sanction_evaluated / 100000).toFixed(1)}L
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Mandatory Target</span>
              <span className="text-xs font-bold text-slate-300 font-mono">7.5% Min</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-500',
                isStDeficit ? 'bg-amber-500' : 'bg-emerald-500'
              )}
              style={{ width: `${Math.min(100, (data.st_allocation.actual_pct / 7.5) * 100)}%` }}
            />
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            {isStDeficit ? (
              <span className="text-amber-300">
                Shortfall of {data.st_allocation.deficit_pct}% (approx ₹{(data.st_allocation.deficit_amount / 100000).toFixed(1)}L). Recommended to prioritize works in tribal clusters.
              </span>
            ) : (
              <span className="text-emerald-300">
                Meets statutory 7.5% quota threshold under revised MoSPI 2023 guidelines.
              </span>
            )}
          </p>
        </div>

        {/* 45-Day Sanction SLA Performance (Para 3.1) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-teal-400">PARA 3.1: 45-DAY SLA</span>
            <span
              className={clsx(
                'text-[10px] font-mono font-bold px-2 py-0.5 rounded-full',
                data.sla_performance.sanction_adherence_pct >= 80
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-amber-500/20 text-amber-400'
              )}
            >
              {data.sla_performance.sanction_adherence_pct >= 80 ? 'HIGH ADHERENCE' : 'SLA BREACHES'}
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-black font-mono text-slate-100">
                {data.sla_performance.sanction_adherence_pct}%
              </span>
              <span className="text-xs text-slate-400 ml-2 font-mono">within 45 days</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Breached Works</span>
              <span className="text-xs font-bold text-red-400 font-mono">
                {data.sla_performance.breached_sla_count}
              </span>
            </div>
          </div>

          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-teal-500 transition-all duration-500"
              style={{ width: `${data.sla_performance.sanction_adherence_pct}%` }}
            />
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Statutory requirement mandates District Magistrate sanction within 45 days of MP recommendation.
          </p>
        </div>
      </div>

      {/* Statutory Checklist Table & Prohibited Items Scanner */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Statutory Compliance Checklist */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center space-x-2">
            <FileCheck2 className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase font-mono">
              Statutory Guideline Checklist
            </h2>
          </div>

          <div className="divide-y divide-slate-800">
            {data.statutory_checklist.map((item, idx) => (
              <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">{item.rule}</span>
                  <span className="text-[10px] text-slate-500 font-mono block">Clause {item.clause}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-slate-400">{item.value}</span>
                  {item.status === 'PASS' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : item.status === 'WARNING' ? (
                    <Clock className="w-4 h-4 text-amber-400 shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Prohibited Items Scanner (Annexure-II) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Ban className="w-4 h-4 text-red-400" />
              <h2 className="text-sm font-bold text-slate-200 uppercase font-mono">
                Annexure-II Prohibited Asset Scanner
              </h2>
            </div>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
              {data.prohibited_items.total_flagged} Flagged
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Automated screening against ineligible works: places of worship, commercial buildings, private clubs, and staff residential quarters.
          </p>

          <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
            {data.prohibited_items.flagged_works.map((pw) => (
              <div
                key={pw.work_rec_id}
                className="p-3 bg-slate-950/60 border border-red-500/20 rounded-xl space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-red-400 font-bold uppercase">
                    {pw.rule_violated}
                  </span>
                  {onOpenDossier && (
                    <button
                      onClick={() => onOpenDossier(pw.work_rec_id)}
                      className="text-[11px] text-sky-400 hover:text-sky-300 flex items-center space-x-1"
                    >
                      <FileText className="w-3 h-3" />
                      <span>Dossier</span>
                    </button>
                  )}
                </div>

                <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                  {pw.description}
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 font-mono">
                  <span>₹{pw.sanction_amount.toLocaleString()}</span>
                  <span>{pw.district_name}, {pw.state_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
