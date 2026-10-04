import { useMemo, useState } from 'react';
import { Landmark, Search } from 'lucide-react';
import { useRajyaSabha } from '../lib/queries';
import Spinner from './ui/Spinner';

/** All sitting Rajya Sabha members, filterable by name, state or party. */
export default function RajyaSabhaMembers({ onOpenMember, onOpenParty }) {
  const { data, isLoading, isError } = useRajyaSabha();
  const [q, setQ] = useState('');
  const [ministers, setMinisters] = useState(false);
  const members = useMemo(() => {
    const s = q.trim().toLowerCase();
    return (data?.data || []).filter((m) => (!ministers || m.is_minister) && (!s
      || [m.name, m.name_hi, m.state, m.party, m.party_id].some((v) => v && v.toLowerCase().includes(s))));
  }, [data, q, ministers]);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-900 flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2"><Landmark className="w-4 h-4 text-cyan-400" /> Rajya Sabha</h2>
          <p className="text-[11px] text-slate-400">
            {data ? `${data.total} sitting members` : 'Sitting members'} from sansad.in. Party seats:{' '}
            {(data?.seats_by_party || []).slice(0, 6).map((p) => `${p.party} ${p.members}`).join(' · ')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <input type="checkbox" checked={ministers} onChange={(e) => setMinisters(e.target.checked)} /> Ministers only
          </label>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, state or party…"
              className="pl-8 pr-3 py-1.5 bg-slate-900/50 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50" />
          </div>
        </div>
      </div>
      {isLoading ? <Spinner label="Loading members…" /> : isError ? (
        <p className="text-xs text-red-400">Could not load Rajya Sabha members.</p>
      ) : (
        <div className="max-h-[420px] overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="text-[10px] uppercase text-slate-500 sticky top-0 bg-slate-950">
              <tr><th className="text-left py-2">Member</th><th className="text-left">State</th><th className="text-left">Party</th><th className="text-right">Term ends</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-900">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-slate-900/50">
                  <td className="py-1.5">
                    <button onClick={() => onOpenMember(m.id)} className="text-slate-100 hover:text-cyan-300 text-left">{m.name}</button>
                    {m.is_minister && <span className="ml-1.5 text-[9px] px-1 rounded border border-amber-800/60 text-amber-300">Minister</span>}
                  </td>
                  <td className="text-slate-400">{m.state}</td>
                  <td className="text-slate-400">
                    {m.party_id ? <button onClick={() => onOpenParty(m.party_id)} className="hover:text-cyan-300">{m.party_id}</button> : (m.party || '—')}
                  </td>
                  <td className="text-right text-slate-500 tabular-nums">{m.term_end || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
