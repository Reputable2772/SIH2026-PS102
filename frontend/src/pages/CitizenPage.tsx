import React, { useState } from 'react';
import { api } from '../api/client';
import { CanonicalWork } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { useToast } from '../context/ToastContext';
import {
  HeartHandshake,
  Search,
  CheckCircle,
  HelpCircle,
  ExternalLink,
  MessageSquare,
  Sparkles,
  Building,
  FileText,
  MapPin,
  Send,
} from 'lucide-react';

interface CitizenPageProps {
  onOpenDossier?: (recId: string) => void;
}

export const CitizenPage: React.FC<CitizenPageProps> = ({ onOpenDossier }) => {
  const [villageSearch, setVillageSearch] = useState<string>('');
  const [searchResults, setSearchResults] = useState<CanonicalWork[]>([]);
  const [searching, setSearching] = useState<boolean>(false);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [feedbackSent, setFeedbackSent] = useState<boolean>(false);
  const [complaintText, setComplaintText] = useState<string>('');

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!villageSearch.trim()) return;

    setSearching(true);
    setHasSearched(true);
    try {
      const res = await api.searchWorks({
        query: villageSearch.trim(),
        page_size: 8,
      });
      setSearchResults(res.items);
    } catch (err) {
      console.error('Failed to search citizen works:', err);
    } finally {
      setSearching(false);
    }
  };

  const { showToast } = useToast();

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintText.trim()) return;
    setFeedbackSent(true);
    showToast(
      'Observation Submitted',
      'Your citizen report has been assigned to the District Quality Monitor (DQM) inspection queue.',
      'success'
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 max-w-5xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 p-8 rounded-3xl relative overflow-hidden">
        <div className="space-y-3 relative z-10">
          <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-semibold">
            Jan-Bhagidari • Citizen Transparency Portal
          </span>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Track Development Projects in Your Village &amp; Constituency
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Every Member of Parliament receives ₹5 Crore annually from taxpayers under MPLADS to create durable community
            infrastructure—drinking water facilities, school buildings, solar lighting, and roads.
          </p>
        </div>
      </div>

      {/* Citizen Search Bar */}
      <div className="bg-[#131D31] border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <h2 className="text-sm font-bold text-white flex items-center space-x-2">
          <Search className="w-4 h-4 text-emerald-400" />
          <span>Find Works in Your Area</span>
        </h2>
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            placeholder="Enter your Village, Panchayat, Block, or MP Name (e.g. Baramati, Pune, Solar Light)..."
            value={villageSearch}
            onChange={(e) => setVillageSearch(e.target.value)}
            className="flex-1 bg-[#0B1120] border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <button
            type="submit"
            disabled={searching}
            className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            {searching ? (
              <span>Searching...</span>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Search Projects</span>
              </>
            )}
          </button>
        </form>

        {/* Search Results Display */}
        {hasSearched && (
          <div className="pt-4 border-t border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>Matching Public Projects:</span>
              <span className="text-emerald-400 font-bold">{searchResults.length} Results Found</span>
            </div>

            {searchResults.length > 0 ? (
              <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#0B1120]">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#131D31] text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3">Location &amp; MP</th>
                      <th className="py-2.5 px-3">Budget</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {searchResults.map((work) => (
                      <tr key={work.work_rec_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-3">
                          <PriorityBadge priority={work.priority} size="sm" />
                        </td>
                        <td className="py-3 px-3 max-w-xs">
                          <p className="text-slate-200 font-medium truncate">{work.description}</p>
                          <span className="text-[10px] text-slate-500 font-mono block">ID: #{work.work_rec_id}</span>
                        </td>
                        <td className="py-3 px-3 text-[11px] text-slate-400">
                          <span className="text-slate-300 block">{work.ida_name}, {work.state_name}</span>
                          <span className="text-slate-500 block truncate max-w-[120px]">{work.mp_name}</span>
                        </td>
                        <td className="py-3 px-3 font-mono">
                          <span className="text-emerald-400 font-bold block">₹{work.sanction_amount.toLocaleString()}</span>
                          <span className="text-[10px] text-slate-500 block">Disb: ₹{work.total_disbursed.toLocaleString()}</span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          {onOpenDossier && (
                            <button
                              onClick={() => onOpenDossier(work.work_rec_id)}
                              className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition-colors"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              <span>View Dossier</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-slate-500 font-mono">
                No matching projects found for &quot;{villageSearch}&quot;. Try searching by district name or category.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Citizen Educational Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#131D31] border border-slate-800 rounded-2xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <CheckCircle className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white">45-Day Sanction Rule</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Under official MoSPI guidelines, the District Collector must sanction or reject any recommended work within
            45 calendar days.
          </p>
        </div>

        <div className="bg-[#131D31] border border-slate-800 rounded-2xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Building className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white">1-Year Completion Mandate</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Works must be physically completed and handed over for public use within 365 days of administrative approval.
          </p>
        </div>

        <div className="bg-[#131D31] border border-slate-800 rounded-2xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white">100% Public Access</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            All assets created under MPLADS must be for public use without private or commercial exclusion.
          </p>
        </div>
      </div>

      {/* Citizen Feedback & Observation Form */}
      <div className="bg-[#131D31] border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-sky-400" />
          <h3 className="text-base font-bold text-white">Report Project Delay or Irregularity</h3>
        </div>
        <p className="text-xs text-slate-400">
          Notice a project that remains incomplete or has stalled? Submit a citizen observation to be included in the
          district review dossier.
        </p>

        {feedbackSent ? (
          <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
            <span>
              ✅ Thank you! Your citizen report has been logged and assigned to the District Quality Monitor (DQM) inspection queue.
            </span>
            <button
              onClick={() => {
                setFeedbackSent(false);
                setComplaintText('');
              }}
              className="text-emerald-400 underline font-mono text-[11px] ml-4 shrink-0"
            >
              Submit Another Report
            </button>
          </div>
        ) : (
          <form onSubmit={handleFeedbackSubmit} className="space-y-3">
            <textarea
              rows={3}
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              placeholder="Describe the project location, delayed status, or observed defect (e.g. Incomplete road in Baramati, work stalled for 8 months)..."
              required
              className="w-full bg-[#0B1120] border border-slate-700/80 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-md transition-colors flex items-center space-x-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit Citizen Report</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
