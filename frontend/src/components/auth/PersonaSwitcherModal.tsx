import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../api/client';
import { MPProfile, StateMapMetric, DistrictMetric } from '../../types';
import {
  X,
  UserCheck,
  Building2,
  MapPin,
  Users,
  Shield,
  Search,
  Check,
  Sparkles,
  ToggleLeft,
  ToggleRight,
  ChevronRight,
  Globe2,
} from 'lucide-react';
import clsx from 'clsx';

interface PersonaSwitcherModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PersonaSwitcherModal: React.FC<PersonaSwitcherModalProps> = ({ isOpen, onClose }) => {
  const { currentUser, switchDynamicPersona, switchPersona, loading } = useAuth();
  const { showToast } = useToast();

  const [activeTab, setActiveTab] = useState<'presets' | 'mp' | 'district' | 'state'>('presets');
  const [strictIsolation, setStrictIsolation] = useState<boolean>(currentUser?.strict_isolation ?? true);

  // MP Search state
  const [mpSearch, setMpSearch] = useState<string>('');
  const [mpList, setMpList] = useState<MPProfile[]>([]);
  const [loadingMps, setLoadingMps] = useState<boolean>(false);

  // District state
  const [states, setStates] = useState<StateMapMetric[]>([]);
  const [selectedState, setSelectedState] = useState<string>('Maharashtra');
  const [districts, setDistricts] = useState<DistrictMetric[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('PUNE');
  const [loadingDistricts, setLoadingDistricts] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    setStrictIsolation(currentUser?.strict_isolation ?? true);

    // Preload states
    api.getStateMapMetrics().then((data) => {
      setStates(data);
      if (data.length > 0 && !selectedState) {
        setSelectedState(data[0].state_name);
      }
    });

    // Preload top MPs
    searchMps('');
  }, [isOpen]);

  useEffect(() => {
    if (!selectedState) return;
    setLoadingDistricts(true);
    api.getDistrictsForState(selectedState)
      .then((dists) => {
        setDistricts(dists);
        if (dists.length > 0) {
          setSelectedDistrict(dists[0].district_name);
        }
      })
      .catch((err) => console.error('Failed to load districts:', err))
      .finally(() => setLoadingDistricts(false));
  }, [selectedState]);

  const searchMps = async (query: string) => {
    setLoadingMps(true);
    try {
      const res = await api.searchMps({ query: query.trim() || undefined, page_size: 15 });
      setMpList(res.items);
    } catch (err) {
      console.error('Failed to search MPs:', err);
    } finally {
      setLoadingMps(false);
    }
  };

  const handleMpSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setMpSearch(val);
    searchMps(val);
  };

  const handleSelectMp = async (mp: MPProfile) => {
    await switchDynamicPersona({
      role: 'MP_USER',
      mp_name: mp.mp_name,
      constituency: mp.constituency,
      state: mp.state_name,
      strict_isolation: strictIsolation,
    });
    showToast(
      'Persona Switched',
      `Now acting as Hon. ${mp.mp_name} (${mp.constituency}, ${mp.state_name})`,
      'success'
    );
    onClose();
  };

  const handleSelectDistrict = async () => {
    await switchDynamicPersona({
      role: 'DISTRICT_AUTHORITY',
      state: selectedState,
      district: selectedDistrict,
      strict_isolation: strictIsolation,
    });
    showToast(
      'Persona Switched',
      `Now acting as District Authority for ${selectedDistrict}, ${selectedState}`,
      'success'
    );
    onClose();
  };

  const handleSelectStateOfficer = async (stateName: string) => {
    await switchDynamicPersona({
      role: 'STATE_NODAL_OFFICER',
      state: stateName,
      strict_isolation: strictIsolation,
    });
    showToast(
      'Persona Switched',
      `Now acting as State Nodal Officer for ${stateName}`,
      'success'
    );
    onClose();
  };

  const handleSelectPreset = async (presetId: string, label: string) => {
    await switchDynamicPersona({
      persona_id: presetId,
      strict_isolation: strictIsolation,
    });
    showToast('Persona Switched', `Active role updated to ${label}`, 'info');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="bg-[#0F172A] border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-[#131D31]">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-sky-500/15 border border-sky-500/30 text-sky-400">
              <UserCheck className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Multi-Tenant Persona &amp; Jurisdiction Engine
              </h2>
              <p className="text-xs text-slate-400">
                Switch between statutory roles or act as any of the 775 MPs &amp; 700+ Districts nationwide
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

        {/* Global Isolation Toggle Ribbon */}
        <div className="px-6 py-3 bg-[#0B1120] border-b border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <Shield className={clsx('w-4 h-4', strictIsolation ? 'text-emerald-400' : 'text-amber-400')} />
            <span className="font-medium text-slate-300">
              Strict Tenant Boundary Enforcement:
            </span>
            <span
              className={clsx(
                'px-2 py-0.5 rounded font-mono text-[10px] font-bold border',
                strictIsolation
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
              )}
            >
              {strictIsolation ? 'ON (Statutory Isolation)' : 'OFF (All-India Sandbox)'}
            </span>
          </div>

          <button
            onClick={() => setStrictIsolation(!strictIsolation)}
            className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-[11px] transition-colors"
          >
            {strictIsolation ? (
              <>
                <ToggleRight className="w-4 h-4 text-emerald-400" />
                <span>Enforce Boundary</span>
              </>
            ) : (
              <>
                <ToggleLeft className="w-4 h-4 text-amber-400" />
                <span>Open Sandbox</span>
              </>
            )}
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center px-6 pt-3 border-b border-slate-800 space-x-2 bg-[#131D31]/50">
          <button
            onClick={() => setActiveTab('presets')}
            className={clsx(
              'px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2',
              activeTab === 'presets'
                ? 'border-sky-500 text-sky-400 bg-slate-900/60'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            )}
          >
            Official Presets
          </button>
          <button
            onClick={() => setActiveTab('mp')}
            className={clsx(
              'px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 flex items-center space-x-1.5',
              activeTab === 'mp'
                ? 'border-sky-500 text-sky-400 bg-slate-900/60'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            )}
          >
            <span>Any Member of Parliament (775)</span>
          </button>
          <button
            onClick={() => setActiveTab('district')}
            className={clsx(
              'px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2',
              activeTab === 'district'
                ? 'border-sky-500 text-sky-400 bg-slate-900/60'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            )}
          >
            Any District Authority
          </button>
          <button
            onClick={() => setActiveTab('state')}
            className={clsx(
              'px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2',
              activeTab === 'state'
                ? 'border-sky-500 text-sky-400 bg-slate-900/60'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            )}
          >
            Any State Officer
          </button>
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* TAB 1: PRESETS */}
          {activeTab === 'presets' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-400 mb-2 font-sans">
                Quick-switch to statutory demo personas configured for standard evaluation checkpoints:
              </p>
              <div className="grid grid-cols-1 gap-2.5">
                {[
                  {
                    id: 'central_auditor',
                    title: '🏛️ Central Auditor (MoSPI / CAG Analytical Wing)',
                    subtitle: 'Full all-India audit clearance across 36 States/UTs, unredacted contractor intelligence, and compliance triggers.',
                    badge: 'National Jurisdiction',
                  },
                  {
                    id: 'state_nodal_officer',
                    title: '🏢 State Nodal Officer (Maharashtra Planning Dept)',
                    subtitle: 'State oversight across 3,051 works, district bottleneck flagging, and state compliance review.',
                    badge: 'State Tenant',
                  },
                  {
                    id: 'district_authority',
                    title: '📍 District Magistrate / IDA Pune (Collector Office)',
                    subtitle: 'Direct administrative jurisdiction over 167 works, DQM inspection dispatch orders, and milestone verification.',
                    badge: 'District Tenant',
                  },
                  {
                    id: 'mp_user',
                    title: '🗳️ Member of Parliament (Hon. Supriya Sule, Baramati)',
                    subtitle: 'Portfolio tracking for 39 recommended community works, statutory SLA monitor, and constituency summaries.',
                    badge: 'Constituency Tenant',
                  },
                  {
                    id: 'citizen',
                    title: '👥 Public Citizen (Jan-Bhagidari Open Data)',
                    subtitle: 'Open social audit verification, public community works search, and masked contractor identities.',
                    badge: 'Public Transparency',
                  },
                ].map((preset) => (
                  <div
                    key={preset.id}
                    onClick={() => handleSelectPreset(preset.id, preset.title)}
                    className="p-3.5 rounded-xl bg-[#131D31] border border-slate-800 hover:border-sky-500/50 hover:bg-[#18233a] cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div>
                      <h4 className="text-xs font-bold text-white group-hover:text-sky-300 transition-colors">
                        {preset.title}
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-0.5 max-w-lg">
                        {preset.subtitle}
                      </p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0 ml-3">
                      {preset.badge}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: ANY MP */}
          {activeTab === 'mp' && (
            <div className="space-y-4">
              <div className="space-y-1">
                <p className="text-xs text-slate-400">
                  Search across all 775 Members of Parliament (Lok Sabha &amp; Rajya Sabha) to act as any representative:
                </p>
                <div className="relative pt-1">
                  <Search className="w-4 h-4 absolute left-3 top-3.5 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search MP name, constituency, or state (e.g. Modi, Rahul, Sule, Anurag, Derek)..."
                    value={mpSearch}
                    onChange={handleMpSearchChange}
                    className="w-full bg-[#0B1120] border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              </div>

              {/* Fast Presets Pills */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[
                  'Hon. Narendra Modi (Varanasi)',
                  'Hon. Rahul Gandhi (Rae Bareli)',
                  'Hon. Supriya Sule (Baramati)',
                  'Hon. Anurag Singh Thakur (Hamirpur)',
                  'Hon. Derek O Brien (West Bengal)',
                ].map((name) => (
                  <button
                    key={name}
                    onClick={() => {
                      const clean = name.replace('Hon. ', '').split(' (')[0];
                      setMpSearch(clean);
                      searchMps(clean);
                    }}
                    className="px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[11px] font-mono border border-slate-700 transition-colors"
                  >
                    {name}
                  </button>
                ))}
              </div>

              {/* MP List */}
              <div className="border border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-800/60 max-h-64 overflow-y-auto">
                {loadingMps ? (
                  <div className="py-8 text-center text-xs text-slate-400 font-mono">
                    Searching parliamentary directory...
                  </div>
                ) : mpList.length > 0 ? (
                  mpList.map((mp) => (
                    <div
                      key={mp.mp_name}
                      onClick={() => handleSelectMp(mp)}
                      className="p-3 hover:bg-slate-800/50 cursor-pointer transition-colors flex items-center justify-between group"
                    >
                      <div>
                        <h4 className="text-xs font-bold text-slate-200 group-hover:text-sky-300">
                          {mp.mp_name}
                        </h4>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {mp.house} • {mp.constituency}, {mp.state_name} ({mp.total_works} Works)
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-sky-400 group-hover:translate-x-0.5 transition-all" />
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-slate-500 font-mono">
                    No MP matching &quot;{mpSearch}&quot;.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: ANY DISTRICT */}
          {activeTab === 'district' && (
            <div className="space-y-4">
              <p className="text-xs text-slate-400">
                Choose any State and District to act as the official District Magistrate / Implementing District Authority (IDA):
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Select State / UT:</label>
                  <select
                    value={selectedState}
                    onChange={(e) => setSelectedState(e.target.value)}
                    className="w-full bg-[#0B1120] border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
                  >
                    {states.map((st) => (
                      <option key={st.state_name} value={st.state_name}>
                        {st.state_name} ({st.total_works} works)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Select District / IDA:</label>
                  <select
                    value={selectedDistrict}
                    onChange={(e) => setSelectedDistrict(e.target.value)}
                    disabled={loadingDistricts}
                    className="w-full bg-[#0B1120] border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
                  >
                    {districts.map((d) => (
                      <option key={d.district_name} value={d.district_name}>
                        {d.district_name} ({d.total_works} works)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleSelectDistrict}
                  disabled={loadingDistricts || !selectedDistrict}
                  className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs shadow-lg shadow-sky-600/20 transition-all disabled:opacity-50"
                >
                  Switch to {selectedDistrict || 'District'} Authority
                </button>
              </div>
            </div>
          )}

          {/* TAB 4: ANY STATE */}
          {activeTab === 'state' && (
            <div className="space-y-4">
              <p className="text-xs text-slate-400">
                Choose any State or Union Territory to act as the State Nodal Officer (SNO) in charge of planning &amp; monitoring:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-72 overflow-y-auto pr-1">
                {states.map((st) => (
                  <div
                    key={st.state_name}
                    onClick={() => handleSelectStateOfficer(st.state_name)}
                    className="p-3 rounded-xl bg-[#131D31] border border-slate-800 hover:border-sky-500/50 hover:bg-[#18233a] cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 group-hover:text-sky-300">
                        {st.state_name}
                      </h4>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {st.total_works.toLocaleString()} works • ₹{st.sanctioned_amount_cr} Cr
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-sky-400" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
