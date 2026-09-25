import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CanonicalWork, StateMapMetric } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import {
  Search,
  Filter,
  FileText,
  ChevronLeft,
  ChevronRight,
  IndianRupee,
  MapPin,
  Calendar,
  X,
  Copy,
  Check,
  RotateCcw,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Lock,
  Shield,
  Download,
} from 'lucide-react';
import clsx from 'clsx';

interface WorksPageProps {
  onOpenDossier: (recId: string) => void;
  initialFilter?: {
    priority?: string;
    category?: string;
    query?: string;
    state?: string;
  } | null;
}

const CATEGORY_PILLS = [
  { id: 'all', label: 'All Categories', filter: {} },
  { id: 'critical', label: '🔴 Critical', filter: { priority: 'CRITICAL' } },
  { id: 'high', label: '🟠 High', filter: { priority: 'HIGH' } },
  { id: 'water', label: '🚰 Drinking Water', filter: { category: 'Drinking Water' } },
  { id: 'solar', label: '⚡ Solar Light', filter: { category: 'Solar' } },
  { id: 'roads', label: '🛣️ Roads & Pathways', filter: { category: 'Road' } },
  { id: 'health', label: '🏥 Public Health', filter: { category: 'Health' } },
  { id: 'education', label: '🏫 Schools & Anganwadi', filter: { category: 'Education' } },
];

