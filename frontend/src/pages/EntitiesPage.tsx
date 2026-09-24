import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { MPProfile, VendorProfile } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { MpDetailModal } from '../components/entities/MpDetailModal';
import { VendorDetailModal } from '../components/entities/VendorDetailModal';
import { useAuth } from '../context/AuthContext';
import {
  Users,
  Briefcase,
  Building,
  Search,
  IndianRupee,
  AlertTriangle,
  Award,
  ChevronLeft,
  ChevronRight,
  Lock,
  ShieldCheck,
} from 'lucide-react';
import clsx from 'clsx';

interface EntitiesPageProps {
  onOpenDossier?: (recId: string) => void;
}

export const EntitiesPage: React.FC<EntitiesPageProps> = ({ onOpenDossier }) => {
  const { currentUser } = useAuth();
  const [subTab, setSubTab] = useState<'mps' | 'vendors'>('mps');
  const [mps, setMps] = useState<MPProfile[]>([]);
  const [vendors, setVendors] = useState<VendorProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);

  // Drilldown Dialog States
  const [selectedMpName, setSelectedMpName] = useState<string | null>(null);
  const [selectedVendorName, setSelectedVendorName] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    if (subTab === 'mps') {
      api.searchMps({ query: search, page, page_size: 18 })
        .then((res) => {
          setMps(res.items);
          setTotal(res.total);
        })
        .finally(() => setLoading(false));
    } else {
      api.searchVendors({ query: search, page, page_size: 18 })
        .then((res) => {
          setVendors(res.items);
          setTotal(res.total);
        })
        .finally(() => setLoading(false));
    }
  }, [currentUser, subTab, page, search]);

  const jurisdictionLabel = currentUser?.role === 'DISTRICT_AUTHORITY'
    ? `${currentUser.district} District (${currentUser.state})`
    : currentUser?.role === 'STATE_NODAL_OFFICER'
    ? `${currentUser.state} State`
    : currentUser?.role === 'MP_USER'
    ? `Hon. ${currentUser.name} (${currentUser.constituency})`
    : 'National Directory (MoSPI / CAG)';

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#131D31] border border-slate-800 p-6 rounded-2xl">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">Entity Intelligence &amp; Market Monopolies</h1>
            {currentUser?.strict_isolation && currentUser?.role !== 'CENTRAL_AUDITOR' && (
              <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 text-[10px] font-mono">
                <Lock className="w-3 h-3" />
                <span>Scoped</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-record tracking of Parliamentary Quotas, District Implementing Agencies, and Contractor Dominance (HHI).
          </p>
          <div className="mt-2 text-xs font-mono text-sky-400 flex items-center space-x-2">
            <span className="text-slate-400">Authorized Territory:</span>
            <span className="font-semibold text-slate-200">{jurisdictionLabel}</span>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center bg-[#0B1120] border border-slate-800 rounded-lg p-1 space-x-1">
          <button
            onClick={() => {
              setSubTab('mps');
              setPage(1);
              setSearch('');
            }}
            className={clsx(
              'flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              subTab === 'mps' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Users className="w-3.5 h-3.5" />
            <span>MP Portfolios (775)</span>
          </button>
          <button
            onClick={() => {
              setSubTab('vendors');
              setPage(1);
              setSearch('');
            }}
            className={clsx(
              'flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              subTab === 'vendors' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Contractors &amp; HHI Monopolies</span>
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="flex items-center justify-between">
        <div className="w-full max-w-sm relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder={subTab === 'mps' ? 'Search MP name or constituency...' : 'Search contractor or vendor name...'}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full bg-[#131D31] border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>
        <span className="text-xs font-mono text-slate-400">Total Entities: {total.toLocaleString()}</span>
      </div>

      {/* Grid Content */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400 font-mono">Loading entity profiles...</div>
      ) : subTab === 'mps' ? (
        /* MP Directory Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {mps.map((mp) => (
            <div
              key={mp.mp_name}
              onClick={() => setSelectedMpName(mp.mp_name)}
              className="bg-[#131D31] border border-slate-800/90 hover:border-sky-500/50 hover:bg-[#18233a] cursor-pointer rounded-xl p-5 space-y-3 transition-all group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white tracking-tight group-hover:text-sky-300 transition-colors">
                    {mp.mp_name}
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {mp.house} • {mp.constituency}, {mp.state_name}
                  </p>
                </div>
                <PriorityBadge priority={mp.risk_tier} size="sm" />
              </div>

              {/* Quota Progress Meter */}
              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Quota Utilization</span>
                  <span className={mp.utilization_pct > 100 ? 'text-amber-400 font-bold' : 'text-emerald-400 font-bold'}>
                    {mp.utilization_pct}%
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={clsx(
                      'h-full rounded-full',
                      mp.utilization_pct > 100 ? 'bg-amber-400' : 'bg-emerald-400'
                    )}
                    style={{ width: `${Math.min(100, mp.utilization_pct)}%` }}
                  />
                </div>
              </div>

              {/* Financial Snapshot */}
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
                <div>
                  <span className="text-[9px] text-slate-500 block">Recommended</span>
                  <span className="text-slate-300 font-semibold">{mp.total_works} works</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 block">Sanctioned</span>
                  <span className="text-slate-300 font-semibold">₹{mp.sanctioned_amount_cr} Cr</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 block">Disbursed</span>
                  <span className="text-sky-400 font-semibold">₹{mp.disbursed_amount_cr} Cr</span>
                </div>
              </div>

              <div className="pt-1 text-[10px] text-sky-400/80 font-mono text-right group-hover:text-sky-300">
                Click to inspect portfolio →
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Vendor Directory Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {vendors.map((v) => (
            <div
              key={v.vendor_name}
              onClick={() => setSelectedVendorName(v.vendor_name)}
              className="bg-[#131D31] border border-slate-800/90 hover:border-amber-500/50 hover:bg-[#18233a] cursor-pointer rounded-xl p-5 space-y-3 transition-all group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white tracking-tight truncate max-w-[220px] group-hover:text-amber-300 transition-colors">
                    {v.vendor_name}
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {v.primary_state} • {v.primary_category}
                  </p>
                </div>
                <span
                  className={clsx(
                    'text-[10px] font-mono font-bold px-2 py-0.5 rounded border',
                    v.hhi_risk === 'CONCENTRATED'
                      ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                      : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  )}
                >
                  {v.hhi_risk}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
                <div>
                  <span className="text-[9px] text-slate-500 block">Disbursed</span>
                  <span className="text-emerald-400 font-semibold">₹{v.total_disbursed_cr} Cr</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 block">Projects</span>
                  <span className="text-slate-300 font-semibold">{v.total_works}</span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 block">Districts</span>
                  <span className="text-slate-300 font-semibold">{v.district_count}</span>
                </div>
              </div>

              {v.has_recurrence_flag && (
                <div className="pt-2 text-[10px] text-red-400 font-mono flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>Repeat Anomaly Flags Detected</span>
                </div>
              )}

              <div className="pt-1 text-[10px] text-amber-400/80 font-mono text-right group-hover:text-amber-300">
                Click to inspect contracts →
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-slate-400 pt-4">
        <span>Page {page} of {Math.ceil(total / 18) || 1}</span>
        <div className="flex items-center space-x-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            disabled={page >= Math.ceil(total / 18)}
            onClick={() => setPage((p) => p + 1)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Modals */}
      {selectedMpName && (
        <MpDetailModal
          mpName={selectedMpName}
          onClose={() => setSelectedMpName(null)}
          onOpenDossier={onOpenDossier}
        />
      )}

      {selectedVendorName && (
        <VendorDetailModal
          vendorName={selectedVendorName}
          onClose={() => setSelectedVendorName(null)}
          onOpenDossier={onOpenDossier}
        />
      )}
    </div>
  );
};
