import { useState } from 'react';
import { useCandidateStateSummary } from '../../lib/queries';
import { useT } from '../../lib/i18n';
import { CandidatesPanel, LegislativePanel, NgoPanel } from './DossierPanels';
import InTheNews from '../live/InTheNews';

const TABS = [
  { id: 'candidates', label: 'state.tab.ls', source: 'Source: MyNeta / ADR (Lok Sabha 2024 affidavits)' },
  { id: 'mlas', label: 'state.tab.mla', source: 'Source: MyNeta / ADR (latest assembly election affidavits)' },
  { id: 'ngos', label: 'state.tab.ngo', source: 'Source: FCRA annual returns (MHA)' },
  { id: 'legislative', label: 'state.tab.parl', source: 'Source: Lok Sabha activity (Vonter dataset)' },
  { id: 'news', label: 'state.tab.news', source: 'Source: live headlines from public feeds that name the state' },
];

export default function StateDossier({ state, candidateSummary, onOpenMp, onOpenCandidate }) {
  const t = useT();
  const tr = t;
  const [tab, setTab] = useState('candidates');
  const active = TABS.find((t) => t.id === tab);
  const { data: mlaSummary = {} } = useCandidateStateSummary('Vidhan Sabha');

  return (
    <div className="glass-panel rounded-2xl p-6 shadow-xl border border-slate-900 flex flex-col gap-4 min-h-[480px]">
      <div>
        <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest block">{t('state.profile')}</span>
        <h2 className="text-xl font-bold text-white mt-0.5">{state || t('state.select')}</h2>
      </div>

      <div className="flex border-b border-slate-900 text-xs">
        {TABS.map((tb) => (
          <button key={tb.id} onClick={() => setTab(tb.id)}
            className={`flex-1 py-2 font-bold transition-all border-b-2 ${tab === tb.id ? 'border-cyan-500 text-cyan-400' : 'border-transparent text-slate-400 hover:text-white'}`}>
            {tr(tb.label)}
          </button>
        ))}
      </div>

      {state ? (
        tab === 'candidates' ? <CandidatesPanel state={state} summary={candidateSummary} onOpenCandidate={onOpenCandidate} />
          : tab === 'mlas' ? <CandidatesPanel state={state} summary={mlaSummary[state]} house="Vidhan Sabha" noun="Sitting MLAs" onOpenCandidate={onOpenCandidate} />
          : tab === 'ngos' ? <NgoPanel state={state} />
            : tab === 'news' ? <InTheNews kind="state" refId={state} title="Latest headlines" />
              : <LegislativePanel state={state} onOpenMp={onOpenMp} />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 border border-dashed border-slate-800 rounded-2xl bg-slate-950/30 px-6 py-10">
          <h3 className="text-sm font-bold text-slate-200">{t('state.empty.title')}</h3>
          <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
            {t('state.empty.body')}
          </p>
        </div>
      )}

      <div className="text-[9px] text-slate-500 border-t border-slate-900/60 pt-2 mt-auto">
        {state ? active.source : 'No state selected'}
      </div>
    </div>
  );
}
