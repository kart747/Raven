import { ExternalLink, X } from 'lucide-react';
import { formatCrore } from '../lib/format';
import { useCandidateProfile } from '../lib/queries';
import Spinner from './ui/Spinner';

const pctChange = (a, b) => (b ? `${a >= b ? '+' : ''}${Math.round((100 * (a - b)) / b)}%` : 'n/a');

/** One candidate or MLA: affidavit, change since the previous affidavit, and the rest of the seat. */
export default function CandidateProfile({ candidateId, onClose, onOpenParty, onOpenMp, onOpenCandidate }) {
  const { data: c, isLoading, isError } = useCandidateProfile(candidateId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border-cyan-500/20" onClick={(e) => e.stopPropagation()}>
        {isLoading ? <div className="p-16"><Spinner label="Loading..." /></div> : isError || !c ? (
          <div className="p-16 text-center text-xs text-red-400">Could not load this candidate.</div>
        ) : (
          <>
            <div className="p-6 border-b border-slate-900 flex justify-between items-start gap-4">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">
                  {c.house === 'Vidhan Sabha' ? 'MLA' : c.is_winner ? 'Elected' : 'Candidate'} · {c.election}
                </span>
                <h3 className="text-lg font-bold text-white">{c.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {c.constituency}, {c.state} ·{' '}
                  <button onClick={() => onOpenParty(c.party_id)} className="hover:text-cyan-400 underline decoration-dotted">{c.party}</button>
                  {c.is_winner && <span className="ml-2 text-emerald-400 font-bold">WON</span>}
                </p>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>

            <div className="p-6 flex flex-col gap-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="text-xs space-y-1.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Affidavit</h4>
                  <div className="flex justify-between"><span className="text-slate-400">Declared assets</span><span className="text-emerald-400 font-bold">{formatCrore(c.assets)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Declared liabilities</span><span className="text-slate-200">{formatCrore(c.liabilities)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Pending criminal cases declared</span>
                    <span className={c.criminal_cases ? 'text-red-400 font-bold' : 'text-slate-200'}>{c.criminal_cases}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Education</span><span className="text-slate-200">{c.education}</span></div>
                  <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-cyan-400 hover:text-white pt-1">
                    Full affidavit on MyNeta <ExternalLink className="w-3 h-3" />
                  </a>
                  {c.mp_id && (
                    <button onClick={() => onOpenMp(c.mp_id)} className="block text-cyan-400 hover:text-white">Parliament record →</button>
                  )}
                </div>
                <div className="text-xs space-y-1.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Change since previous affidavit</h4>
                  {c.asset_change ? (
                    <>
                      <div className="flex justify-between"><span className="text-slate-400">{c.asset_change.previous_election}</span><span className="text-slate-200">{formatCrore(c.asset_change.previous_assets)}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">{c.election}</span><span className="text-slate-200">{formatCrore(c.asset_change.assets)}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Change</span>
                        <span className="font-bold text-emerald-400">{pctChange(c.asset_change.assets, c.asset_change.previous_assets)}</span></div>
                      {c.asset_change.remarks && <div className="text-[10px] text-slate-500">{c.asset_change.remarks}</div>}
                      <a href={c.asset_change.comparison_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-cyan-400 hover:text-white">
                        Side-by-side on MyNeta <ExternalLink className="w-3 h-3" />
                      </a>
                    </>
                  ) : <p className="text-slate-500">Only published for members who stood again after winning the previous election.</p>}
                </div>
              </div>

              {c.seat_field.length > 1 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Everyone who stood in {c.constituency} ({c.seat_field.length})</h4>
                  <div className="flex flex-col gap-0.5 max-h-64 overflow-y-auto pr-1 text-xs">
                    {c.seat_field.map((o) => (
                      <button key={o.id} onClick={() => onOpenCandidate(o.id)}
                        className={`flex justify-between gap-3 p-1.5 rounded text-left hover:bg-slate-900 ${o.id === c.id ? 'bg-slate-900/70' : ''}`}>
                        <span className="text-slate-200 truncate">{o.name} <span className="text-slate-500">· {o.party_id}</span>
                          {o.is_winner && <span className="ml-1 text-emerald-400 text-[10px] font-bold">WON</span>}</span>
                        <span className="text-slate-400 flex-shrink-0 tabular-nums">{formatCrore(o.assets, 1)}{o.criminal_cases > 0 && <span className="text-red-400"> · {o.criminal_cases} cases</span>}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <ul className="text-[10px] text-slate-500 list-disc pl-4 space-y-0.5">{c.notes.map((n) => <li key={n}>{n}</li>)}</ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
