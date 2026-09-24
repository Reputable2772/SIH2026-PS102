import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DistrictMetric, StateMapMetric } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { DistrictDetailModal } from '../components/districts/DistrictDetailModal';
import {
  MapPin,
  Building,
  AlertTriangle,
  IndianRupee,
  Layers,
  ChevronRight,
  X,
  TrendingUp,
  FileText,
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
  const [loadingDistricts, setLoadingDistricts] = useState<boolean>(false);
  const [metric, setMetric] = useState<'alerts' | 'sanctioned' | 'utilization'>('alerts');
  const [searchFilter, setSearchFilter] = useState<string>('');

  useEffect(() => {
    api.getStateMapMetrics().then((data) => {
      setStates(data);
      if (data.length > 0) {
        handleSelectState(data[0]);
      }
    });
  }, []);

  const handleSelectState = async (st: StateMapMetric) => {
    setSelectedState(st);
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

  // Sort states actively by the selected metric toggle
  const sortedStates = [...states]
    .filter((s) => s.state_name.toLowerCase().includes(searchFilter.toLowerCase()))
    .sort((a, b) => {
      if (metric === 'alerts') return b.critical_alerts - a.critical_alerts;
      if (metric === 'sanctioned') return b.sanctioned_amount_cr - a.sanctioned_amount_cr;
      if (metric === 'utilization') return b.utilization_pct - a.utilization_pct;
      return 0;
    });

  return (
    <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
      {/* Left Panel: State Choropleth Radar & Controls */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Header & Metric Toggles */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#131D31] border border-slate-800 p-5 rounded-2xl">
          <div>
            <div className="flex items-center space-x-2">
              <MapPin className="w-5 h-5 text-sky-400" />
              <h2 className="text-base font-bold text-white tracking-tight">
                Geospatial Anomaly Radar across 36 States/UTs
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Select a state to inspect localized Implementing Agency bottlenecks and district overloads.
            </p>
          </div>

          {/* Metric Selector (Actively sorts and visualizes cards) */}
          <div className="flex items-center bg-[#0B1120] border border-slate-800 rounded-lg p-1 space-x-1">
            <button
              onClick={() => setMetric('alerts')}
              className={clsx(
                'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                metric === 'alerts'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              Alerts
            </button>
            <button
              onClick={() => setMetric('sanctioned')}
              className={clsx(
                'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                metric === 'sanctioned'
                  ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              Capital (₹ Cr)
            </button>
            <button
              onClick={() => setMetric('utilization')}
              className={clsx(
                'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                metric === 'utilization'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              Utilization %
            </button>
          </div>
        </div>

        {/* Filter Input */}
        <div className="flex items-center justify-between">
          <input
            type="text"
            placeholder="Search state or territory (e.g. Maharashtra, Uttar Pradesh)..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full max-w-sm bg-[#131D31] border border-slate-800 rounded-xl px-4 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <span className="text-xs text-slate-400 font-mono">
            Showing {sortedStates.length} of {states.length} States/UTs (Sorted by {metric.toUpperCase()})
          </span>
        </div>

        {/* Grid of State Cards (Spatial Grid Engine) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedStates.map((st) => {
            const isSelected = selectedState?.state_name === st.state_name;
            return (
              <div
                key={st.state_name}
                onClick={() => handleSelectState(st)}
                className={clsx(
                  'p-4 rounded-xl border cursor-pointer transition-all relative overflow-hidden group',
                  isSelected
                    ? 'bg-sky-950/20 border-sky-500/60 shadow-lg shadow-sky-500/5'
                    : 'bg-[#131D31] border-slate-800/80 hover:border-slate-700 hover:bg-[#18233a]'
                )}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition-colors">
                      {st.state_name}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                      {st.district_count} Districts • {st.total_works.toLocaleString()} Works
                    </p>
                  </div>
                  {st.critical_alerts > 0 ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/15 text-red-400 border border-red-500/30">
                      {st.critical_alerts} Critical
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 bg-emerald-500/15 border border-emerald-500/30">
                      Normal
                    </span>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Sanctioned</span>
                    <span className="text-slate-200 font-semibold">₹{st.sanctioned_amount_cr} Cr</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">Utilization</span>
                    <span className="text-emerald-400 font-semibold">{st.utilization_pct}%</span>
                  </div>
                </div>

                {isSelected && (
                  <div className="absolute top-0 right-0 w-1.5 h-full bg-sky-500" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Drawer: State & District Bottleneck Drilldown */}
      <div className="w-full md:w-96 bg-[#0B1120] border-t md:border-t-0 md:border-l border-slate-800/80 flex flex-col h-auto md:h-full shrink-0">
        <div className="p-5 border-b border-slate-800 bg-[#131D31]">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase font-mono text-sky-400 block font-semibold">
                District Deep-Dive
              </span>
              <h3 className="text-base font-bold text-white tracking-tight">
                {selectedState?.state_name || 'Select a State'}
              </h3>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold font-mono text-emerald-400 block">
                ₹{selectedState?.sanctioned_amount_cr || 0} Cr
              </span>
              <span className="text-[10px] text-slate-400">Total Sanction</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
            <span>District / Implementing Agency</span>
            <span>Click to Inspect</span>
          </div>

          {loadingDistricts ? (
            <div className="py-12 text-center text-xs text-slate-400 font-mono">
              Loading district bottleneck metrics...
            </div>
          ) : districts.length > 0 ? (
            districts.map((d) => (
              <div
                key={d.district_name}
                onClick={() => setSelectedDistrict(d)}
                className="p-3.5 rounded-xl bg-[#131D31] border border-slate-800 hover:border-sky-500/50 hover:bg-[#18233a] cursor-pointer transition-all space-y-2 group"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 group-hover:text-sky-300 transition-colors">
                      {d.district_name}
                    </h4>
                    <span className="text-[10px] font-mono text-slate-400 block mt-0.5 truncate max-w-[200px]">
                      IA: {d.primary_ia}
                    </span>
                  </div>
                  <PriorityBadge priority={d.risk_tier} size="sm" />
                </div>

                <div className="grid grid-cols-3 gap-1 pt-2 border-t border-slate-800/60 text-[11px] font-mono">
                  <div>
                    <span className="text-[9px] text-slate-500 block">Works</span>
                    <span className="text-slate-300">{d.total_works}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 block">Disbursed</span>
                    <span className="text-slate-300">₹{d.disbursed_amount_cr} Cr</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 block">Completion</span>
                    <span className="text-emerald-400">{d.completion_pct}%</span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="py-12 text-center text-xs text-slate-500 font-mono">
              No district records found for this state.
            </div>
          )}
        </div>
      </div>

      {/* District Drill-down Modal */}
      {selectedDistrict && (
        <DistrictDetailModal
          district={selectedDistrict}
          stateName={selectedState?.state_name || ''}
          onClose={() => setSelectedDistrict(null)}
          onOpenDossier={onOpenDossier}
        />
      )}
    </div>
  );
};
