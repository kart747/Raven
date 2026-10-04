import { ExternalLink, X } from 'lucide-react';
import { formatCrore } from '../lib/format';
import { useMpProfile } from '../lib/queries';
import Spinner from './ui/Spinner';

function Stat({ label, value }) {
  return (
    <div className="bg-slate-950/50 border border-slate-900 rounded-xl p-3">
      <div className="text-[10px] text-slate-500 uppercase font-bold">{label}</div>
      <div className="text-lg font-black text-white">{value}</div>
    </div>
  );
}

/** One Lok Sabha MP: affidavit (MyNeta) + parliamentary record (Lok Sabha via Vonter). */
export default function MpProfile({ mpId, onClose, onOpenParty }) {
  const { data: m, isLoading, isError } = useMpProfile(mpId);
  if (mpId == null) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border-cyan-500/20" onClick={(e) => e.stopPropagation()}>
        {isLoading ? <div className="p-16"><Spinner label="Loading MP..." /></div> : isError || !m ? (
          <div className="p-16 text-center text-xs text-red-400">Could not load this MP.</div>
        ) : (
          <>
            <div className="p-6 border-b border-slate-900 flex justify-between items-start gap-4">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">Member of Parliament · 18th Lok Sabha</span>
                <h3 className="text-lg font-bold text-white">{m.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {m.constituency}, {m.state} ·{' '}
                  {m.party_id ? (
                    <button onClick={() => onOpenParty(m.party_id)} className="hover:text-cyan-400 underline decoration-dotted">{m.party}</button>
                  ) : m.party}
                </p>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>

            <div className="p-6 flex flex-col gap-6">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <Stat label="Attendance" value={m.activity.attendance_pct != null ? `${m.activity.attendance_pct}%` : 'n/a'} />
                <Stat label="Debates" value={m.activity.debates} />
                <Stat label="Questions (18th LS)" value={m.activity.questions} />
                <Stat label="Private member bills" value={m.activity.private_member_bills} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">2024 affidavit</h4>
                  {m.affidavit ? (
                    <div className="text-xs space-y-1.5">
                      <div className="flex justify-between"><span className="text-slate-400">Declared assets</span><span className="text-emerald-400 font-bold">{formatCrore(m.affidavit.assets)}</span></div>
                      {m.asset_change_since_2019 && (
                        <div className="flex justify-between">
                          <span className="text-slate-400">Declared in 2019</span>
                          <a href={m.asset_change_since_2019.comparison_url} target="_blank" rel="noopener noreferrer" className="text-slate-200 hover:text-cyan-400">
                            {formatCrore(m.asset_change_since_2019.assets_2019)} ({m.asset_change_since_2019.assets_2019
                              ? `${m.asset_change_since_2019.assets_2024 >= m.asset_change_since_2019.assets_2019 ? '+' : ''}${Math.round(100 * (m.asset_change_since_2019.assets_2024 - m.asset_change_since_2019.assets_2019) / m.asset_change_since_2019.assets_2019)}% since`
                              : 'n/a'})
                          </a>
                        </div>
                      )}
                      <div className="flex justify-between"><span className="text-slate-400">Declared liabilities</span><span className="text-slate-200">{formatCrore(m.affidavit.liabilities)}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Pending criminal cases declared</span>
                        <span className={m.affidavit.criminal_cases ? 'text-red-400 font-bold' : 'text-slate-200'}>{m.affidavit.criminal_cases}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Education</span><span className="text-slate-200">{m.affidavit.education}</span></div>
                      <a href={m.affidavit.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-cyan-400 hover:text-white mt-1">
                        Full affidavit on MyNeta <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  ) : <p className="text-xs text-slate-500">No matching 2024 affidavit found for this seat.</p>}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Questions by ministry ({m.questions_total.toLocaleString('en-IN')} since 2009)</h4>
                  {m.questions_by_ministry.length ? (
                    <ul className="text-xs space-y-1">
                      {m.questions_by_ministry.map((x) => (
                        <li key={x.ministry} className="flex justify-between gap-3">
                          <span className="text-slate-300 truncate">{x.ministry}</span>
                          <span className="text-slate-500">{x.count}</span>
                        </li>
                      ))}
                    </ul>
                  ) : <p className="text-xs text-slate-500">No questions found under this name.</p>}
                </div>
              </div>

              {m.recent_questions.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Recent questions</h4>
                  <div className="flex flex-col gap-1 max-h-64 overflow-y-auto pr-1">
                    {m.recent_questions.map((q) => (
                      <a key={q.id} href={q.official_url} target="_blank" rel="noopener noreferrer"
                        className="flex justify-between gap-3 text-xs p-1.5 rounded hover:bg-slate-900">
                        <span className="text-slate-200">{q.title} <span className="text-slate-500">· {q.ministry}</span></span>
                        <span className="text-slate-500 flex-shrink-0">{q.date}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {m.bills.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Private member bills</h4>
                  {m.bills.map((b) => (
                    <a key={b.official_url + b.title} href={b.official_url} target="_blank" rel="noopener noreferrer"
                      className="flex justify-between gap-3 text-xs p-1.5 rounded hover:bg-slate-900">
                      <span className="text-slate-200">{b.title}</span><span className="text-slate-500 flex-shrink-0">{b.status}</span>
                    </a>
                  ))}
                </div>
              )}

              <ul className="text-[10px] text-slate-500 list-disc pl-4 space-y-0.5">
                {m.notes.map((n) => <li key={n}>{n}</li>)}
                <li><a href={m.activity.source_url} className="hover:text-slate-300" target="_blank" rel="noopener noreferrer">Activity source</a></li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
