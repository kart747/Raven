import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Download, ExternalLink, MessageSquareText, Search } from 'lucide-react';
import { apiUrl } from '../api';
import { useQuestionMinistries, useQuestions, useQuestionStats } from '../lib/queries';
import { INPUT, RESET_BTN } from './ngos/constants';
import Pagination from './ui/Pagination';
import Spinner from './ui/Spinner';

const LIMIT = 15;
const HOUSES = [
  { n: '', label: 'All (2009 onwards)' },
  { n: 18, label: '18th (2024–)' },
  { n: 17, label: '17th (2019–24)' },
  { n: 16, label: '16th (2014–19)' },
  { n: 15, label: '15th (2009–14)' },
];

/** Search every Lok Sabha question since 2009; each row links to the official answer on sansad.in. */
export default function QuestionsExplorer() {
  const [lokSabha, setLokSabha] = useState('');
  const [search, setSearch] = useState('');
  const [ministry, setMinistry] = useState('');
  const [member, setMember] = useState('');
  const [offset, setOffset] = useState(0);

  const { data: stats } = useQuestionStats(lokSabha);
  const { data: ministries = [] } = useQuestionMinistries();
  const params = { lok_sabha: lokSabha, search, ministry, representative: member };
  const { data, isLoading, isError } = useQuestions({ ...params, limit: LIMIT, offset });
  const rows = data?.data || [];
  const update = (setter) => (e) => { setter(e.target.value); setOffset(0); };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <MessageSquareText className="w-5 h-5 text-cyan-400" /> Lok Sabha Questions
          </h2>
          <p className="text-xs text-slate-400">
            {stats ? `${stats.total.toLocaleString('en-IN')} questions` : 'Questions'} asked by MPs
            {stats?.date_range?.[0] && ` (${stats.date_range[0]} to ${stats.date_range[1]})`}, each linked to the official answer.
          </p>
        </div>
        <button onClick={() => window.open(apiUrl('/api/v1/questions', { ...params, export_csv: true }))}
          className="flex items-center gap-2 self-start px-4 py-2 bg-cyan-950/80 border border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/50 hover:text-white rounded-xl text-xs font-semibold transition-all">
          <Download className="w-3.5 h-3.5" /> Export CSV
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {HOUSES.map((h) => (
          <button key={h.label} onClick={() => { setLokSabha(h.n); setOffset(0); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              lokSabha === h.n ? 'bg-cyan-950/60 border-cyan-700/50 text-cyan-300' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
            {h.label}
          </button>
        ))}
      </div>

      {stats && stats.total > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 h-56 bg-slate-950/30 rounded-xl border border-slate-900 p-3">
            <div className="text-[10px] text-slate-400 font-bold uppercase mb-1">Most-asked ministries</div>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart data={stats.by_ministry.slice(0, 10)} layout="vertical" margin={{ left: 10, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                <XAxis type="number" stroke="#475569" fontSize={9} tickLine={false} axisLine={false} />
                <YAxis dataKey="ministry" type="category" stroke="#475569" fontSize={9} width={150} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#020617', border: '1px solid #1e293b', fontSize: 11 }} />
                <Bar dataKey="count" fill="#06b6d4" radius={[0, 3, 3, 0]} cursor="pointer"
                  onClick={(d) => { setMinistry(d.ministry); setOffset(0); }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-slate-950/30 rounded-xl border border-slate-900 p-3 text-xs">
            <div className="text-[10px] text-slate-400 font-bold uppercase mb-2">Members who asked the most</div>
            <ol className="space-y-1">
              {stats.top_askers.map((a, i) => (
                <li key={a.representative} className="flex justify-between gap-2">
                  <button onClick={() => { setMember(a.representative); setOffset(0); }}
                    className="text-slate-200 hover:text-cyan-400 text-left truncate">{i + 1}. {a.representative}</button>
                  <span className="text-slate-500 flex-shrink-0">{a.count.toLocaleString('en-IN')}</span>
                </li>
              ))}
            </ol>
            <p className="text-[10px] text-slate-500 mt-2">Joint questions count once for each member who asked.</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input type="text" placeholder="Words in the question title..." value={search} onChange={update(setSearch)}
            className={`w-full pl-10 pr-4 ${INPUT}`} />
        </div>
        <input type="text" placeholder="Member name..." value={member} onChange={update(setMember)} className={INPUT} />
        <select value={ministry} onChange={update(setMinistry)} className={`${INPUT} appearance-none`}>
          <option value="">All ministries</option>
          {ministries.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <button onClick={() => { setSearch(''); setMinistry(''); setMember(''); setOffset(0); }} className={RESET_BTN}>Reset Filters</button>
      </div>

      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold tracking-wider text-slate-400">
              <th className="p-3">Date</th>
              <th className="p-3">Question</th>
              <th className="p-3">Ministry</th>
              <th className="p-3">Asked by</th>
              <th className="p-3">Answer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900 text-xs">
            {isLoading ? (
              <tr><td colSpan="5" className="p-8"><Spinner label="Searching questions..." /></td></tr>
            ) : isError ? (
              <tr><td colSpan="5" className="p-8 text-center text-red-400">Could not load questions.</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan="5" className="p-8 text-center text-slate-500">
                No questions match. If this is empty without filters, run <code className="text-slate-300">python -m app.cli ingest-questions</code>.
              </td></tr>
            ) : rows.map((q) => (
              <tr key={q.id} className="hover:bg-slate-900/20">
                <td className="p-3 text-slate-400 whitespace-nowrap">{q.date}</td>
                <td className="p-3 text-slate-100">
                  {q.title}
                  {q.question_type === 'Starred' && <span className="ml-2 text-[9px] text-amber-400 font-bold">STARRED</span>}
                </td>
                <td className="p-3 text-slate-400">{q.ministry}</td>
                <td className="p-3 text-slate-300">{q.representative}</td>
                <td className="p-3">
                  <a href={q.official_url} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-cyan-400 hover:text-white font-semibold">
                    PDF <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination offset={offset} limit={LIMIT} total={data?.total || 0} noun="questions" onChange={setOffset} />
    </div>
  );
}