export const WorksPage: React.FC<WorksPageProps> = ({ onOpenDossier, initialFilter }) => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const [works, setWorks] = useState<CanonicalWork[]>([]);
  const [availableStates, setAvailableStates] = useState<StateMapMetric[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);
  const [query, setQuery] = useState<string>('');
  const [debouncedQuery, setDebouncedQuery] = useState<string>('');
  const [priority, setPriority] = useState<string>('');
  const [stateFilter, setStateFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('priority');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [loading, setLoading] = useState<boolean>(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Debounce query input by 300ms for smooth, responsive search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Sync state filter with user jurisdiction if strict isolation is active
  useEffect(() => {
    if (currentUser?.strict_isolation) {
      if (currentUser.role === 'DISTRICT_AUTHORITY' && currentUser.state) {
        setStateFilter(currentUser.state);
      } else if (currentUser.role === 'STATE_NODAL_OFFICER' && currentUser.state) {
        setStateFilter(currentUser.state);
      }
    } else {
      setStateFilter('');
    }
  }, [currentUser]);

  useEffect(() => {
    api.getStateMapMetrics()
      .then((states) => setAvailableStates(states))
      .catch((err) => console.error('Failed to load state list:', err));
  }, []);

  useEffect(() => {
    if (initialFilter) {
      if (initialFilter.priority !== undefined) setPriority(initialFilter.priority);
      if (initialFilter.category !== undefined) setCategoryFilter(initialFilter.category);
      if (initialFilter.query !== undefined) {
        setQuery(initialFilter.query);
        setDebouncedQuery(initialFilter.query);
      }
      if (initialFilter.state !== undefined) setStateFilter(initialFilter.state);
      setPage(1);
    }
  }, [initialFilter]);

  const isDistrictLocked = currentUser?.strict_isolation && currentUser?.role === 'DISTRICT_AUTHORITY';
  const isStateLocked = currentUser?.strict_isolation && (currentUser?.role === 'STATE_NODAL_OFFICER' || currentUser?.role === 'DISTRICT_AUTHORITY');
  const isMpLocked = currentUser?.strict_isolation && currentUser?.role === 'MP_USER';

  const fetchWorks = async () => {
    setLoading(true);
    try {
      const data = await api.searchWorks({
        query: debouncedQuery.trim() || undefined,
        priority: priority || undefined,
        state: isStateLocked ? (currentUser?.state || undefined) : (stateFilter.trim() || undefined),
        district: isDistrictLocked ? (currentUser?.district || undefined) : undefined,
        mp_name: isMpLocked ? (currentUser?.mp_name || undefined) : undefined,
        category: categoryFilter.trim() || undefined,
        sort_by: sortBy || undefined,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      });
      setWorks(data.items);
      setTotal(data.total);
    } catch (err: any) {
      console.error('Failed to search works:', err);
      showToast('Query Restricted', err.message || 'Action restricted by multi-tenant security boundary', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorks();
  }, [currentUser, page, priority, stateFilter, categoryFilter, sortBy, sortOrder, debouncedQuery]);

  const handleExportCsv = () => {
    if (works.length === 0) {
      showToast('Export Error', 'No records to export in current view', 'warning');
      return;
    }
    const headers = ['Rec ID', 'Work ID', 'Description', 'Category', 'State', 'District/IDA', 'MP Name', 'Sanction Amount (INR)', 'Total Disbursed (INR)', 'Priority', 'SLA Days'];
    const rows = works.map((w) => [
      w.work_rec_id,
      w.work_id,
      `"${w.description.replace(/"/g, '""')}"`,
      w.category,
      w.state_name,
      `"${w.ida_name}"`,
      `"${w.mp_name}"`,
      w.sanction_amount,
      w.total_disbursed,
      w.priority,
      w.days_rec_to_sanction,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `MPLADS_Works_${currentUser?.role || 'export'}_page${page}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Export Complete', `Exported ${works.length} records to CSV`, 'success');
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchWorks();
  };

  const handleClearFilters = () => {
    setQuery('');
    setPriority('');
    setStateFilter('');
    setCategoryFilter('');
    setPage(1);
  };

  const handleCopyRecId = (e: React.MouseEvent, recId: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(recId);
    setCopiedId(recId);
    showToast('Copied to Clipboard', `Work ID #${recId}`, 'info');
    setTimeout(() => setCopiedId(null), 2000);
  };

  const totalPages = Math.ceil(total / pageSize);
  const hasActiveFilters = Boolean(query || priority || stateFilter || categoryFilter);

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Canonical Works Directory</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Searchable repository of 102,548 itemized MPLADS developmental works across all 36 States &amp; UTs. Click any row for the 5-Question Governance Dossier.
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
          <span>
            Total Matching: <strong className="text-sky-400">{total.toLocaleString()}</strong> works
          </span>
          <button
            onClick={handleExportCsv}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium text-xs transition-colors"
            title="Export filtered records to CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
            >
              <RotateCcw className="w-3 h-3 text-amber-400" />
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>

      {/* RBAC Jurisdiction Security Notice */}
      {currentUser?.strict_isolation && currentUser?.role !== 'CENTRAL_AUDITOR' && (
        <div className="p-3.5 bg-gradient-to-r from-amber-500/10 via-sky-500/5 to-transparent border border-amber-500/30 rounded-2xl flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-amber-300">
                Statutory Multi-Tenant Isolation Active ({currentUser.role.replace(/_/g, ' ')})
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
                {currentUser.role === 'DISTRICT_AUTHORITY' && (
                  <>Locked to jurisdiction: <strong className="text-white">{currentUser.district}, {currentUser.state}</strong>. Cross-district queries are restricted under Section 3.2 MPLADS Guidelines.</>
                )}
                {currentUser.role === 'STATE_NODAL_OFFICER' && (
                  <>Locked to state: <strong className="text-white">{currentUser.state}</strong>. Cross-state queries are restricted under statutory RBAC.</>
                )}
                {currentUser.role === 'MP_USER' && (
                  <>Locked to MP portfolio: <strong className="text-white">{currentUser.name} ({currentUser.constituency})</strong>.</>
                )}
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono uppercase px-2.5 py-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold shrink-0">
            Tenant Isolated
          </span>
        </div>
      )}

      {/* Filter Ribbon */}
      <form onSubmit={handleSearchSubmit} className="bg-[#131D31] border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center gap-3 shadow-lg">
        <div className="flex-1 min-w-[240px] relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder={
              isDistrictLocked
                ? `Search projects within ${currentUser?.district} district...`
                : "Search by ID, description, MP, or district..."
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-[#0B1120] border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>

        {/* State Filter Dropdown (Locked if user has state scope) */}
        {isStateLocked ? (
          <div className="flex items-center space-x-1.5 bg-[#0B1120] border border-amber-500/30 px-3 py-2 rounded-xl text-xs text-amber-300 font-mono">
            <Lock className="w-3 h-3 text-amber-400" />
            <span>{currentUser?.state}</span>
          </div>
        ) : (
          <select
            value={stateFilter}
            onChange={(e) => {
              setStateFilter(e.target.value);
              setPage(1);
            }}
            className="bg-[#0B1120] border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer max-w-[200px]"
          >
            <option value="">All States &amp; UTs</option>
            {availableStates.map((st) => (
              <option key={st.state_name} value={st.state_name}>
                {st.state_name}
              </option>
            ))}
          </select>
        )}

        {/* Priority Filter */}
        <select
          value={priority}
          onChange={(e) => {
            setPriority(e.target.value);
            setPage(1);
          }}
          className="bg-[#0B1120] border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
        >
          <option value="">All Priorities</option>
          <option value="CRITICAL">🔴 Critical Priority</option>
          <option value="HIGH">🟠 High Priority</option>
          <option value="MEDIUM">🟡 Medium Priority</option>
          <option value="LOW">🟢 Low / Normal</option>
        </select>

        <button
          type="submit"
          className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-md shadow-sky-600/20 transition-colors"
        >
          Search Works
        </button>
      </form>

      {/* YouTube-Style Category Filter Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto no-scrollbar py-0.5">
        {CATEGORY_PILLS.map((pill) => {
          const isActive =
            (pill.filter.priority && priority === pill.filter.priority) ||
            (pill.filter.category && categoryFilter === pill.filter.category) ||
            (!pill.filter.priority && !pill.filter.category && !priority && !categoryFilter);

          return (
            <button
              key={pill.id}
              onClick={() => {
                if (pill.filter.priority) {
                  setPriority(priority === pill.filter.priority ? '' : pill.filter.priority);
                } else if (pill.filter.category) {
                  setCategoryFilter(categoryFilter === pill.filter.category ? '' : pill.filter.category);
                } else {
                  setPriority('');
                  setCategoryFilter('');
                }
                setPage(1);
              }}
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

      {/* Table */}
      <div className="bg-[#131D31] border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B1120] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800 select-none">
              <tr>
                <th
                  onClick={() => handleSort('priority')}
                  className="py-3 px-4 cursor-pointer hover:text-white hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Priority</span>
                    {sortBy === 'priority' ? (
                      sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-sky-400" /> : <ArrowDown className="w-3 h-3 text-sky-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('work_rec_id')}
                  className="py-3 px-4 cursor-pointer hover:text-white hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Rec ID / Project</span>
                    {sortBy === 'work_rec_id' ? (
                      sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-sky-400" /> : <ArrowDown className="w-3 h-3 text-sky-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('category')}
                  className="py-3 px-4 cursor-pointer hover:text-white hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Category</span>
                    {sortBy === 'category' ? (
                      sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-sky-400" /> : <ArrowDown className="w-3 h-3 text-sky-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
                    )}
                  </div>
                </th>
                <th className="py-3 px-4">Location &amp; MP</th>
                <th
                  onClick={() => handleSort('sanction_amount')}
                  className="py-3 px-4 cursor-pointer hover:text-white hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Financials</span>
                    {sortBy === 'sanction_amount' ? (
                      sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-sky-400" /> : <ArrowDown className="w-3 h-3 text-sky-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('days_rec_to_sanction')}
                  className="py-3 px-4 cursor-pointer hover:text-white hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>SLA Turnaround</span>
                    {sortBy === 'days_rec_to_sanction' ? (
                      sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-sky-400" /> : <ArrowDown className="w-3 h-3 text-sky-400" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40 group-hover:opacity-100" />
                    )}
                  </div>
                </th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={idx} className="animate-pulse">
                    <td className="py-4 px-4"><div className="w-16 h-5 rounded-full bg-slate-800" /></td>
                    <td className="py-4 px-4"><div className="w-48 h-4 rounded bg-slate-800" /><div className="w-24 h-3 rounded bg-slate-800/60 mt-1" /></td>
                    <td className="py-4 px-4"><div className="w-20 h-4 rounded bg-slate-800" /></td>
                    <td className="py-4 px-4"><div className="w-32 h-4 rounded bg-slate-800" /></td>
                    <td className="py-4 px-4"><div className="w-24 h-4 rounded bg-slate-800" /></td>
                    <td className="py-4 px-4"><div className="w-16 h-4 rounded bg-slate-800" /></td>
                    <td className="py-4 px-4 text-right"><div className="w-16 h-7 rounded-lg bg-slate-800 ml-auto" /></td>
                  </tr>
                ))
              ) : works.length > 0 ? (
                works.map((work) => (
                  <tr
                    key={work.work_rec_id}
                    onClick={() => onOpenDossier(work.work_rec_id)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                  >
                    <td className="py-3.5 px-4">
                      <PriorityBadge priority={work.priority} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 max-w-xs">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-mono text-slate-400 text-[11px]">#{work.work_rec_id}</span>
                        <button
                          onClick={(e) => handleCopyRecId(e, work.work_rec_id)}
                          className="text-slate-500 hover:text-slate-300 transition-colors p-0.5"
                          title="Copy Rec ID"
                        >
                          {copiedId === work.work_rec_id ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          )}
                        </button>
                      </div>
                      <p className="text-slate-200 truncate font-medium group-hover:text-sky-300 transition-colors">
                        {work.description}
                      </p>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono">
                        {work.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-slate-300 font-medium block">
                        {work.ida_name}, {work.state_name}
                      </span>
                      <span className="text-slate-400 text-[11px] block truncate max-w-[160px]">
                        {work.mp_name}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      <span className="text-emerald-400 block font-semibold">
                        ₹{work.sanction_amount.toLocaleString()}
                      </span>
                      <span className="text-slate-400 text-[11px] block">
                        Disb: ₹{work.total_disbursed.toLocaleString()}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px]">
                      <span
                        className={clsx(
                          'px-2 py-0.5 rounded border',
                          work.days_rec_to_sanction > 45
                            ? 'bg-red-500/15 text-red-400 border-red-500/30 font-bold'
                            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        )}
                      >
                        {work.days_rec_to_sanction}d to sanction
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenDossier(work.work_rec_id);
                        }}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium transition-all"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Dossier</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-slate-400 font-mono">
                    No matching works found. Try modifying search query or resetting filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="px-6 py-3.5 border-t border-slate-800 bg-[#0B1120] flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">
              Page {page} of {totalPages} ({total.toLocaleString()} total works)
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || loading}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 font-mono flex items-center space-x-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 font-mono flex items-center space-x-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
