import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ExternalLink, X } from 'lucide-react';
import { formatCrore } from '../lib/format';
import { useDonorProfile } from '../lib/queries';
import Spinner from './ui/Spinner';

/** Monthly encashment totals, with every event month present so reference lines have an x position. */
function monthlySeries(profile) {
  const totals = {};
  profile.monthly_encashments.forEach(({ month, amount }) => {
    totals[month] = (totals[month] || 0) + amount;
  });
  profile.events.forEach((e) => {
    const month = e.event_date.slice(0, 7);
    totals[month] = totals[month] || 0;
  });
  // Continuous month axis: months with no encashments are shown as zero, not skipped
  const months = Object.keys(totals).sort();
  if (!months.length) return [];
  const series = [];
  let [y, m] = months[0].split('-').map(Number);
  const last = months[months.length - 1];
  for (;;) {
    const key = `${y}-${String(m).padStart(2, '0')}`;
    series.push({ month: key, crore: +((totals[key] || 0) / 1e7).toFixed(2) });
    if (key >= last) break;
    m += 1;
    if (m > 12) { m = 1; y += 1; }
  }
  return series;
}

export default function DonorProfile({ donorId, onClose, onOpenParty }) {
  const { data: p, isLoading, isError } = useDonorProfile(donorId);
  if (donorId == null) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border-cyan-500/20"
        onClick={(e) => e.stopPropagation()}>
        {isLoading ? (
          <div className="p-16"><Spinner label="Loading purchaser profile..." /></div>
        ) : isError || !p ? (
          <div className="p-16 text-center text-xs text-red-400">Could not load this purchaser.</div>
        ) : (
          <>
            <div className="p-6 border-b border-slate-900 flex justify-between items-start gap-4">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">Electoral bond purchaser</span>
                <h3 className="text-lg font-bold text-white">{p.name}</h3>
                <p className="text-xs text-slate-400 mt-1">
                  {formatCrore(p.total_amount)} across {p.bond_count} encashed bonds
                  {p.industry && p.industry !== 'Unknown' && ` · ${p.industry}`}
                </p>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 flex flex-col gap-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Encashments by month (₹ Cr)</h4>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={monthlySeries(p)} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                      <XAxis dataKey="month" stroke="#475569" fontSize={9} tickLine={false} />
                      <YAxis stroke="#475569" fontSize={9} tickLine={false} axisLine={false} width={40} />
                      <Tooltip contentStyle={{ background: '#020617', border: '1px solid #1e293b', fontSize: 11 }}
                        formatter={(v) => [`₹${v} Cr`, 'Encashed']} />
                      <Bar dataKey="crore" fill="#06b6d4" radius={[3, 3, 0, 0]} />
                      {p.events.map((e) => (
                        <ReferenceLine key={e.id} x={e.event_date.slice(0, 7)} stroke="#f59e0b" strokeDasharray="4 3"
                          label={{ value: e.event_type, position: 'top', fill: '#f59e0b', fontSize: 9 }} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-[10px] text-slate-500">{p.note}</p>

                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-4">
                  Lok Sabha questions naming this company ({p.questions_naming?.length || 0})
                </h4>
                {p.questions_naming?.length ? (
                  <div className="flex flex-col gap-1.5 max-h-56 overflow-y-auto pr-1">
                    {p.questions_naming.map((q) => (
                      <a key={q.id} href={q.official_url} target="_blank" rel="noopener noreferrer"
                        className="p-2 bg-slate-950/60 border border-slate-900 hover:border-slate-700 rounded-lg text-xs">
                        <span className="text-slate-500 text-[10px]">{q.date} · {q.ministry} · {q.representative}</span>
                        <p className="text-slate-200">{q.title}</p>
                      </a>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No question titles name this company.</p>
                )}
                <p className="text-[10px] text-slate-500">
                  Exact name matches in question titles only. Asking about a company says nothing about the member's
                  relationship with it.
                </p>

                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-4">Sourced events</h4>
                {p.events.length === 0 ? (
                  <p className="text-xs text-slate-500">
                    No events loaded for this purchaser. Add sourced rows to data/entity_events.csv and run
                    <code className="text-slate-300"> python -m app.cli ingest-events</code>.
                  </p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {p.events.map((e) => (
                      <a key={e.id} href={e.source_url} target="_blank" rel="noopener noreferrer"
                        className="p-3 bg-slate-950/60 border border-slate-900 hover:border-slate-700 rounded-xl text-xs flex justify-between gap-3">
                        <div>
                          <span className="text-amber-400 font-bold uppercase text-[10px]">{e.event_type}</span>
                          <span className="text-slate-500 text-[10px] ml-2">{e.event_date}</span>
                          <p className="text-slate-200 mt-0.5">{e.description}</p>
                        </div>
                        <span className="text-cyan-400 flex items-center gap-1 text-[10px] flex-shrink-0">
                          {e.source_name || 'Source'} <ExternalLink className="w-3 h-3" />
                        </span>
                      </a>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-5">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Received by</h4>
                  <div className="flex flex-col gap-1.5">
                    {p.by_party.map((row) => (
                      <div key={row.party_id} className="text-xs">
                        <div className="flex justify-between">
                          <button onClick={() => onOpenParty?.(row.party_id)} className="text-slate-200 hover:text-cyan-400 text-left">
                            {row.party_name}
                          </button>
                          <span className="text-emerald-400 font-bold">{formatCrore(row.amount)}</span>
                        </div>
                        <div className="h-1.5 bg-slate-900 rounded mt-1">
                          <div className="h-1.5 bg-cyan-500 rounded" style={{ width: `${(100 * row.amount) / p.total_amount}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Spellings in the SBI data</h4>
                  <ul className="text-[11px] text-slate-300 space-y-1">
                    {p.spellings_in_source.map((s) => (
                      <li key={s.raw_name} className="flex justify-between gap-2">
                        <span className="font-mono break-all">{s.raw_name}</span>
                        <span className="text-slate-500 flex-shrink-0">{s.bond_count} bonds bought</span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-[10px] text-slate-500 mt-2">
                    Spellings are merged when they differ only in spacing, punctuation, "&amp;/AND" or the legal suffix, or
                    when the source cut a long name short.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
