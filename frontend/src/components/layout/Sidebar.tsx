import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  MapPin,
  ShieldAlert,
  Search,
  Users2,
  HeartHandshake,
  CheckCircle2,
  SlidersHorizontal,
} from 'lucide-react';
import clsx from 'clsx';

export type NavTab = 'overview' | 'map' | 'detectors' | 'works' | 'entities' | 'citizen' | 'validation';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const { currentUser } = useAuth();
  const role = currentUser?.role || 'CENTRAL_AUDITOR';

  const allNavItems: { id: NavTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'overview',
      label: 'Executive Overview',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      id: 'map',
      label: 'Geospatial Radar',
      icon: <MapPin className="w-4 h-4" />,
      badge: '36 States',
    },
    {
      id: 'detectors',
      label: 'Anomaly Detectors',
      icon: <ShieldAlert className="w-4 h-4 text-red-400" />,
      badge: '15 Rules',
    },
    {
      id: 'works',
      label: 'Works Explorer',
      icon: <Search className="w-4 h-4" />,
      badge: '102k',
    },
    {
      id: 'entities',
      label: 'Entity Intelligence',
      icon: <Users2 className="w-4 h-4 text-sky-400" />,
    },
    {
      id: 'citizen',
      label: 'Citizen Transparency',
      icon: <HeartHandshake className="w-4 h-4 text-emerald-400" />,
    },
    {
      id: 'validation',
      label: 'Validation & ML Lab',
      icon: <SlidersHorizontal className="w-4 h-4 text-amber-400" />,
      badge: '93.4%',
    },
  ];

  // RBAC Tab Gating
  const navItems = allNavItems.filter((item) => {
    if (role === 'CITIZEN') {
      return ['overview', 'map', 'citizen'].includes(item.id);
    }
    if (role === 'MP_USER') {
      return ['overview', 'works', 'entities', 'citizen'].includes(item.id);
    }
    if (role === 'DISTRICT_AUTHORITY' || role === 'STATE_NODAL_OFFICER') {
      return ['overview', 'map', 'works', 'entities', 'detectors', 'citizen'].includes(item.id);
    }
    return true; // CENTRAL_AUDITOR
  });

  // Switch tab if current tab is hidden by active persona
  useEffect(() => {
    if (!navItems.some((item) => item.id === activeTab)) {
      if (navItems.length > 0) setActiveTab(navItems[0].id);
    }
  }, [role, navItems, activeTab, setActiveTab]);

  return (
    <aside className="w-64 bg-[#0B1120] border-r border-slate-800/80 flex flex-col justify-between py-4 select-none shrink-0">
      <div className="space-y-6">
        <div className="px-5">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider font-mono">
            Analytical Navigation
          </p>
        </div>

        <nav className="space-y-1 px-3">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={clsx(
                  'w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group',
                  isActive
                    ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                )}
              >
                <div className="flex items-center space-x-3">
                  <span className={clsx(isActive ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200')}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={clsx(
                      'text-[10px] font-mono px-1.5 py-0.5 rounded',
                      isActive ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-400'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info / SLA Badge */}
      <div className="px-4 py-3 mx-3 bg-[#131D31] border border-slate-800/80 rounded-xl space-y-2 text-xs">
        <div className="flex items-center justify-between text-slate-400">
          <span className="font-mono text-[11px]">Statutory SLA</span>
          <span className="font-mono text-[11px] text-emerald-400 font-semibold">45 Days</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="font-mono text-[11px]">Execution SLA</span>
          <span className="font-mono text-[11px] text-sky-400 font-semibold">365 Days</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="font-mono text-[11px]">Audit Engine</span>
          <span className="font-mono text-[11px] text-amber-400 font-semibold">v1.0 Frozen</span>
        </div>
      </div>
    </aside>
  );
};
