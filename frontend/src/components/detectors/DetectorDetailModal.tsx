import React from 'react';
import { DetectorDefinition } from '../../types';
import {
  X,
  ShieldAlert,
  Scale,
  BookOpen,
  CheckCircle2,
  FileCode,
  AlertTriangle,
} from 'lucide-react';

interface DetectorDetailModalProps {
  detector: DetectorDefinition | null;
  onClose: () => void;
}

export const DetectorDetailModal: React.FC<DetectorDetailModalProps> = ({
  detector,
  onClose,
}) => {
  if (!detector) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0F172A] border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#131D31]">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-red-500/15 border border-red-500/30 text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 rounded font-mono text-xs font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30">
                  {detector.code}
                </span>
                <h2 className="text-base font-bold text-white tracking-tight">
                  {detector.name}
                </h2>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {detector.phase} • Category: {detector.category}
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
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Description */}
          <div className="p-4 bg-[#131D31] border border-slate-800 rounded-xl space-y-1">
            <span className="text-[10px] font-mono uppercase text-slate-500 block">Detector Purpose</span>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">{detector.description}</p>
          </div>

          {/* Legal Basis Card */}
          <div className="p-4 bg-[#131D31] border border-slate-800 rounded-xl space-y-2">
            <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold font-mono">
              <BookOpen className="w-4 h-4" />
              <span>Statutory Legal Basis &amp; Mandate</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-mono bg-[#0B1120] p-3 rounded-lg border border-slate-800">
              {detector.legal_basis}
            </p>
          </div>

          {/* Threshold & Formula */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-[#131D31] border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold font-mono">
                <Scale className="w-4 h-4" />
                <span>Statutory Threshold Ceiling</span>
              </div>
              <p className="text-xs text-slate-300 font-mono bg-[#0B1120] p-3 rounded-lg border border-slate-800">
                {detector.threshold}
              </p>
            </div>

            <div className="p-4 bg-[#131D31] border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold font-mono">
                <FileCode className="w-4 h-4" />
                <span>Mathematical Logic / Expression</span>
              </div>
              <p className="text-xs text-slate-300 font-mono bg-[#0B1120] p-3 rounded-lg border border-slate-800 break-all">
                {detector.formula}
              </p>
            </div>
          </div>

          {/* Prescribed AC-19 Action */}
          <div className="p-4 bg-[#131D31] border border-slate-800 rounded-xl space-y-2">
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold font-mono">
              <CheckCircle2 className="w-4 h-4" />
              <span>Prescribed AC-19 Administrative &amp; Vigilance Action</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed bg-[#0B1120] p-3 rounded-lg border border-slate-800">
              {detector.prescribed_action}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
