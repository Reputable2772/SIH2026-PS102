import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { CanonicalWork, DistrictMetric } from '../../types';
import { PriorityBadge } from '../common/PriorityBadge';
import {
  X,
  MapPin,
  Building,
  AlertTriangle,
  IndianRupee,
  FileText,
  CheckCircle,
} from 'lucide-react';

interface DistrictDetailModalProps {
  district: DistrictMetric | null;
  stateName: string;
  onClose: () => void;
  onOpenDossier: (recId: string) => void;
}

export const DistrictDetailModal: React.FC<DistrictDetailModalProps> = ({
  district,
  stateName,
  onClose,
  onOpenDossier,
}) => {
  const [works, setWorks] = useState<CanonicalWork[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!district) return;
    setLoading(true);
    api.searchWorks({
      state: stateName,
      district: district.district_name,
      page_size: 15,
    })
      .then((res) => setWorks(res.items))
      .catch((err) => console.error('Failed to load district works:', err))
      .finally(() => setLoading(false));
  }, [district, stateName]);

  if (!district) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0F172A] border border-slate-700/80 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#131D31]">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-sky-500/15 border border-sky-500/30 text-sky-400">
              <MapPin className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  {district.district_name}, {stateName}
                </h2>
                <PriorityBadge priority={district.risk_tier} size="sm" />
              </div>
              <p className="text-xs text-slate-400">
                Primary Implementing Agency: <span className="text-slate-200 font-mono">{district.primary_ia}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metrics Ribbon */}
          <div className="bg-[#131D31] border border-slate-800 rounded-xl p-4 grid grid-cols-3 gap-3 text-center font-mono">
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Total Works</span>
              <span className="text-base font-bold text-slate-200 mt-1 block">{district.total_works} Projects</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Disbursed Funds</span>
              <span className="text-base font-bold text-emerald-400 mt-1 block">₹{district.disbursed_amount_cr} Cr</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Completion Rate</span>
              <span className="text-base font-bold text-sky-400 mt-1 block">{district.completion_pct}%</span>
            </div>
          </div>

          {/* District Works Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                Works Allocated to {district.district_name}
              </h4>
              <span className="text-xs font-mono text-slate-400">
                Showing top priority candidates
              </span>
            </div>

            <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#131D31]">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0B1120] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Priority</th>
                    <th className="py-2.5 px-3">Description</th>
                    <th className="py-2.5 px-3">MP</th>
                    <th className="py-2.5 px-3">Sanction</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-slate-400 font-mono">
                        Loading district works...
                      </td>
                    </tr>
                  ) : works.length > 0 ? (
                    works.map((w) => (
                      <tr key={w.work_rec_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-2.5 px-3">
                          <PriorityBadge priority={w.priority} size="sm" />
                        </td>
                        <td className="py-2.5 px-3 max-w-xs truncate text-slate-200">
                          {w.description}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 text-[11px] truncate max-w-[120px]">
                          {w.mp_name}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400">
                          ₹{w.sanction_amount.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => {
                              onClose();
                              onOpenDossier(w.work_rec_id);
                            }}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-[11px]"
                          >
                            <FileText className="w-3 h-3" />
                            <span>Dossier</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-slate-500 font-mono">
                        No projects recorded for this district.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
