import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { CanonicalWork, PlatformOverview } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { PriorityBadge } from '../components/common/PriorityBadge';
import {
  IndianRupee,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  TrendingUp,
  Building2,
  FileText,
  Filter,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import clsx from 'clsx';

interface OverviewPageProps {
  onOpenDossier: (recId: string) => void;
  onNavigateToWorks?: (filter?: any) => void;
}

const FILTER_PILLS = [
  { id: 'all', label: 'All Portfolios', filter: {} },
  { id: 'critical', label: '🔴 Critical Triage', filter: { priority: 'CRITICAL' } },
  { id: 'high', label: '🟠 High Priority', filter: { priority: 'HIGH' } },
  { id: 'drinking_water', label: '🚰 Drinking Water', filter: { category: 'Drinking Water' } },
  { id: 'solar', label: '⚡ Solar Lighting', filter: { category: 'Solar' } },
  { id: 'roads', label: '🛣️ Roads & Pathways', filter: { category: 'Road' } },
  { id: 'health', label: '🏥 Public Health', filter: { category: 'Health' } },
  { id: 'education', label: '🏫 Schools & Anganwadi', filter: { category: 'Education' } },
];

export const OverviewPage: React.FC<OverviewPageProps> = ({ onOpenDossier, onNavigateToWorks }) => {
  const { currentUser } = useAuth();
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [urgentWorks, setUrgentWorks] = useState<CanonicalWork[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activePill, setActivePill] = useState<string>('all');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [ovData, trData, worksData] = await Promise.all([
          api.getOverview(),
          api.getTrends(),
          api.searchWorks({ priority: 'CRITICAL', page_size: 6 }),
        ]);
        setOverview(ovData);
        setTrends(trData);
        setUrgentWorks(worksData.items);
      } catch (err) {
        console.error('Failed to load overview data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentUser]);

  const handlePillClick = (pill: typeof FILTER_PILLS[0]) => {
    setActivePill(pill.id);
    if (pill.id === 'all') {
      api.searchWorks({ priority: 'CRITICAL', page_size: 6 }).then((res) => setUrgentWorks(res.items));
    } else if (onNavigateToWorks) {
      onNavigateToWorks(pill.filter);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="space-y-3 text-center">
          <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-mono">Aggregating MPLADS Analytical Intelligence...</p>
        </div>
      </div>
    );
  }

  // Format category chart data
  const categoryData = overview?.top_categories?.map((c) => ({
    name: c.name.length > 20 ? c.name.slice(0, 18) + '...' : c.name,
    count: c.count,
  })) || [];

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-7">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-blue-950/40 via-slate-900 to-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden shadow-xl">
        <div className="space-y-1 relative z-10">
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">National Governance &amp; Audit Overview</h1>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono">
              Empirical Core Active
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl">
            Real-time multi-detector anomaly surveillance across 36 States/UTs, 543 Lok Sabha constituencies, and 245 Rajya Sabha seats.
          </p>
        </div>
        <div className="flex items-center space-x-3 text-right">
          <div className="bg-[#0B1120] border border-slate-800 px-4 py-2.5 rounded-xl shadow-inner">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Analytical Quality Index</span>
            <span className="text-base font-bold font-mono text-emerald-400">
              {((overview?.avg_dqi_score || 0.85) * 100).toFixed(1)}% DQI
            </span>
          </div>
        </div>
      </div>

      {/* YouTube-Style Horizontally Scrollable Category Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto no-scrollbar py-1">
        {FILTER_PILLS.map((pill) => {
          const isActive = activePill === pill.id;
          return (
            <button
              key={pill.id}
              onClick={() => handlePillClick(pill)}
              className={clsx(
                'px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all duration-200 border shadow-sm select-none',
                isActive
                  ? 'bg-sky-500 text-white border-sky-400 font-semibold shadow-sky-500/20 shadow-md'
                  : 'bg-[#131D31] text-slate-300 border-slate-800 hover:border-slate-700 hover:bg-[#18233a]'
              )}
            >
              {pill.label}
            </button>
          );
        })}
      </div>

      {/* Interactive KPI Ribbon with Direct Navigation */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Sanctioned Capital"
          value={`₹${(overview?.total_sanctioned_cr || 0).toLocaleString()} Cr`}
          subtitle="Formally approved by IDAs"
          icon={<IndianRupee className="w-5 h-5" />}
          badge={`${(overview?.total_works || 0).toLocaleString()} Works`}
          badgeType="info"
          onClick={() => onNavigateToWorks?.()}
          clickableHint="Explore All Works →"
        />
        <MetricCard
          title="Total Disbursed"
          value={`₹${(overview?.total_disbursed_cr || 0).toLocaleString()} Cr`}
          subtitle={`Fund Utilization: ${overview?.overall_utilization_pct || 0}%`}
          icon={<Activity className="w-5 h-5 text-emerald-400" />}
          badge="Line-Item Vouchers"
          badgeType="success"
          onClick={() => onNavigateToWorks?.()}
          clickableHint="Inspect Disbursed →"
        />
        <MetricCard
          title="Completed Assets"
          value={(overview?.completed_works || 0).toLocaleString()}
          subtitle={`Completion Rate: ${overview?.overall_completion_pct || 0}%`}
          icon={<CheckCircle className="w-5 h-5 text-sky-400" />}
          badge="Handover Certified"
          badgeType="info"
          onClick={() => onNavigateToWorks?.({ query: 'completed' })}
          clickableHint="Browse Assets →"
        />
        <MetricCard
          title="Critical Anomalies"
          value={(overview?.priority_summary?.CRITICAL || 0).toLocaleString()}
          subtitle="Statutory Review Candidates"
          icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
          badge="High Vigilance Floor"
          badgeType="danger"
          onClick={() => onNavigateToWorks?.({ priority: 'CRITICAL' })}
          clickableHint="View Critical Triage →"
        />
      </div>

      {/* Priority Distribution Banner (Clickable Tiers) */}
      <div className="bg-[#131D31] border border-slate-800/80 rounded-2xl p-5 space-y-3 shadow-lg">
        <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
          <span>Autonomous Anomaly Triage Hierarchy (Click Tier to Inspect in Works)</span>
          <span>{overview?.total_works ? `${overview.total_works.toLocaleString()} Evaluated` : 'All Active'}</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div
            onClick={() => onNavigateToWorks?.({ priority: 'CRITICAL' })}
            role="button"
            tabIndex={0}
            className="p-3.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/50 rounded-xl cursor-pointer transition-all duration-200 hover:-translate-y-0.5 group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-red-400 flex items-center space-x-1">
                <span>CRITICAL</span>
                <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </span>
              <span className="text-base font-bold font-mono text-red-400">
                {(overview?.priority_summary?.CRITICAL || 0).toLocaleString()}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">Cost Overrun or &gt;2yr Delay</p>
          </div>

          <div
            onClick={() => onNavigateToWorks?.({ priority: 'HIGH' })}
            role="button"
            tabIndex={0}
            className="p-3.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 hover:border-amber-500/50 rounded-xl cursor-pointer transition-all duration-200 hover:-translate-y-0.5 group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-400 flex items-center space-x-1">
                <span>HIGH</span>
                <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </span>
              <span className="text-base font-bold font-mono text-amber-400">
                {(overview?.priority_summary?.HIGH || 0).toLocaleString()}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">SLA Breach + Dormant Mobilization</p>
          </div>

          <div
            onClick={() => onNavigateToWorks?.({ priority: 'MEDIUM' })}
            role="button"
            tabIndex={0}
            className="p-3.5 bg-yellow-500/10 hover:bg-yellow-500/20 border border-yellow-500/30 hover:border-yellow-500/50 rounded-xl cursor-pointer transition-all duration-200 hover:-translate-y-0.5 group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-yellow-300 flex items-center space-x-1">
                <span>MEDIUM</span>
                <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </span>
              <span className="text-base font-bold font-mono text-yellow-300">
                {(overview?.priority_summary?.MEDIUM || 0).toLocaleString()}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">45-day SLA Breach or Peer Cost Outlier</p>
          </div>

          <div
            onClick={() => onNavigateToWorks?.({ priority: 'LOW' })}
            role="button"
            tabIndex={0}
            className="p-3.5 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 hover:border-emerald-500/50 rounded-xl cursor-pointer transition-all duration-200 hover:-translate-y-0.5 group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1">
                <span>NORMAL / LOW</span>
                <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </span>
              <span className="text-base font-bold font-mono text-emerald-400">
                {(overview?.priority_summary?.LOW || 0).toLocaleString()}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">Baseline Milestone Progression</p>
          </div>
        </div>
      </div>

      {/* Visual Analytics Grid: Category Breakdown & Velocity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-[#131D31] border border-slate-800/80 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Building2 className="w-4 h-4 text-sky-400" />
              <span>Expenditure by Work Category (Annexure-VIII)</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">Project Volume</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" stroke="#64748B" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#94A3B8" fontSize={11} width={110} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1120', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#38BDF8', fontSize: '12px' }}
                />
                <Bar dataKey="count" fill="#0284C7" radius={[0, 4, 4, 0]}>
                  {categoryData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#38BDF8' : '#0284C7'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Macro Trends */}
        <div className="bg-[#131D31] border border-slate-800/80 rounded-2xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Longitudinal Velocity (Sanction vs Disbursement)</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">2020 - 2026</span>
          </div>
          <div className="h-64 w-full">
            {trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends} margin={{ left: 0, right: 20, top: 10, bottom: 5 }}>
                  <XAxis dataKey="tenure_or_year" stroke="#64748B" fontSize={11} />
                  <YAxis stroke="#64748B" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B1120', borderColor: '#334155', borderRadius: '8px' }}
                  />
                  <Line type="monotone" dataKey="sanctioned_cr" stroke="#38BDF8" strokeWidth={2} name="Sanctioned (Cr)" />
                  <Line type="monotone" dataKey="disbursed_cr" stroke="#10B981" strokeWidth={2} name="Disbursed (Cr)" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 font-mono">
                Longitudinal trends actively computing from historical masters...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Urgent Review Queue Table */}
      <div className="bg-[#131D31] border border-slate-800/80 rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span>Urgent Priority Review Queue (Top Critical Candidates)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Ranked cases exhibiting statutory deadline breaches, severe cost overruns, or stalled funds.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B1120] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Work ID / Description</th>
                <th className="py-3 px-4">Location &amp; MP</th>
                <th className="py-3 px-4">Sanction / Disbursed</th>
                <th className="py-3 px-4">Turnaround</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {urgentWorks.map((work) => (
                <tr
                  key={work.work_rec_id}
                  onClick={() => onOpenDossier(work.work_rec_id)}
                  className="hover:bg-slate-800/60 cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-4">
                    <PriorityBadge priority={work.priority} size="sm" />
                  </td>
                  <td className="py-3.5 px-4 max-w-xs">
                    <span className="font-mono text-slate-400 text-[11px] block">#{work.work_rec_id}</span>
                    <p className="text-slate-200 truncate font-medium">{work.description}</p>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="text-slate-300 font-medium block">{work.ida_name}, {work.state_name}</span>
                    <span className="text-slate-400 text-[11px] block truncate max-w-[180px]">{work.mp_name}</span>
                  </td>
                  <td className="py-3.5 px-4 font-mono">
                    <span className="text-emerald-400 block font-semibold">₹{work.sanction_amount.toLocaleString()}</span>
                    <span className="text-slate-400 text-[11px] block">₹{work.total_disbursed.toLocaleString()}</span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-[11px]">
                    <span className={work.days_rec_to_sanction > 45 ? 'text-red-400 font-bold' : 'text-slate-400'}>
                      {work.days_rec_to_sanction}d to sanction
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => onOpenDossier(work.work_rec_id)}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-all"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>View Dossier</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
