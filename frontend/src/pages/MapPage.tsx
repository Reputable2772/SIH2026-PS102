import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CanonicalWork, DistrictMetric, StateMapMetric } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { IndiaSvgMap } from '../components/map/IndiaSvgMap';
import {
  MapPin,
  Building,
  AlertTriangle,
  IndianRupee,
  ChevronRight,
  ArrowLeft,
  Search,
  FileText,
  Activity,
  Layers,
  Sparkles,
  Users,
  Compass,
  CheckCircle2,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import clsx from 'clsx';

interface MapPageProps {
  onOpenDossier: (recId: string) => void;
}

export const MapPage: React.FC<MapPageProps> = ({ onOpenDossier }) => {
  const [states, setStates] = useState<StateMapMetric[]>([]);
  const [selectedState, setSelectedState] = useState<StateMapMetric | null>(null);
  const [districts, setDistricts] = useState<DistrictMetric[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictMetric | null>(null);
  const [districtWorks, setDistrictWorks] = useState<CanonicalWork[]>([]);
  
  // Navigation level: 'national' -> 'state' -> 'district'
  const [viewLevel, setViewLevel] = useState<'national' | 'state' | 'district'>('national');
  const [loadingDistricts, setLoadingDistricts] = useState<boolean>(false);
  const [loadingWorks, setLoadingWorks] = useState<boolean>(false);
  const [metric, setMetric] = useState<'alerts' | 'sanctioned' | 'utilization'>('alerts');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('priority');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    api.getStateMapMetrics().then((data) => {
      setStates(data);
      if (data.length > 0) {
        setSelectedState(data[0]);
      }
    });
  }, []);

  const handleSelectStateByName = async (stateName: string) => {
    const found = states.find(
      (s) => s.state_name.toLowerCase().trim() === stateName.toLowerCase().trim()
    );
    if (found) {
      handleSelectState(found);
    } else {
      // Find case-insensitive or partial
      const partial = states.find(
        (s) => s.state_name.toLowerCase().includes(stateName.toLowerCase())
      );
      if (partial) handleSelectState(partial);
    }
  };

  const handleSelectState = async (st: StateMapMetric) => {
    setSelectedState(st);
    setSelectedDistrict(null);
    setViewLevel('state');
    setLoadingDistricts(true);
    try {
      const dists = await api.getDistrictsForState(st.state_name);
      setDistricts(dists);
    } catch (err) {
      console.error('Failed to load districts:', err);
    } finally {
      setLoadingDistricts(false);
    }
  };

  const handleSelectDistrict = async (
    d: DistrictMetric,
    newSortBy = sortBy,
    newSortOrder = sortOrder
  ) => {
    setSelectedDistrict(d);
    setViewLevel('district');
    setLoadingWorks(true);
    try {
      const res = await api.searchWorks({
        state: selectedState?.state_name,
        district: d.district_name,
        sort_by: newSortBy,
        sort_order: newSortOrder,
        page_size: 50,
      });
      setDistrictWorks(res.items);
    } catch (err) {
      console.error('Failed to load district works:', err);
    } finally {
      setLoadingWorks(false);
    }
  };

  const handleSort = (column: string) => {
    const nextOrder = sortBy === column && sortOrder === 'desc' ? 'asc' : 'desc';
    setSortBy(column);
    setSortOrder(nextOrder);
    if (selectedDistrict) {
      handleSelectDistrict(selectedDistrict, column, nextOrder);
    }
  };

  const renderSortIcon = (column: string) => {
    if (sortBy !== column) {
      return <ArrowUpDown className="w-3 h-3 text-slate-600 group-hover:text-slate-400 transition-colors" />;
    }
    return sortOrder === 'asc' ? (
      <ArrowUp className="w-3 h-3 text-sky-400" />
    ) : (
      <ArrowDown className="w-3 h-3 text-sky-400" />
    );
  };

  // Search filtering
  const filteredStates = states.filter((s) => {
    const q = searchFilter.toLowerCase().trim();
    if (!q) return true;
    return s.state_name.toLowerCase().includes(q);
  });

  const filteredDistricts = districts.filter((d) => {
    const q = searchFilter.toLowerCase().trim();
    if (!q) return true;
    return (
      d.district_name.toLowerCase().includes(q) ||
      d.primary_ia.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#0A0F1D]">
      {/* Dynamic Breadcrumbs & Search Header */}
      <div className="p-4 md:px-6 md:py-3.5 border-b border-slate-800 bg-[#0F172A]/90 backdrop-blur-md flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-lg">
        {/* Breadcrumb Hierarchy */}
        <div className="flex items-center space-x-2 text-xs font-mono">
          <button
            onClick={() => {
              setViewLevel('national');
              setSelectedDistrict(null);
            }}
            className={clsx(
              'px-2.5 py-1 rounded-lg transition-colors flex items-center space-x-1.5',
              viewLevel === 'national'
                ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/40'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            )}
          >
            <Compass className="w-3.5 h-3.5 text-sky-400" />
            <span>National India Map</span>
          </button>

          {selectedState && (viewLevel === 'state' || viewLevel === 'district') && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <button
                onClick={() => {
                  setViewLevel('state');
                  setSelectedDistrict(null);
                }}
                className={clsx(
                  'px-2.5 py-1 rounded-lg transition-colors',
                  viewLevel === 'state'
                    ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/40'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                )}
              >
                {selectedState.state_name} ({districts.length} Districts)
              </button>
            </>
          )}

          {selectedDistrict && viewLevel === 'district' && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/40">
                {selectedDistrict.district_name} ({districtWorks.length} Works)
              </span>
            </>
          )}
        </div>

        {/* Global Finder & Metric Selector */}
        <div className="flex items-center space-x-3 w-full sm:w-auto">
          {viewLevel === 'national' && (
            <div className="flex items-center bg-[#0B1120] border border-slate-800 rounded-xl p-1 text-xs font-mono">
              <button
                onClick={() => setMetric('alerts')}
                className={clsx(
                  'px-3 py-1 rounded-lg transition-all',
                  metric === 'alerts'
                    ? 'bg-red-500/20 text-red-400 font-bold border border-red-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                Critical Radar
              </button>
              <button
                onClick={() => setMetric('sanctioned')}
                className={clsx(
                  'px-3 py-1 rounded-lg transition-all',
                  metric === 'sanctioned'
                    ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                Sanctioned (Cr)
              </button>
              <button
                onClick={() => setMetric('utilization')}
                className={clsx(
                  'px-3 py-1 rounded-lg transition-all',
                  metric === 'utilization'
                    ? 'bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                Utilization %
              </button>
            </div>
          )}

          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={
                viewLevel === 'national'
                  ? 'Find State or UT...'
                  : viewLevel === 'state'
                  ? 'Find District or IA...'
                  : 'Filter works in district...'
              }
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full bg-[#0B1120] border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-sans"
            />
          </div>
        </div>
      </div>

      {/* TIER 1: NATIONAL INDIA MAP VIEW */}
      {viewLevel === 'national' && (
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Left: Vector India SVG Map */}
          <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-y-auto relative bg-[#090D18]">
            <div className="absolute top-4 left-6 z-10 space-y-1">
              <span className="text-[10px] font-mono uppercase text-sky-400 tracking-wider font-semibold block">
                Interactive Geospatial Radar
              </span>
              <h2 className="text-base font-bold text-white tracking-tight">
                Republic of India (36 States &amp; UTs)
              </h2>
              <p className="text-xs text-slate-400">
                Click any State or UT polygon to inspect its Parliamentary Constituencies &amp; Districts.
              </p>
            </div>

            <div className="w-full max-w-2xl h-full flex items-center justify-center mt-6">
              <IndiaSvgMap
                metrics={states}
                selectedState={selectedState?.state_name || null}
                onSelectState={handleSelectStateByName}
                metricType={metric}
              />
            </div>
          </div>

          {/* Right: State Ranking Cards & Fast Select List */}
          <div className="w-full lg:w-96 bg-[#0B1120] border-t lg:border-t-0 lg:border-l border-slate-800/80 flex flex-col shrink-0 overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-[#131D31] flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-400 block font-semibold">
                  Territory Registry
                </span>
                <h3 className="text-sm font-bold text-white tracking-tight">
                  {filteredStates.length} Matching Jurisdictions
                </h3>
              </div>
              <span className="text-xs font-mono text-emerald-400 font-bold">
                102,548 Works
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
              {filteredStates.map((st) => {
                const isSelected = selectedState?.state_name === st.state_name;
                return (
                  <div
                    key={st.state_name}
                    onClick={() => handleSelectState(st)}
                    className={clsx(
                      'p-3.5 rounded-xl border cursor-pointer transition-all duration-150 space-y-2 group relative',
                      isSelected
                        ? 'bg-[#18233a] border-sky-500 shadow-md shadow-sky-500/10'
                        : 'bg-[#131D31] border-slate-800/80 hover:border-slate-700 hover:bg-[#162035]'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-xs font-bold text-slate-200 group-hover:text-sky-300 transition-colors">
                          {st.state_name}
                        </h4>
                        <span className="text-[10px] font-mono text-slate-400 block mt-0.5">
                          {st.district_count} Districts • {st.total_works.toLocaleString()} Projects
                        </span>
                      </div>
                      {st.critical_alerts > 0 ? (
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/30">
                          {st.critical_alerts} Critical
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          Optimal
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-[11px] font-mono">
                      <div>
                        <span className="text-[9px] text-slate-500 block">Sanctioned</span>
                        <span className="text-slate-200 font-semibold">₹{st.sanctioned_amount_cr} Cr</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block">Utilization</span>
                        <span className="text-emerald-400 font-semibold">{st.utilization_pct}%</span>
                      </div>
                    </div>

                    <div className="text-[10px] font-mono text-sky-400/80 text-right pt-1 group-hover:text-sky-300">
                      Explore Districts →
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TIER 2: STATE DISTRICTS & CONSTITUENCIES DRILLDOWN */}
      {viewLevel === 'state' && selectedState && (
        <div className="flex-1 flex flex-col overflow-hidden p-6 space-y-5">
          {/* State Metric Ribbon Banner */}
          <div className="bg-gradient-to-r from-blue-950/40 via-slate-900 to-slate-900 border border-slate-800 p-5 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setViewLevel('national')}
                  className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                  title="Back to India Map"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <h1 className="text-lg font-bold text-white tracking-tight">
                  {selectedState.state_name}
                </h1>
                <span className="px-2 py-0.5 rounded-full bg-sky-500/15 text-sky-400 border border-sky-500/30 text-[10px] font-mono">
                  State Deep-Dive
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Click any District or Implementing Agency below to drill directly into itemized works and dossiers.
              </p>
            </div>

            <div className="flex items-center space-x-4 font-mono text-xs">
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Total Works</span>
                <span className="font-bold text-slate-200">{selectedState.total_works.toLocaleString()}</span>
              </div>
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Sanctioned</span>
                <span className="font-bold text-emerald-400">₹{selectedState.sanctioned_amount_cr} Cr</span>
              </div>
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Disbursed</span>
                <span className="font-bold text-sky-400">₹{selectedState.disbursed_amount_cr} Cr</span>
              </div>
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Utilization</span>
                <span className="font-bold text-emerald-400">{selectedState.utilization_pct}%</span>
              </div>
            </div>
          </div>

          {/* District Cards Grid */}
          <div className="flex-1 overflow-y-auto">
            {loadingDistricts ? (
              <div className="py-24 text-center text-xs text-slate-400 font-mono">
                Loading district &amp; constituency telemetry for {selectedState.state_name}...
              </div>
            ) : filteredDistricts.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredDistricts.map((d) => (
                  <div
                    key={d.district_name}
                    onClick={() => handleSelectDistrict(d)}
                    className="p-4 rounded-xl bg-[#131D31] border border-slate-800/80 hover:border-sky-500/60 hover:bg-[#18233a] cursor-pointer transition-all duration-150 space-y-3 group shadow-md"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-xs font-bold text-white group-hover:text-sky-300 transition-colors">
                          {d.district_name}
                        </h3>
                        <span className="text-[10px] font-mono text-slate-400 block mt-0.5 truncate max-w-[180px]">
                          IA: {d.primary_ia}
                        </span>
                      </div>
                      <PriorityBadge priority={d.risk_tier} size="sm" />
                    </div>

                    <div className="grid grid-cols-3 gap-1 pt-2 border-t border-slate-800/60 text-[11px] font-mono">
                      <div>
                        <span className="text-[9px] text-slate-500 block">Works</span>
                        <span className="text-slate-200 font-semibold">{d.total_works}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block">Disbursed</span>
                        <span className="text-emerald-400 font-semibold">₹{d.disbursed_amount_cr} Cr</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block">Completion</span>
                        <span className="text-sky-400 font-semibold">{d.completion_pct}%</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-sky-400 group-hover:text-sky-300">
                      <span>Click to list works</span>
                      <span>→</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-24 text-center text-xs text-slate-500 font-mono">
                No districts match your filter query.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TIER 3: DISTRICT ITEMIZED WORKS TABLE WITH CLICK-ROW DOSSIER */}
      {viewLevel === 'district' && selectedDistrict && (
        <div className="flex-1 flex flex-col overflow-hidden p-6 space-y-5">
          {/* District Header Banner */}
          <div className="bg-[#131D31] border border-slate-800 p-5 rounded-2xl flex flex-wrap items-center justify-between gap-4 shadow-xl">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setViewLevel('state')}
                  className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                  title="Back to State Districts"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <h1 className="text-lg font-bold text-white tracking-tight">
                  {selectedDistrict.district_name}, {selectedState?.state_name}
                </h1>
                <PriorityBadge priority={selectedDistrict.risk_tier} size="sm" />
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Primary Implementing Agency: <span className="text-slate-200">{selectedDistrict.primary_ia}</span>
              </p>
            </div>

            <div className="flex items-center space-x-4 font-mono text-xs">
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Total Works</span>
                <span className="font-bold text-slate-200">{selectedDistrict.total_works}</span>
              </div>
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Disbursed</span>
                <span className="font-bold text-emerald-400">₹{selectedDistrict.disbursed_amount_cr} Cr</span>
              </div>
              <div className="bg-[#0B1120] border border-slate-800 px-3.5 py-2 rounded-xl text-center">
                <span className="text-[9px] text-slate-500 uppercase block">Completion Rate</span>
                <span className="font-bold text-sky-400">{selectedDistrict.completion_pct}%</span>
              </div>
            </div>
          </div>

          {/* Itemized Works Table - Entire Row Clickable */}
          <div className="bg-[#131D31] border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex-1 flex flex-col">
            <div className="p-3.5 bg-[#0B1120] border-b border-slate-800 flex items-center justify-between text-xs">
              <span className="font-bold text-slate-200 font-mono uppercase tracking-wider text-[11px]">
                Itemized Works Allocated to {selectedDistrict.district_name}
              </span>
              <span className="text-slate-400 font-mono text-[11px]">
                Showing {districtWorks.length} candidate projects • Click any row to inspect Governance Dossier
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0B1120] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800 sticky top-0">
                  <tr>
                    <th
                      onClick={() => handleSort('priority')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors group select-none"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>Priority</span>
                        {renderSortIcon('priority')}
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('work_rec_id')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors group select-none"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>Rec ID / Project</span>
                        {renderSortIcon('work_rec_id')}
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('category')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors group select-none"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>Category</span>
                        {renderSortIcon('category')}
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('mp_name')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors group select-none"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>MP Name</span>
                        {renderSortIcon('mp_name')}
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('sanction_amount')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors group select-none"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>Sanction / Disbursed</span>
                        {renderSortIcon('sanction_amount')}
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('days_rec_to_sanction')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition-colors group select-none"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>Turnaround</span>
                        {renderSortIcon('days_rec_to_sanction')}
                      </div>
                    </th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {loadingWorks ? (
                    <tr>
                      <td colSpan={7} className="py-16 text-center text-slate-400 font-mono">
                        Loading district works...
                      </td>
                    </tr>
                  ) : districtWorks.length > 0 ? (
                    districtWorks.map((w) => (
                      <tr
                        key={w.work_rec_id}
                        onClick={() => onOpenDossier(w.work_rec_id)}
                        className="hover:bg-slate-800/60 cursor-pointer transition-colors group"
                      >
                        <td className="py-3.5 px-4">
                          <PriorityBadge priority={w.priority} size="sm" />
                        </td>
                        <td className="py-3.5 px-4 max-w-xs">
                          <span className="font-mono text-slate-400 text-[11px] block">#{w.work_rec_id}</span>
                          <p className="text-slate-200 truncate font-medium group-hover:text-sky-300 transition-colors">
                            {w.description}
                          </p>
                        </td>
                        <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono">
                            {w.category}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="text-slate-300 font-medium block truncate max-w-[150px]">
                            {w.mp_name}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono">
                          <span className="text-emerald-400 block font-semibold">
                            ₹{w.sanction_amount.toLocaleString()}
                          </span>
                          <span className="text-slate-400 text-[11px] block">
                            Disb: ₹{w.total_disbursed.toLocaleString()}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-[11px]">
                          <span
                            className={clsx(
                              'px-2 py-0.5 rounded border',
                              w.days_rec_to_sanction > 45
                                ? 'bg-red-500/15 text-red-400 border-red-500/30 font-bold'
                                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            )}
                          >
                            {w.days_rec_to_sanction}d to sanction
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onOpenDossier(w.work_rec_id);
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
                      <td colSpan={7} className="py-16 text-center text-slate-500 font-mono">
                        No projects recorded for this district.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
