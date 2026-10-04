import React, { Suspense, lazy, useEffect, useState } from 'react';
import { AlertCircle, Award, BarChart3, Database, Flag, Globe, Landmark, Search, Sparkles, UserCheck } from 'lucide-react';
import DashboardStats from './components/DashboardStats';
import IndiaMap from './components/IndiaMap';
import useHashParams from './lib/useHashParams';
import { LANGS, LangContext, translate } from './lib/i18n';
import PibTicker from './components/dashboard/PibTicker';
import BondFlows from './components/dashboard/BondFlows';
import KeyFacts from './components/dashboard/KeyFacts';
import StateDossier from './components/dashboard/StateDossier';
import { useCandidateStateSummary, useDashboardStats, useNgoStateTotals, useParties } from './lib/queries';

// Tabs and profile windows load on demand to keep the first page light
const DonationsTable = lazy(() => import('./components/DonationsTable'));
const CandidatesTable = lazy(() => import('./components/CandidatesTable'));
const NgosTracker = lazy(() => import('./components/NgosTracker'));
const LegislativeTracker = lazy(() => import('./components/LegislativeTracker'));
const Sources = lazy(() => import('./components/Sources'));
const BriefViewer = lazy(() => import('./components/BriefViewer'));
const DonorProfile = lazy(() => import('./components/DonorProfile'));
const PartyProfile = lazy(() => import('./components/PartyProfile'));
const MpProfile = lazy(() => import('./components/MpProfile'));
const NgoDetailModal = lazy(() => import('./components/ngos/NgoDetailModal'));
const SearchPalette = lazy(() => import('./components/SearchPalette'));
const SeatMap = lazy(() => import('./components/SeatMap'));
const PartyScoreboard = lazy(() => import('./components/PartyScoreboard'));
const AssetGrowth = lazy(() => import('./components/AssetGrowth'));

// Widgets available at #embed=<id> for use in <iframe>s
const EMBEDS = {
  flows: (p) => <BondFlows onOpenDonor={p.onOpenDonor} onOpenParty={p.onOpenParty} />,
  facts: (p) => <KeyFacts onNavigate={p.onNavigate} />,
  map: (p) => <IndiaMap selectedState={null} onSelectState={p.onSelectState}
    lsSummary={p.lsSummary} vsSummary={p.vsSummary} ngoTotals={p.ngoTotals} />,
  seats: (p) => <Suspense fallback={null}><SeatMap onOpenMp={p.onOpenMp} /></Suspense>,
};

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'parties', label: 'Parties', icon: Flag },
  { id: 'donations', label: 'Electoral Bonds', icon: Landmark },
  { id: 'candidates', label: 'Candidates', icon: Award },
  { id: 'ngos', label: 'NGO Funding', icon: Globe },
  { id: 'legislative', label: 'Parliament', icon: UserCheck },
  { id: 'brief', label: 'AI Brief', icon: Sparkles },
  { id: 'sources', label: 'Sources', icon: Database },
];

