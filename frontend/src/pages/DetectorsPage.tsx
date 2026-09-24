import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DetectorDefinition } from '../types';
import { DetectorDetailModal } from '../components/detectors/DetectorDetailModal';
import {
  ShieldAlert,
  Sliders,
  Scale,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  BookOpen,
} from 'lucide-react';
import clsx from 'clsx';

export const DetectorsPage: React.FC = () => {
  const [detectors, setDetectors] = useState<DetectorDefinition[]>([]);
  const [selectedDetector, setSelectedDetector] = useState<DetectorDefinition | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Simulation Sandbox State
  const [slaDays, setSlaDays] = useState<number>(45);
  const [executionDays, setExecutionDays] = useState<number>(365);
  const [zThreshold, setZThreshold] = useState<number>(2.5);
  const [simResults, setSimResults] = useState<any>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  useEffect(() => {
    api.getDetectors().then((data) => {
      setDetectors(data);
      setLoading(false);
    });

    // Run baseline simulation
    runSimulation(45, 365, 2.5);
  }, []);

  const runSimulation = async (sla: number, exec: number, z: number) => {
    setSimulating(true);
    try {
      const res = await api.simulateThresholds({
        sla_days: sla,
        execution_days: exec,
        z_threshold: z,
      });
      setSimResults(res);
    } catch (err) {
      console.error('Failed to run simulation:', err);
    } finally {
      setSimulating(false);
    }
  };

  const handleReset = () => {
    setSlaDays(45);
    setExecutionDays(365);
    setZThreshold(2.5);
    runSimulation(45, 365, 2.5);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8">
      {/* Header */}
      <div className="bg-[#131D31] border border-slate-800 p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Autonomous Anomaly Detectors & Statutory Rule Matrix
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Codified regulatory ceilings from MPLADS Guidelines (Para 3.2.4 &amp; 3.2.12), General Financial Rules (GFR),
            and dynamic statistical peer-group medians.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
            {detectors.length} Detectors Frozen
          </span>
        </div>
      </div>

      {/* Dynamic Threshold Simulation Sandbox */}
      <div className="bg-[#131D31] border border-slate-800 rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Live Regulatory Threshold Simulation Sandbox
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleReset}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Statutory Defaults</span>
            </button>
          </div>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {/* Slider 1: SLA Days */}
          <div className="space-y-2 bg-[#0B1120] p-4 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">Sanction SLA Floor:</span>
              <span className="text-sky-400 font-bold">{slaDays} Days</span>
            </div>
            <input
              type="range"
              min={15}
              max={90}
              step={5}
              value={slaDays}
              onChange={(e) => {
                const val = Number(e.target.value);
                setSlaDays(val);
                runSimulation(val, executionDays, zThreshold);
              }}
              className="w-full accent-sky-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block">Default: 45 days (MPLADS Para 3.2.4)</span>
          </div>

          {/* Slider 2: Execution Days */}
          <div className="space-y-2 bg-[#0B1120] p-4 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">Execution Deadline:</span>
              <span className="text-sky-400 font-bold">{executionDays} Days</span>
            </div>
            <input
              type="range"
              min={180}
              max={730}
              step={30}
              value={executionDays}
              onChange={(e) => {
                const val = Number(e.target.value);
                setExecutionDays(val);
                runSimulation(slaDays, val, zThreshold);
              }}
              className="w-full accent-sky-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block">Default: 365 days (1 statutory year)</span>
          </div>

          {/* Slider 3: Z-Score Outlier Floor */}
          <div className="space-y-2 bg-[#0B1120] p-4 rounded-xl border border-slate-800">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">Cost Outlier Threshold (Z):</span>
              <span className="text-amber-400 font-bold">{zThreshold.toFixed(1)}σ</span>
            </div>
            <input
              type="range"
              min={1.5}
              max={4.0}
              step={0.1}
              value={zThreshold}
              onChange={(e) => {
                const val = Number(e.target.value);
                setZThreshold(val);
                runSimulation(slaDays, executionDays, val);
              }}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block">Default: 2.5σ (99.4th percentile peer group)</span>
          </div>
        </div>

        {/* Live Simulation Results */}
        {simResults && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-slate-800">
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
              <span className="text-[10px] uppercase font-mono text-red-400 block">Simulated Critical Works</span>
              <span className="text-xl font-bold font-mono text-red-400 mt-1 block">
                {simResults.simulated_critical_count.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <span className="text-[10px] uppercase font-mono text-amber-400 block">Sanction SLA Breaches</span>
              <span className="text-xl font-bold font-mono text-amber-400 mt-1 block">
                {simResults.sanction_sla_breaches.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-xl">
              <span className="text-[10px] uppercase font-mono text-sky-400 block">Execution Breaches</span>
              <span className="text-xl font-bold font-mono text-sky-400 mt-1 block">
                {simResults.execution_sla_breaches.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
              <span className="text-[10px] uppercase font-mono text-yellow-300 block">Budget Overruns</span>
              <span className="text-xl font-bold font-mono text-yellow-300 mt-1 block">
                {simResults.budget_overruns.toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Detector Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {detectors.map((d) => (
          <div
            key={d.code}
            onClick={() => setSelectedDetector(d)}
            className="bg-[#131D31] border border-slate-800/90 hover:border-red-500/50 hover:bg-[#18233a] cursor-pointer rounded-xl p-5 space-y-3 transition-all flex flex-col justify-between group"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-sky-500/15 text-sky-400 border border-sky-500/30">
                  {d.code}
                </span>
                <span className="text-[10px] uppercase font-mono text-slate-500">{d.phase}</span>
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-red-300 transition-colors">{d.name}</h3>
              <p className="text-xs text-slate-300 leading-relaxed">{d.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-800/80 space-y-2 text-[11px]">
              <div>
                <span className="text-slate-500 uppercase font-mono text-[9px] block">Statutory Legal Basis</span>
                <span className="text-slate-400 font-medium">{d.legal_basis}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase font-mono text-[9px] block">Prescribed AC-19 Action</span>
                <span className="text-emerald-400/90 font-medium">{d.prescribed_action}</span>
              </div>
              <div className="text-[10px] text-red-400/80 font-mono text-right pt-1 group-hover:text-red-300">
                Click to inspect statutory formula →
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detector Detail Modal */}
      {selectedDetector && (
        <DetectorDetailModal
          detector={selectedDetector}
          onClose={() => setSelectedDetector(null)}
        />
      )}
    </div>
  );
};
