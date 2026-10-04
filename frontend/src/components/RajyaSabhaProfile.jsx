import { ExternalLink, X } from 'lucide-react';
import { useRajyaSabhaMember } from '../lib/queries';
import Spinner from './ui/Spinner';
import InTheNews from './live/InTheNews';

const year = (iso) => (iso ? iso.slice(0, 4) : '?');

/** One sitting Rajya Sabha member (sansad.in): party, state, term, and recent headlines. */
export default function RajyaSabhaProfile({ memberId, onClose, onOpenParty }) {
  const { data: m, isLoading, isError } = useRajyaSabhaMember(memberId);
  if (memberId == null) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border-cyan-500/20" onClick={(e) => e.stopPropagation()}>
        {isLoading ? <div className="p-16"><Spinner label="Loading member..." /></div> : isError || !m ? (
          <div className="p-16 text-center text-xs text-red-400">Could not load this member.</div>
        ) : (
          <>
            <div className="p-6 border-b border-slate-900 flex justify-between items-start gap-4">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">
                  Member of Parliament · Rajya Sabha{m.is_minister ? ' · Minister' : ''}
                </span>
                <h3 className="text-lg font-bold text-white">{m.name}</h3>
                {m.name_hi && <p className="text-sm text-slate-300" lang="hi">{m.name_hi}</p>}
                <p className="text-xs text-slate-400 mt-0.5">
                  {m.state === 'Nominated' ? 'Nominated member' : m.state} ·{' '}
                  {m.party_id ? (
                    <button onClick={() => onOpenParty(m.party_id)} className="hover:text-cyan-400 underline decoration-dotted">{m.party}</button>
                  ) : (m.party || 'No party')}
                </p>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-6 flex flex-col gap-6">
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="bg-slate-950/50 border border-slate-900 rounded-xl p-3">
                  <div className="text-[10px] text-slate-500 uppercase font-bold">Current term</div>
                  <div className="text-base font-black text-white">{year(m.term_start)}–{year(m.term_end)}</div>
                </div>
                <div className="bg-slate-950/50 border border-slate-900 rounded-xl p-3">
                  <div className="text-[10px] text-slate-500 uppercase font-bold">Terms in Rajya Sabha</div>
                  <div className="text-base font-black text-white">{m.terms_served ?? '—'}</div>
                </div>
                <div className="bg-slate-950/50 border border-slate-900 rounded-xl p-3">
                  <div className="text-[10px] text-slate-500 uppercase font-bold">Term ends</div>
                  <div className="text-base font-black text-white">{m.term_end || '—'}</div>
                </div>
              </div>
              <InTheNews kind="rs" refId={m.id} />
              <p className="text-[10px] text-slate-500">
                Source: <a href={m.source_url} target="_blank" rel="noopener noreferrer" className="text-cyan-500 hover:text-cyan-300 inline-flex items-center gap-0.5">
                  sansad.in Rajya Sabha members <ExternalLink className="w-3 h-3" /></a>. Assets and declared cases are not
                shown: Raven's affidavit data covers Lok Sabha and assembly candidates, not Rajya Sabha members.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
