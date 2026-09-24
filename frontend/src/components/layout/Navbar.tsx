import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { PersonaSwitcherModal } from '../auth/PersonaSwitcherModal';
import {
  Building2,
  UserCheck,
  Search,
  Shield,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';

interface NavbarProps {
  onSearch?: (query: string) => void;
  onNavigateToWorks?: (filter?: any) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onSearch, onNavigateToWorks }) => {
  const { currentUser, loading } = useAuth();
  const [isSwitcherOpen, setIsSwitcherOpen] = useState<boolean>(false);
  const [navSearch, setNavSearch] = useState<string>('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!navSearch.trim()) return;
    if (onSearch) {
      onSearch(navSearch.trim());
    } else if (onNavigateToWorks) {
      onNavigateToWorks({ query: navSearch.trim() });
    }
  };

  const getRoleDisplayName = () => {
    if (!currentUser) return 'Authorized Auditor';
    if (currentUser.role === 'MP_USER') {
      return `🗳️ ${currentUser.name} (${currentUser.constituency || 'MP'})`;
    }
    if (currentUser.role === 'DISTRICT_AUTHORITY') {
      return `📍 DM ${currentUser.district || 'District'} (${currentUser.state || ''})`;
    }
    if (currentUser.role === 'STATE_NODAL_OFFICER') {
      return `🏢 SNO (${currentUser.state || 'State'})`;
    }
    if (currentUser.role === 'CENTRAL_AUDITOR') {
      return '🏛️ Central Auditor (MoSPI / CAG)';
    }
    return '👥 Public Citizen';
  };

  return (
    <>
      <header className="h-16 bg-[#0B1120] border-b border-slate-800/80 sticky top-0 z-40 px-6 flex items-center justify-between backdrop-blur-md select-none">
        {/* Brand Identity */}
        <div className="flex items-center space-x-3.5 shrink-0">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 via-sky-500 to-indigo-700 flex items-center justify-center shadow-lg shadow-sky-500/10 border border-sky-400/30">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-100 tracking-tight text-base">MPLADS e-SAKSHI</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-400 border border-sky-500/30">
                MoSPI DIID • SIH PS102
              </span>
            </div>
            <p className="text-[11px] text-slate-400 flex items-center space-x-1">
              <span>Autonomous Intelligence &amp; Review Prioritization Platform</span>
            </p>
          </div>
        </div>

        {/* Center Quick Search Bar with ⌘K Badge */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
          <form onSubmit={handleSearchSubmit} className="w-full relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search 102k+ works by ID, MP, district, keyword..."
              value={navSearch}
              onChange={(e) => setNavSearch(e.target.value)}
              className="w-full bg-[#131D31] border border-slate-800 rounded-xl pl-9 pr-12 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500 transition-all focus:border-sky-500/50"
            />
            <div className="absolute right-2.5 top-2 flex items-center pointer-events-none">
              <kbd className="px-1.5 py-0.5 text-[9px] font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700 rounded shadow-sm">
                ⌘K
              </kbd>
            </div>
          </form>
        </div>

        {/* Right Controls: Dynamic Persona Switcher Button & Profile */}
        <div className="flex items-center space-x-3 shrink-0">
          {/* Dynamic Persona Trigger Button */}
          <button
            onClick={() => setIsSwitcherOpen(true)}
            className="flex items-center space-x-2.5 px-3 py-1.5 rounded-xl bg-[#131D31] hover:bg-[#18233a] border border-slate-800 hover:border-sky-500/50 text-xs transition-all group shadow-sm"
          >
            <div className="flex items-center space-x-2 text-left">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <div>
                <span className="text-[10px] font-mono text-slate-400 block leading-tight">
                  Jurisdiction &amp; Role:
                </span>
                <span className="font-semibold text-slate-200 group-hover:text-sky-300 transition-colors block truncate max-w-[190px]">
                  {getRoleDisplayName()}
                </span>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-400 transition-colors ml-1" />
          </button>

          {/* User Mini Avatar */}
          <div className="hidden sm:flex items-center space-x-2.5 pl-2 border-l border-slate-800 text-right">
            <div>
              <p className="text-xs font-semibold text-slate-200 truncate max-w-[120px]">
                {currentUser?.name || 'Officer'}
              </p>
              <div className="flex items-center justify-end space-x-1">
                {currentUser?.strict_isolation ? (
                  <span className="text-[9px] font-mono px-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    SCOPED
                  </span>
                ) : (
                  <span className="text-[9px] font-mono px-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    SANDBOX
                  </span>
                )}
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center text-xs font-bold text-sky-400 font-mono shadow-sm">
              {currentUser?.name ? currentUser.name.charAt(0) : 'U'}
            </div>
          </div>
        </div>
      </header>

      {/* Dynamic Persona & Jurisdiction Modal */}
      <PersonaSwitcherModal
        isOpen={isSwitcherOpen}
        onClose={() => setIsSwitcherOpen(false)}
      />
    </>
  );
};
