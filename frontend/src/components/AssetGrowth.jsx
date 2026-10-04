import { useState } from 'react';
import { ExternalLink, TrendingUp } from 'lucide-react';
import { formatCrore } from '../lib/format';
import { useAssetGrowth } from '../lib/queries';
import Spinner from './ui/Spinner';

const SORTS = [
  { id: 'increase', label: 'Largest ₹ increase' },
  { id: 'pct', label: 'Largest % increase' },
  { id: 'decrease', label: 'Largest decrease' },
];
const RESULTS = [{ id: '', label: 'All' }, { id: 'won', label: 'Re-elected 2024' }, { id: 'lost', label: 'Lost 2024' }];

/** Declared assets 2019 vs 2024 for MPs elected in 2019 who stood again. */
export default function AssetGrowth({ onOpenParty }) {
  const [sort, setSort] = useState('increase');
  const [result, setResult] = useState('');
  const { data, isLoading, isError } = useAssetGrowth({ sort, result, limit: 25 });
  const s = data?.summary;
  const btn = (on) => `px-2.5 py-1 rounded-md text-[11px] border ${on ? 'border-cyan-700 text-cyan-300 bg-cyan-950/50' : 'border-slate-800 text-slate-400 hover:text-white'}`;

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-4 shadow-xl">
      <div>
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-cyan-400" /> Declared assets, 2019 → 2024
        </h2>
        <p className="text-xs text-slate-400 max-w-3xl">
          MPs elected in 2019 who stood again in 2024, compared affidavit to affidavit by MyNeta.
          {s && ` ${s.increased} of ${s.count} declared more in 2024; ${s.doubled_or_more} at least doubled; median change +${s.median_pct}%.`}
          {' '}Figures are self-declared. Percentages from small 2019 values can be very large. A change in declared
          assets is not by itself evidence of wrongdoing.
        </p>
      </div>
      <div className="flex flex-wrap gap-1">
        {SORTS.map((o) => <button key={o.id} onClick={() => setSort(o.id)} className={btn(sort === o.id)}>{o.label}</button>)}
        <span className="w-3" />
        {RESULTS.map((o) => <button key={o.label} onClick={() => setResult(o.id)} className={btn(result === o.id)}>{o.label}</button>)}
      </div>
      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold text-slate-400">
              <th className="p-3 text-left">Member</th>
              <th className="p-3 text-left">Seat (2024)</th>
              <th className="p-3 text-right">2019</th>
              <th className="p-3 text-right">2024</th>
              <th className="p-3 text-right">Change</th>
              <th className="p-3 text-left">2024 result</th>
              <th className="p-3 text-left">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900">
            {isLoading ? <tr><td colSpan="7" className="p-8"><Spinner label="Loading..." /></td></tr>
              : isError ? <tr><td colSpan="7" className="p-8 text-center text-red-400">Could not load comparisons.</td></tr>
                : data.rows.length === 0 ? <tr><td colSpan="7" className="p-8 text-center text-slate-500">
                  Not loaded yet: run <code className="text-slate-300">python -m app.cli ingest-asset-growth</code>.</td></tr>
                  : data.rows.map((r) => (
                    <tr key={r.comparison_url} className="hover:bg-slate-900/20">
                      <td className="p-3">
                        <div className="text-slate-100 font-semibold">{r.name}</div>
                        {r.party_id ? (
                          <button onClick={() => onOpenParty(r.party_id)} className="text-[10px] text-slate-400 hover:text-cyan-400">{r.party}</button>
                        ) : <span className="text-[10px] text-slate-400">{r.party}</span>}
                        {r.remarks && <div className="text-[10px] text-slate-500">{r.remarks}</div>}
                      </td>
                      <td className="p-3 text-slate-300">{r.constituency}<div className="text-[10px] text-slate-500">{r.state}</div></td>
                      <td className="p-3 text-right text-slate-400 tabular-nums">{formatCrore(r.assets_2019, 1)}</td>
                      <td className="p-3 text-right text-slate-200 tabular-nums">{formatCrore(r.assets_2024, 1)}</td>
                      <td className={`p-3 text-right tabular-nums font-bold ${r.increase >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {r.increase >= 0 ? '+' : '−'}{formatCrore(Math.abs(r.increase), 1)}
                        <div className="text-[10px] font-normal text-slate-500">{r.pct != null ? `${r.pct > 0 ? '+' : ''}${r.pct}%` : ''}</div>
                      </td>
                      <td className="p-3">{r.won_2024 ? <span className="text-emerald-400">Re-elected</span> : <span className="text-slate-500">Lost</span>}</td>
                      <td className="p-3">
                        <a href={r.comparison_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-cyan-400 hover:text-white">
                          Compare <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                    </tr>
                  ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