export default function App() {
  // View state lives in the URL hash so any view can be bookmarked or shared
  const [hash, setHash] = useHashParams();
  const lang = LANGS.some((l) => l.id === hash.lang) ? hash.lang : 'en';
  const t = (key) => translate(lang, key);
  const activeTab = TABS.some((t) => t.id === hash.tab) ? hash.tab : 'dashboard';
  const selectedState = hash.state || null;
  const donorId = hash.donor ? Number(hash.donor) : null;
  const ngoId = hash.ngo ? Number(hash.ngo) : null;
  const partyId = hash.party || null;
  const mpId = hash.mp ? Number(hash.mp) : null;
  const setActiveTab = (tab) => setHash({ tab: tab === 'dashboard' ? null : tab });
  const setSelectedState = (state) => setHash({ state });
  const setDonorId = (id) => setHash({ donor: id });
  const setNgoId = (id) => setHash({ ngo: id });
  const setPartyId = (id) => setHash({ party: id });
  const setMpId = (id) => setHash({ mp: id });

  const [searchOpen, setSearchOpen] = useState(false);
  const embed = hash.embed;
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
  const { data: mlaStats = {} } = useCandidateStateSummary('Vidhan Sabha');
  const { data: ngoTotals = {} } = useNgoStateTotals();

  if (EMBEDS[embed]) {
    // Embed mode: one widget, a credit line, links open the full site
    const open = (patch) => window.open(`${window.location.pathname}#${new URLSearchParams(
      Object.entries(patch).filter(([, v]) => v != null)).toString()}`, '_blank', 'noopener');
    return (
      <LangContext.Provider value={lang}>
        <div className="min-h-screen bg-slate-950 text-slate-100 p-3 flex flex-col gap-2">
          {EMBEDS[embed]({
            onOpenDonor: (donor) => open({ donor }), onOpenParty: (party) => open({ party }), onOpenMp: (mp) => open({ mp }),
            onNavigate: (link) => open(link), onSelectState: (state) => open({ state }),
            lsSummary: stateStats, vsSummary: mlaStats, ngoTotals,
          })}
          <a href={window.location.pathname} target="_blank" rel="noopener noreferrer" className="text-[10px] text-slate-500 hover:text-slate-300">
            Source: Raven, open public-records data on Indian politics · {window.location.host}
          </a>
        </div>
      </LangContext.Provider>
    );
  }

  return (
    <LangContext.Provider value={lang}>
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="sticky top-0 z-50 bg-slate-950/85 backdrop-blur-md border-b border-slate-900 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 lg:py-0 lg:h-16 flex flex-wrap lg:flex-nowrap items-center gap-x-4 gap-y-2">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center font-black text-black select-none">
              R
            </div>
            <div>
              <span className="text-sm font-black tracking-wider text-white uppercase block leading-tight">Raven</span>
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest leading-none">{t('app.tagline')}</span>
            </div>
          </div>

          {/* Below lg the tabs get their own scrollable row under the logo and controls */}
          <nav className="order-last lg:order-none w-full lg:w-auto lg:flex-1 flex items-center gap-0.5 overflow-x-auto -mx-1 px-1 pb-1 lg:pb-0">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setHash({ tab: id === 'dashboard' ? null : id, state: id === 'dashboard' ? null : selectedState })}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                  activeTab === id
                    ? 'bg-slate-900 border border-slate-800 text-cyan-400 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900/30'
                }`}
              >
                <Icon className="w-3.5 h-3.5 hidden 2xl:block" />
                {t(`nav.${id}`) || label}
              </button>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2 flex-shrink-0">
          <button onClick={() => setSearchOpen(true)} title="Search everything (press /)"
            className="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-400 hover:text-white hover:border-slate-700">
            <Search className="w-3.5 h-3.5" /> <span className="hidden sm:inline">{t('app.search')}</span> <kbd className="hidden sm:inline text-[10px] text-slate-600">/</kbd>
          </button>
          <div className="flex-shrink-0 flex rounded-lg border border-slate-800 overflow-hidden text-[11px]">
            {LANGS.map((l) => (
              <button key={l.id} onClick={() => setHash({ lang: l.id === 'en' ? null : l.id })}
                className={`px-2 py-1.5 ${lang === l.id ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'}`}>
                {l.label}
              </button>
            ))}
          </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-8">
        <div className="mb-6 border border-slate-800 bg-slate-950 rounded-xl p-3.5 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-400 leading-normal">
            <strong className="text-slate-200">{t('notice.title')}</strong> {t('notice.body')}
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
                {hash.map === 'seats' ? (
                  <Suspense fallback={<div className="glass-panel rounded-2xl min-h-[480px]" />}>
                    <SeatMap onOpenMp={setMpId} onShowStates={() => setHash({ map: null })} />
                  </Suspense>
                ) : (
                  <IndiaMap selectedState={selectedState} onSelectState={setSelectedState}
                    lsSummary={stateStats} vsSummary={mlaStats} ngoTotals={ngoTotals} onShowSeats={() => setHash({ map: 'seats' })} />
                )}
              </div>
              <div className="lg:col-span-5">
                <StateDossier state={selectedState} candidateSummary={stateStats[selectedState]} onOpenMp={setMpId} />
              </div>
            </div>
          </div>
        )}

        <Suspense fallback={<div className="py-16 text-center text-xs text-slate-500">Loading…</div>}>
        {activeTab === 'parties' && <PartyScoreboard onOpenParty={setPartyId} />}
        {activeTab === 'donations' && <DonationsTable parties={parties} onOpenDonor={setDonorId} />}
        {activeTab === 'candidates' && (
          <div className="flex flex-col gap-6">
            <CandidatesTable initialFilterState={selectedState} />
            <AssetGrowth onOpenParty={setPartyId} />
          </div>
        )}
        {activeTab === 'ngos' && <NgosTracker onOpenNgo={setNgoId} />}
        {activeTab === 'legislative' && <LegislativeTracker onOpenMp={setMpId} />}
        {activeTab === 'brief' && <BriefViewer />}
        {activeTab === 'sources' && <Sources />}
        </Suspense>
      </main>

      <Suspense fallback={null}>
      {donorId != null && <DonorProfile donorId={donorId} onClose={() => setDonorId(null)} onOpenParty={(id) => setHash({ donor: null, party: id })} />}
      {partyId && <PartyProfile partyId={partyId} onClose={() => setPartyId(null)} onOpenDonor={(id) => setHash({ party: null, donor: id })} />}
      {ngoId != null && <NgoDetailModal ngoId={ngoId} onClose={() => setNgoId(null)} />}
      {mpId != null && <MpProfile mpId={mpId} onClose={() => setMpId(null)} onOpenParty={(id) => setHash({ mp: null, party: id })} />}
      {searchOpen && (
        <SearchPalette
          open={searchOpen}
          onClose={() => setSearchOpen(false)}
          onOpenDonor={setDonorId}
          onOpenNgo={setNgoId}
          onOpenState={(state) => setHash({ tab: null, state })}
          onOpenMp={setMpId}
          onOpenParty={setPartyId}
        />
      )}
      </Suspense>

      <footer className="bg-slate-950 border-t border-slate-900 mt-12 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          <p>
            Raven · {t('footer.data')} ·{' '}
            <a href="https://github.com/kart747/Raven" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300">{t('footer.code')}</a> ·{' '}
            <a href="https://github.com/kart747/Raven/issues/new?template=data-correction.yml" target="_blank" rel="noopener noreferrer" className="text-amber-400/80 hover:text-amber-300">{t('footer.report')}</a>
          </p>
        </div>
      </footer>
    </div>
    </LangContext.Provider>
  );
}
