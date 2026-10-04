import React, { useEffect, useState } from 'react';
import { AlertCircle, Award, BarChart3, Database, Globe, Landmark, Search, Sparkles, UserCheck } from 'lucide-react';
import DashboardStats from './components/DashboardStats';
import IndiaMap from './components/IndiaMap';
import DonationsTable from './components/DonationsTable';
import CandidatesTable from './components/CandidatesTable';
import NgosTracker from './components/NgosTracker';
import LegislativeTracker from './components/LegislativeTracker';
import Sources from './components/Sources';
import BriefViewer from './components/BriefViewer';
import DonorProfile from './components/DonorProfile';
import PartyProfile from './components/PartyProfile';
import NgoDetailModal from './components/ngos/NgoDetailModal';
import SearchPalette from './components/SearchPalette';
import useHashParams from './lib/useHashParams';
import PibTicker from './components/dashboard/PibTicker';
import BondFlows from './components/dashboard/BondFlows';
import KeyFacts from './components/dashboard/KeyFacts';
import StateDossier from './components/dashboard/StateDossier';
import { useCandidateStateSummary, useDashboardStats, useParties } from './lib/queries';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'donations', label: 'Electoral Bonds', icon: Landmark },
  { id: 'candidates', label: 'Candidate Affidavits', icon: Award },
  { id: 'ngos', label: 'NGO Funding', icon: Globe },
  { id: 'legislative', label: 'Parliament Activity', icon: UserCheck },
  { id: 'brief', label: 'AI Brief', icon: Sparkles },
  { id: 'sources', label: 'Sources & Data Quality', icon: Database },
];

export default function App() {
  // View state lives in the URL hash so any view can be bookmarked or shared
  const [hash, setHash] = useHashParams();
  const activeTab = TABS.some((t) => t.id === hash.tab) ? hash.tab : 'dashboard';
  const selectedState = hash.state || null;
  const donorId = hash.donor ? Number(hash.donor) : null;
  const ngoId = hash.ngo ? Number(hash.ngo) : null;
  const partyId = hash.party || null;
  const setActiveTab = (tab) => setHash({ tab: tab === 'dashboard' ? null : tab });
  const setSelectedState = (state) => setHash({ state });
  const setDonorId = (id) => setHash({ donor: id });
  const setNgoId = (id) => setHash({ ngo: id });
  const setPartyId = (id) => setHash({ party: id });

  const [searchOpen, setSearchOpen] = useState(false);
  useEffect(() => {
    const onKey = (e) => {
      const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);
      if (e.key === '/' && !typing) { e.preventDefault(); setSearchOpen(true); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const { data: parties = [] } = useParties();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: stateStats = {} } = useCandidateStateSummary();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="sticky top-0 z-50 bg-slate-950/85 backdrop-blur-md border-b border-slate-900 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center font-black text-black select-none">
              R
            </div>
            <div>
              <span className="text-sm font-black tracking-wider text-white uppercase block leading-tight">Raven</span>
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest leading-none">OSINT Transparency Portal</span>
            </div>
          </div>

          <nav className="flex items-center gap-1 overflow-x-auto">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setHash({ tab: id === 'dashboard' ? null : id, state: id === 'dashboard' ? null : selectedState })}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                  activeTab === id
                    ? 'bg-slate-900 border border-slate-800 text-cyan-400 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900/30'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </nav>

          <button onClick={() => setSearchOpen(true)} title="Search everything (press /)"
            className="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-400 hover:text-white hover:border-slate-700">
            <Search className="w-3.5 h-3.5" /> Search <kbd className="text-[10px] text-slate-600">/</kbd>
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 border border-slate-800 bg-slate-950 rounded-xl p-3.5 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-400 leading-normal">
            <strong className="text-slate-200">About this data:</strong> every figure comes from a public source
            (SBI/ECI electoral bond disclosure, MyNeta affidavits, FCRA returns, Lok Sabha records, PIB) and links back to it.
            Coverage gaps are listed under Sources &amp; Data Quality.
          </div>
        </div>

        {activeTab === 'dashboard' && (
          <div className="flex flex-col gap-6">
            <KeyFacts onNavigate={(link) => setHash(link)} />
            <DashboardStats stats={stats} loading={statsLoading} onOpenDonor={setDonorId} onOpenParty={setPartyId} />
            <BondFlows onOpenDonor={setDonorId} onOpenParty={setPartyId} />
            <PibTicker />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              <div className="lg:col-span-7">
                <IndiaMap selectedState={selectedState} onSelectState={setSelectedState} stateStats={stateStats} />
              </div>
              <div className="lg:col-span-5">
                <StateDossier state={selectedState} candidateSummary={stateStats[selectedState]} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'donations' && <DonationsTable parties={parties} onOpenDonor={setDonorId} />}
        {activeTab === 'candidates' && <CandidatesTable initialFilterState={selectedState} />}
        {activeTab === 'ngos' && <NgosTracker onOpenNgo={setNgoId} />}
        {activeTab === 'legislative' && <LegislativeTracker />}
        {activeTab === 'brief' && <BriefViewer />}
        {activeTab === 'sources' && <Sources />}
      </main>

      <DonorProfile donorId={donorId} onClose={() => setDonorId(null)} onOpenParty={(id) => setHash({ donor: null, party: id })} />
      <PartyProfile partyId={partyId} onClose={() => setPartyId(null)} onOpenDonor={(id) => setHash({ party: null, donor: id })} />
      <NgoDetailModal ngoId={ngoId} onClose={() => setNgoId(null)} />
      <SearchPalette
        open={searchOpen}
        onClose={() => setSearchOpen(false)}
        onOpenDonor={setDonorId}
        onOpenNgo={setNgoId}
        onOpenState={(state) => setHash({ tab: null, state })}
        onOpenParty={setPartyId}
      />

      <footer className="bg-slate-950 border-t border-slate-900 mt-12 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          <p>
            Raven · Data: SBI/ECI, ADR/MyNeta, MHA FCRA returns, Lok Sabha (via Vonter), PIB ·{' '}
            <a href="https://github.com/kart747/Raven" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300">Source code (AGPL-3.0)</a> ·{' '}
            <a href="https://github.com/kart747/Raven/issues/new?template=data-correction.yml" target="_blank" rel="noopener noreferrer" className="text-amber-400/80 hover:text-amber-300">Report an error</a>
          </p>
        </div>
      </footer>
    </div>
  );
}
