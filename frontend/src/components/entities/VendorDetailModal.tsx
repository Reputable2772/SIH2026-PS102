import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { PriorityBadge } from '../common/PriorityBadge';
import {
  X,
  Briefcase,
  MapPin,
  Building,
  AlertTriangle,
  FileText,
  TrendingUp,
} from 'lucide-react';
import clsx from 'clsx';

interface VendorDetailModalProps {
  vendorName: string | null;
  onClose: () => void;
  onOpenDossier?: (recId: string) => void;
}

export const VendorDetailModal: React.FC<VendorDetailModalProps> = ({
  vendorName,
  onClose,
  onOpenDossier,
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!vendorName) return;
    setLoading(true);
    api.getVendorDetail(vendorName)
      .then((res) => setData(res))
      .catch((err) => console.error('Failed to load vendor detail:', err))
      .finally(() => setLoading(false));
  }, [vendorName]);

  if (!vendorName) return null;

  const profile = data?.profile;
  const districts = data?.district_distribution || [];
  const works = data?.sample_works || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0F172A] border border-slate-700/80 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#131D31]">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
              <Briefcase className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight truncate max-w-md">
                  {vendorName}
                </h2>
                {profile && (
                  <span
                    className={clsx(
                      'text-[10px] font-mono font-bold px-2 py-0.5 rounded border',
                      profile.hhi_risk === 'CONCENTRATED'
                        ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                        : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    )}
                  >
                    {profile.hhi_risk}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                Contractor Profile, District Market Share &amp; Anti-Monopoly Matrix
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

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400 font-mono">Loading contractor contracts...</p>
            </div>
          ) : profile ? (
            <>
              {/* Profile Card */}
              <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Primary State</span>
                  <span className="text-slate-200 font-bold mt-0.5 block">{profile.primary_state}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Primary Category</span>
                  <span className="text-slate-200 font-bold mt-0.5 block truncate">
                    {profile.primary_category}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Total Disbursed</span>
                  <span className="text-emerald-400 font-bold mt-0.5 block">₹{profile.total_disbursed_cr} Cr</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Total Projects</span>
                  <span className="text-sky-400 font-bold mt-0.5 block">{profile.total_works} across {profile.district_count} Dist</span>
                </div>
              </div>

              {profile.has_recurrence_flag && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>
                    <strong>VND-D14 Recurrence Flag:</strong> This contractor exhibits repeated project delay breaches or concentrated procurement awards across multiple district jurisdictions.
                  </span>
                </div>
              )}

              {/* District Spread */}
              {districts.length > 0 && (
                <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Top Execution Districts (Implementing Agencies)
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {districts.map((d: any) => (
                      <span
                        key={d.district}
                        className="px-3 py-1.5 rounded-lg bg-[#0B1120] border border-slate-800 text-xs text-slate-300 font-mono flex items-center space-x-2"
                      >
                        <span>{d.district}</span>
                        <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[10px]">
                          {d.works_count} works
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Contracts Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Sample Executed Contracts ({works.length} Shown)
                </h4>
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#131D31]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#0B1120] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Priority</th>
                        <th className="py-2.5 px-3">Project Description</th>
                        <th className="py-2.5 px-3">District</th>
                        <th className="py-2.5 px-3">Disbursed</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-sans">
                      {works.map((w: any) => (
                        <tr key={w.work_rec_id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="py-2.5 px-3">
                            <PriorityBadge priority={w.priority} size="sm" />
                          </td>
                          <td className="py-2.5 px-3 max-w-xs truncate text-slate-200">
                            {w.description}
                          </td>
                          <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                            {w.ida_name}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-emerald-400">
                            ₹{w.total_disbursed.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {onOpenDossier && (
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
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">Failed to load contractor profile.</div>
          )}
        </div>
      </div>
    </div>
  );
};
