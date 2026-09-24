import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { PriorityBadge } from '../common/PriorityBadge';
import {
  X,
  User,
  MapPin,
  Building,
  CheckCircle,
  FileText,
  TrendingUp,
  Award,
} from 'lucide-react';
import clsx from 'clsx';

interface MpDetailModalProps {
  mpName: string | null;
  onClose: () => void;
  onOpenDossier?: (recId: string) => void;
}

export const MpDetailModal: React.FC<MpDetailModalProps> = ({
  mpName,
  onClose,
  onOpenDossier,
}) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!mpName) return;
    setLoading(true);
    api.getMpDetail(mpName)
      .then((res) => setData(res))
      .catch((err) => console.error('Failed to load MP detail:', err))
      .finally(() => setLoading(false));
  }, [mpName]);

  if (!mpName) return null;

  const profile = data?.profile;
  const categories = data?.category_distribution || [];
  const works = data?.sample_works || [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fadeIn"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-[#0F172A] border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#131D31]">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-sky-500/15 border border-sky-500/30 text-sky-400">
              <User className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  {mpName}
                </h2>
                {profile && <PriorityBadge priority={profile.risk_tier} size="sm" />}
              </div>
              <p className="text-xs text-slate-400">
                Parliamentary Portfolio, Quota Allocations &amp; Work Recommendations
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
              <p className="text-xs text-slate-400 font-mono">Loading MP portfolio metrics...</p>
            </div>
          ) : profile ? (
            <>
              {/* Profile Card */}
              <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">House / Tenure</span>
                  <span className="text-slate-200 font-bold mt-0.5 block">{profile.house}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Constituency</span>
                  <span className="text-slate-200 font-bold mt-0.5 block truncate">
                    {profile.constituency}, {profile.state_name}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Total Works</span>
                  <span className="text-sky-400 font-bold mt-0.5 block">{profile.total_works} Recommended</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Quota Utilization</span>
                  <span className="text-emerald-400 font-bold mt-0.5 block">{profile.utilization_pct}%</span>
                </div>
              </div>

              {/* Financial Snapshot */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#131D31] border border-slate-800 p-4 rounded-xl text-center">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Allocated Quota</span>
                  <span className="text-base font-bold font-mono text-slate-200 mt-1 block">
                    ₹{profile.allocated_amount_cr || 0} Cr
                  </span>
                </div>
                <div className="bg-[#131D31] border border-slate-800 p-4 rounded-xl text-center">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Sanctioned</span>
                  <span className="text-base font-bold font-mono text-emerald-400 mt-1 block">
                    ₹{profile.sanctioned_amount_cr} Cr
                  </span>
                </div>
                <div className="bg-[#131D31] border border-slate-800 p-4 rounded-xl text-center">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Disbursed</span>
                  <span className="text-base font-bold font-mono text-sky-400 mt-1 block">
                    ₹{profile.disbursed_amount_cr} Cr
                  </span>
                </div>
              </div>

              {/* Category Breakdown */}
              {categories.length > 0 && (
                <div className="bg-[#131D31] border border-slate-800 rounded-xl p-5 space-y-3">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Top Recommended Project Categories
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {categories.map((c: any) => (
                      <span
                        key={c.name}
                        className="px-3 py-1.5 rounded-lg bg-[#0B1120] border border-slate-800 text-xs text-slate-300 font-mono flex items-center space-x-2"
                      >
                        <span>{c.name}</span>
                        <span className="px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 text-[10px]">
                          {c.count} works
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Recommended Works Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Recommended Works ({works.length} Shown)
                </h4>
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#131D31]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#0B1120] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Priority</th>
                        <th className="py-2.5 px-3">Project Description</th>
                        <th className="py-2.5 px-3">Sanction</th>
                        <th className="py-2.5 px-3">Disbursed</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-sans">
                      {works.map((w: any) => (
                        <tr
                          key={w.work_rec_id}
                          onClick={() => {
                            if (onOpenDossier) {
                              onClose();
                              onOpenDossier(w.work_rec_id);
                            }
                          }}
                          className="hover:bg-slate-800/60 cursor-pointer transition-colors"
                        >
                          <td className="py-2.5 px-3">
                            <PriorityBadge priority={w.priority} size="sm" />
                          </td>
                          <td className="py-2.5 px-3 max-w-xs truncate text-slate-200">
                            {w.description}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-emerald-400">
                            ₹{w.sanction_amount.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-slate-300">
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
            <div className="py-12 text-center text-slate-500 text-xs">Failed to load MP portfolio.</div>
          )}
        </div>
      </div>
    </div>
  );
};
