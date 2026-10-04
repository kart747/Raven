import { useMemo, useState } from 'react';
import { ArrowDownUp, Flag } from 'lucide-react';
import { formatCrore } from '../lib/format';
import { usePartyScoreboard } from '../lib/queries';
import Spinner from './ui/Spinner';

const COLUMNS = [
  { key: 'party', label: 'Party', align: 'left' },
  { key: 'bonds_amount', label: 'Electoral bonds received', fmt: (v) => (v ? formatCrore(v, 0) : '—') },
  { key: 'mps_2024', label: 'MPs won 2024' },
  { key: 'ls_candidates', label: 'LS 2024 candidates' },
  { key: 'ls_candidates_with_cases_pct', label: 'Candidates declaring cases', fmt: (v) => (v == null ? '—' : `${v}%`) },
  { key: 'avg_mp_assets', label: 'Avg MP assets', fmt: (v) => (v ? formatCrore(v, 1) : '—') },
  { key: 'mlas', label: 'Sitting MLAs' },
  { key: 'mlas_with_cases_pct', label: 'MLAs declaring cases', fmt: (v) => (v == null ? '—' : `${v}%`) },
];

/** Every party side by side across bonds, Parliament and assemblies. */
export default function PartyScoreboard({ onOpenParty }) {
  const { data = [], isLoading, isError } = usePartyScoreboard();
  const [sort, setSort] = useState({ key: 'mps_2024', desc: true });
  const [query, setQuery] = useState('');

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = data.filter((r) => !q || r.party.toLowerCase().includes(q) || r.party_id.toLowerCase().includes(q));
    return [...filtered].sort((a, b) => {
      const x = a[sort.key] ?? -1;
      const y = b[sort.key] ?? -1;
      const c = typeof x === 'string' ? x.localeCompare(y) : x - y;
      return sort.desc ? -c : c;
    });
  }, [data, sort, query]);

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2"><Flag className="w-5 h-5 text-cyan-400" /> Parties</h2>
          <p className="text-xs text-slate-400 max-w-3xl">
            Money in (electoral bonds, Apr 2019 – Feb 2024) next to representation (2024 Lok Sabha, sitting MLAs) and
            self-declared affidavits. "Declaring cases" means pending criminal cases declared, not convictions. Parties are
            matched by MyNeta's label, so post-split factions are separate rows. Click a party for its profile.
          </p>
        </div>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter parties…"
          className="px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50" />
      </div>

      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold text-slate-400">
              {COLUMNS.map((c) => (
                <th key={c.key} className={`p-3 ${c.align === 'left' ? 'text-left' : 'text-right'}`}>
                  <button onClick={() => setSort((s) => ({ key: c.key, desc: s.key === c.key ? !s.desc : c.key !== 'party' }))}
                    className={`inline-flex items-center gap-1 hover:text-white ${sort.key === c.key ? 'text-cyan-300' : ''}`}>
                    {c.label} <ArrowDownUp className="w-3 h-3 opacity-50" />
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900">
            {isLoading ? (
              <tr><td colSpan={COLUMNS.length} className="p-8"><Spinner label="Loading parties..." /></td></tr>
            ) : isError ? (
              <tr><td colSpan={COLUMNS.length} className="p-8 text-center text-red-400">Could not load parties.</td></tr>
            ) : rows.map((r) => (
              <tr key={r.party_id} onClick={() => onOpenParty(r.party_id)} className="hover:bg-slate-900/40 cursor-pointer">
                {COLUMNS.map((c) => (
                  <td key={c.key} className={`p-3 ${c.align === 'left' ? 'text-left text-slate-100 font-semibold' : 'text-right text-slate-300 tabular-nums'}`}>
                    {c.key === 'party' ? <>{r.party}{r.party !== r.party_id && <span className="ml-1.5 text-[10px] text-slate-500">{r.party_id}</span>}</>
                      : c.fmt ? c.fmt(r[c.key]) : (r[c.key] || 0).toLocaleString('en-IN')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[10px] text-slate-500">{rows.length} parties with at least one MP or MLA, or electoral bond receipts.</p>
    </div>
  );
}
