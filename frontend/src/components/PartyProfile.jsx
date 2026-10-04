import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ExternalLink, X } from 'lucide-react';
import { fiscalYear, formatCrore } from '../lib/format';
import { usePartyProfile } from '../lib/queries';
import Spinner from './ui/Spinner';
import InTheNews from './live/InTheNews';

function Stat({ label, value, sub }) {
  return (
    <div className="bg-slate-950/50 border border-slate-900 rounded-xl p-3">
      <div className="text-[10px] text-slate-500 uppercase font-bold">{label}</div>
      <div className="text-lg font-black text-white">{value}</div>
      {sub && <div className="text-[10px] text-slate-500">{sub}</div>}
    </div>
  );
}

const pct = (part, whole) => (whole ? `${Math.round((100 * part) / whole)}%` : '—');

export default function PartyProfile({ partyId, onClose, onOpenDonor, onOpenCandidate, onOpenRs }) {
  const { data: p, isLoading, isError } = usePartyProfile(partyId);
  if (!partyId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-5xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border-cyan-500/20" onClick={(e) => e.stopPropagation()}>
        {isLoading ? <div className="p-16"><Spinner label="Loading party..." /></div> : isError || !p ? (
          <div className="p-16 text-center text-xs text-red-400">Could not load this party.</div>
        ) : (
          <>
            <div className="p-6 border-b border-slate-900 flex justify-between items-start gap-4">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">Party profile · {p.id}</span>
                <h3 className="text-lg font-bold text-white">{p.name}</h3>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>

            <div className="p-6 flex flex-col gap-6">
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <Stat label="Electoral bonds received" value={formatCrore(p.bonds.total, 0)} sub={`${p.bonds.count.toLocaleString('en-IN')} bonds`} />
                <Stat label="Lok Sabha 2024" value={`${p.lok_sabha_2024.winners} won`} sub={`of ${p.lok_sabha_2024.candidates} candidates`} />
                <Stat label="Sitting MLAs" value={p.assemblies.mlas.toLocaleString('en-IN')} sub={`${p.assemblies.by_state.length} assemblies`} />
                <Stat label="Rajya Sabha" value={`${p.rajya_sabha.members} members`} sub="sitting (sansad.in)" />
                <Stat label="MP attendance (18th LS)" value={p.parliament.avg_attendance_pct != null ? `${p.parliament.avg_attendance_pct}%` : '—'}
                  sub={`${p.parliament.mps_with_activity_data} MPs with data`} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Bonds encashed per fiscal year (₹ Cr)</h4>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={p.bonds.by_fiscal_year.map((y) => ({ fy: fiscalYear(y.year), crore: +(y.amount / 1e7).toFixed(1) }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                        <XAxis dataKey="fy" stroke="#475569" fontSize={9} tickLine={false} />
                        <YAxis stroke="#475569" fontSize={9} tickLine={false} axisLine={false} width={45} />
                        <Tooltip contentStyle={{ background: '#020617', border: '1px solid #1e293b', fontSize: 11 }} formatter={(v) => [`₹${v} Cr`, 'Encashed']} />
                        <Bar dataKey="crore" fill="#06b6d4" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  {p.bonds.undisclosed_purchaser_amount > 0 && (
                    <p className="text-[10px] text-slate-500">{formatCrore(p.bonds.undisclosed_purchaser_amount)} came from bonds whose purchaser the disclosure does not name.</p>
                  )}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Largest identified purchasers</h4>
                  {p.bonds.top_purchasers.length === 0 ? <p className="text-xs text-slate-500">No electoral bonds recorded.</p> : (
                    <ol className="text-xs space-y-1 max-h-56 overflow-y-auto pr-1">
                      {p.bonds.top_purchasers.map((d, i) => (
                        <li key={d.id} className="flex justify-between gap-3">
                          <button onClick={() => onOpenDonor(d.id)} className="text-slate-200 hover:text-cyan-400 text-left truncate">{i + 1}. {d.name}</button>
                          <span className="text-emerald-400 font-bold flex-shrink-0">{formatCrore(d.amount)}</span>
                        </li>
                      ))}
                    </ol>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    MPs elected in 2024 ({p.lok_sabha_2024.mps.length})
                  </h4>
                  <p className="text-[10px] text-slate-500 mb-2">
                    {pct(p.lok_sabha_2024.candidates_declaring_cases, p.lok_sabha_2024.candidates)} of the party's 2024 candidates declared
                    pending criminal cases; average declared assets {formatCrore(p.lok_sabha_2024.avg_declared_assets)}.
                  </p>
                  <div className="max-h-64 overflow-y-auto pr-1 flex flex-col gap-1">
                    {p.lok_sabha_2024.mps.map((m) => (
                      <button key={m.id} onClick={() => onOpenCandidate(m.id)}
                        className="w-full text-left flex justify-between gap-3 text-xs p-1.5 rounded hover:bg-slate-900">
                        <span className="text-slate-200 truncate">{m.name} <span className="text-slate-500">· {m.constituency}, {m.state}</span></span>
                        <span className="text-slate-400 flex-shrink-0 flex items-center gap-1">
                          {formatCrore(m.assets, 1)}{m.criminal_cases > 0 && <span className="text-red-400"> · {m.criminal_cases} cases</span>}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">MLAs by assembly</h4>
                  <p className="text-[10px] text-slate-500 mb-2">
                    {pct(p.assemblies.mlas_declaring_cases, p.assemblies.mlas)} of the party's sitting MLAs declared pending criminal cases.
                  </p>
                  <div className="max-h-64 overflow-y-auto pr-1 flex flex-col gap-1 text-xs">
                    {p.assemblies.by_state.map((s) => (
                      <div key={s.election} className="flex justify-between p-1.5">
                        <span className="text-slate-200">{s.election}</span>
                        <span className="text-slate-400">{s.mlas} MLAs</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {p.rajya_sabha.members > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Rajya Sabha members ({p.rajya_sabha.members})</h4>
                  <div className="max-h-48 overflow-y-auto pr-1 grid grid-cols-1 md:grid-cols-2 gap-x-4">
                    {p.rajya_sabha.list.map((m) => (
                      <button key={m.id} onClick={() => onOpenRs(m.id)}
                        className="text-left flex justify-between gap-2 text-xs p-1.5 rounded hover:bg-slate-900">
                        <span className="text-slate-200 truncate">{m.name}{m.is_minister ? ' · Minister' : ''}</span>
                        <span className="text-slate-500 flex-shrink-0">{m.state}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <InTheNews kind="party" refId={p.id} />

              <ul className="text-[10px] text-slate-500 list-disc pl-4 space-y-0.5">
                {p.notes.map((n) => <li key={n}>{n}</li>)}
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
