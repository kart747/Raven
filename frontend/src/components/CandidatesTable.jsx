import { useEffect, useState } from 'react';
import { Award, Download, ExternalLink, Search } from 'lucide-react';
import { apiUrl } from '../api';
import { formatInr } from '../lib/format';
import { useCandidateParties, useCandidates, useElections } from '../lib/queries';
import { STATES } from '../lib/states';
import { INPUT, RESET_BTN } from './ngos/constants';
import Pagination from './ui/Pagination';
import Spinner from './ui/Spinner';

const LIMIT = 10;
const VIEWS = [
  { id: 'ls', label: 'Lok Sabha 2024: all candidates', params: { house: 'Lok Sabha' } },
  { id: 'mp', label: 'Lok Sabha 2024: winners (MPs)', params: { house: 'Lok Sabha', winners_only: true } },
  { id: 'mla', label: 'Sitting MLAs (latest assembly elections)', params: { house: 'Vidhan Sabha' } },
];

export default function CandidatesTable({ initialFilterState }) {
  const [view, setView] = useState('ls');
  const [election, setElection] = useState('');
  const [search, setSearch] = useState('');
  const [party, setParty] = useState('');
  const [state, setState] = useState(initialFilterState || '');
  const [sortBy, setSortBy] = useState('');
  const [offset, setOffset] = useState(0);

  useEffect(() => { setState(initialFilterState || ''); setOffset(0); }, [initialFilterState]);

  const { data: elections = [] } = useElections();
  const assemblies = elections.filter((e) => e.house === 'Vidhan Sabha');

  const filters = {
    ...VIEWS.find((v) => v.id === view).params,
    election: view === 'mla' ? election : '',
    search, party_id: party, state, sort_by: sortBy,
  };
  const { data, isLoading, isError } = useCandidates({ ...filters, limit: LIMIT, offset });
  const { house, winners_only: winnersOnly, election: electionFilter } = filters;
  const { data: parties = [] } = useCandidateParties({ house, winners_only: winnersOnly, election: electionFilter });
  const rows = data?.data || [];
  const update = (setter) => (e) => { setter(e.target.value); setOffset(0); };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-cyan-400" /> Candidate Affidavits
          </h2>
          <p className="text-xs text-slate-400">
            Self-declared in nomination papers, compiled by ADR/MyNeta. "Cases" are pending cases declared by the
            candidate, not convictions.
          </p>
        </div>
        <button onClick={() => window.open(apiUrl('/api/v1/candidates', { ...filters, export_csv: true }))}
          className="flex items-center gap-2 self-start lg:self-center px-4 py-2 bg-cyan-950/80 border border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/50 hover:text-white rounded-xl text-xs font-semibold transition-all">
          <Download className="w-3.5 h-3.5" /> Export Filtered CSV
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {VIEWS.map((v) => (
          <button key={v.id} onClick={() => { setView(v.id); setOffset(0); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              view === v.id ? 'bg-cyan-950/60 border-cyan-700/50 text-cyan-300' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
            {v.label}
          </button>
        ))}
        {view === 'mla' && (
          <select value={election} onChange={update(setElection)} className={`${INPUT} py-1.5 text-xs appearance-none`}>
            <option value="">All assemblies ({assemblies.length})</option>
            {assemblies.map((e) => <option key={e.election} value={e.election}>{e.election} · {e.count} MLAs</option>)}
          </select>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input type="text" placeholder="Search name or constituency..." value={search} onChange={update(setSearch)}
            className={`w-full pl-10 pr-4 ${INPUT}`} />
        </div>
        <select value={state} onChange={update(setState)} className={`${INPUT} appearance-none`}>
          <option value="">All States</option>
          {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={party} onChange={update(setParty)} className={`${INPUT} appearance-none`}>
          <option value="">All Parties</option>
          {parties.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.count})</option>)}
        </select>
        <select value={sortBy} onChange={update(setSortBy)} className={`${INPUT} appearance-none`}>
          <option value="">Sort (default)</option>
          <option value="assets">Assets: high to low</option>
          <option value="criminal_cases">Declared cases: high to low</option>
        </select>
        <button onClick={() => { setSearch(''); setParty(''); setState(''); setSortBy(''); setElection(''); setOffset(0); }}
          className={RESET_BTN}>Reset Filters</button>
      </div>

      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold tracking-wider text-slate-400">
              <th className="p-4">Candidate</th>
              <th className="p-4">Constituency & Election</th>
              <th className="p-4">Education</th>
              <th className="p-4 text-center">Declared Cases</th>
              <th className="p-4 text-right">Assets</th>
              <th className="p-4 text-right">Liabilities</th>
              <th className="p-4">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900 text-sm">
            {isLoading ? (
              <tr><td colSpan="7" className="p-8"><Spinner label="Loading affidavits..." /></td></tr>
            ) : isError ? (
              <tr><td colSpan="7" className="p-8 text-center text-red-400 text-xs">Could not load candidates. Is the API running?</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan="7" className="p-8 text-center text-slate-500">
                No matching records. If this is empty without filters, run
                <code className="text-slate-300"> python -m app.cli ingest-candidates</code> /
                <code className="text-slate-300"> ingest-assemblies</code>.
              </td></tr>
            ) : rows.map((c) => (
              <tr key={c.id} className="hover:bg-slate-900/20 transition-all">
                <td className="p-4">
                  <div className="font-bold text-white text-xs tracking-wide flex items-center gap-2">
                    {c.name}
                    {c.is_winner && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-950/60 border border-emerald-800/40 text-emerald-400">
                        WON
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400">{c.party_name}</span>
                </td>
                <td className="p-4">
                  <div className="text-xs font-semibold text-slate-300">{c.constituency}</div>
                  <span className="text-[10px] text-slate-500">{c.state} · {c.election || c.year}</span>
                </td>
                <td className="p-4 text-xs text-slate-300">{c.education}</td>
                <td className="p-4 text-center">
                  <span className={`inline-flex items-center justify-center min-w-7 h-7 px-1 text-xs font-bold rounded-full ${
                    c.criminal_cases > 0 ? 'bg-red-950/60 border border-red-800/40 text-red-400' : 'bg-slate-900 border border-slate-800 text-slate-400'}`}>
                    {c.criminal_cases}
                  </span>
                </td>
                <td className="p-4 text-right text-emerald-400 font-bold tracking-tight">{formatInr(c.assets)}</td>
                <td className="p-4 text-right text-slate-400 font-bold tracking-tight">{formatInr(c.liabilities)}</td>
                <td className="p-4">
                  <a href={c.source_url} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-950 hover:bg-slate-900 border border-slate-800 text-[10px] text-cyan-400 hover:text-white transition-all font-semibold">
                    MyNeta <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination offset={offset} limit={LIMIT} total={data?.total || 0} noun="records" onChange={setOffset} />
    </div>
  );
}
