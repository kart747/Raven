import { formatCrore } from '../../lib/format';
import { useRajyaSabha, useStateCandidates, useStateLegislative, useStateNgoSummary } from '../../lib/queries';
import { STATUS_COLORS, statusLabel } from '../ngos/constants';
import Spinner from '../ui/Spinner';

function Stat({ label, value, tone = 'text-white' }) {
  return (
    <div>
      <span className="text-[10px] text-slate-500 block uppercase">{label}</span>
      <strong className={`text-sm font-black ${tone}`}>{value}</strong>
    </div>
  );
}

const ROW = 'p-2 bg-slate-950/60 border border-slate-900 rounded-xl flex items-center justify-between text-xs';
const LIST = 'flex flex-col gap-2 max-h-[160px] overflow-y-auto pr-1';
const STATS = 'grid grid-cols-2 gap-3 bg-slate-950/40 border border-slate-900/60 rounded-xl p-3 text-xs';

function Loading({ label }) {
  return <div className="flex-1 flex items-center justify-center py-10"><Spinner label={label} /></div>;
}

function Failed() {
  return <div className="text-center text-xs text-red-400 py-8">Could not load this panel.</div>;
}

export function CandidatesPanel({ state, summary, house = 'Lok Sabha', noun = 'Candidates', onOpenCandidate }) {
  const { data, isLoading, isError } = useStateCandidates(state, house);
  const s = summary || { candidate_count: 0, total_assets: 0, total_cases: 0, candidates_with_cases: 0 };
  const rows = data?.data || [];

  return (
    <div className="flex flex-col gap-4 flex-1">
      <div className={STATS}>
        <Stat label={noun} value={s.candidate_count.toLocaleString('en-IN')} />
        <Stat label="Total declared assets" value={formatCrore(s.total_assets, 0)} tone="text-emerald-400" />
        <Stat label="With declared criminal cases" value={`${s.candidates_with_cases} (${s.candidate_count ? ((100 * s.candidates_with_cases) / s.candidate_count).toFixed(0) : 0}%)`} tone="text-red-400" />
        <Stat label="Cases declared (total)" value={s.total_cases.toLocaleString('en-IN')} tone="text-slate-300" />
      </div>
      <div className="flex-1">
        <h3 className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wider">Highest declared assets</h3>
        {isLoading ? <Loading label="Loading affidavits..." /> : isError ? <Failed /> : (
          <div className={LIST}>
            {rows.length === 0 ? (
              <div className="text-center text-xs text-slate-500 py-4">No {noun.toLowerCase()} imported for this state (source: MyNeta).</div>
            ) : rows.map((c) => (
              <button key={c.id} onClick={() => onOpenCandidate?.(c.id)} className={`${ROW} w-full text-left hover:border-slate-700 transition-all`}>
                <div>
                  <strong className="text-white block truncate max-w-[160px]">
                    {c.name}{c.is_winner && house === 'Lok Sabha' && <span className="ml-1 text-[8px] text-emerald-400">WON</span>}
                  </strong>
                  <span className="text-[9px] text-slate-500">{c.constituency} · {c.party_name}</span>
                </div>
                <div className="text-right">
                  <span className="text-emerald-400 font-bold block">{formatCrore(c.assets)}</span>
                  <span className="text-[9px] text-slate-500">{c.criminal_cases} cases declared</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function NgoPanel({ state }) {
  const { data: s, isLoading, isError } = useStateNgoSummary(state);
  if (isLoading) return <Loading label="Loading FCRA returns..." />;
  if (isError || !s) return <Failed />;
  const verified = ['Active', 'Suspended', 'Cancelled'].reduce((n, k) => n + (s.status_counts[k] || 0), 0);

  return (
    <div className="flex flex-col gap-4 flex-1">
      <div className={STATS}>
        <Stat label="NGOs" value={s.ngos_count.toLocaleString('en-IN')} />
        <Stat label="Foreign contributions" value={formatCrore(s.total_funding)} tone="text-emerald-400" />
        <Stat label="Annual returns" value={s.total_donations.toLocaleString('en-IN')} tone="text-cyan-400" />
        <Stat label="Registration status" tone="text-slate-300"
          value={verified === 0 ? 'Unverified' : `${s.status_counts.Suspended || 0} susp. / ${s.status_counts.Cancelled || 0} canc.`} />
      </div>
      <div className="flex-1">
        <h3 className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wider">Largest recipients</h3>
        <div className={LIST}>
          {s.top_ngos.length === 0 ? (
            <div className="text-center text-xs text-slate-500 py-4">No NGOs in this state.</div>
          ) : s.top_ngos.map((n) => (
            <div key={n.id} className={ROW}>
              <div>
                <strong className="text-white block truncate max-w-[160px]" title={n.name}>{n.name}</strong>
                <span className="text-[9px] text-slate-500">FCRA: {n.fcra_registration_number}</span>
              </div>
              <div className="text-right">
                <span className="text-emerald-400 font-bold block">{formatCrore(n.total_foreign_funding)}</span>
                <span className={`inline-block px-1.5 text-[8px] font-bold rounded border ${STATUS_COLORS[n.registration_status]}`}>
                  {statusLabel(n.registration_status)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const BILL_COLORS = {
  Passed: 'bg-emerald-950/60 border-emerald-800/40 text-emerald-400',
  Introduced: 'bg-cyan-950/60 border-cyan-800/40 text-cyan-400',
  Pending: 'bg-amber-950/60 border-amber-800/40 text-amber-400',
};

export function LegislativePanel({ state, onOpenMp, onOpenRs }) {
  const { data: s, isLoading, isError } = useStateLegislative(state);
  const { data: rs } = useRajyaSabha();
  const rsMembers = (rs?.data || []).filter((m) => m.state === state);
  if (isLoading) return <Loading label="Loading parliamentary activity..." />;
  if (isError || !s) return <Failed />;

  return (
    <div className="flex flex-col gap-4 flex-1">
      <div className={STATS}>
        <Stat label="Lok Sabha MPs" value={s.total_mps} />
        <Stat label="Rajya Sabha" value={rsMembers.length} />
        <Stat label="Private member bills" value={s.total_bills} tone="text-cyan-400" />
      </div>
      <div>
        <h3 className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wider">MPs</h3>
        <div className={LIST}>
          {s.mps.length === 0 ? <div className="text-center text-xs text-slate-500 py-4">No MPs for this state.</div> : s.mps.map((mp) => (
            <div key={mp.id} className={ROW}>
              <div>
                <button onClick={() => onOpenMp?.(mp.id)} className="text-white hover:text-cyan-400 font-bold block truncate max-w-[160px] text-left" title={mp.mp_name}>{mp.mp_name}</button>
                <span className="text-[9px] text-slate-500">{mp.constituency} | {mp.party_name}</span>
              </div>
              <div className="text-right">
                <span className="text-emerald-400 font-bold block">{mp.attendance_pct != null ? `${mp.attendance_pct.toFixed(1)}% attendance` : 'Attendance n/a'}</span>
                <span className="text-[9px] text-slate-500">{mp.debates_count} debates · {mp.questions_count} questions</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      {rsMembers.length > 0 && (
        <div>
          <h3 className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wider">Rajya Sabha members</h3>
          <div className={LIST}>
            {rsMembers.map((m) => (
              <div key={m.id} className={ROW}>
                <button onClick={() => onOpenRs?.(m.id)} className="text-white hover:text-cyan-400 font-bold truncate max-w-[200px] text-left" title={m.name}>
                  {m.name}{m.is_minister ? ' · Minister' : ''}
                </button>
                <span className="text-[9px] text-slate-500 flex-shrink-0">{m.party_id || m.party} · until {m.term_end?.slice(0, 4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div>
        <h3 className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wider">Private member bills</h3>
        <div className={LIST}>
          {s.bills.length === 0 ? <div className="text-center text-xs text-slate-500 py-4">No bills from this state's MPs.</div> : s.bills.map((bill) => (
            <a key={bill.id} href={bill.official_url} target="_blank" rel="noopener noreferrer" className={`${ROW} items-start gap-3 hover:border-slate-700`}>
              <div className="min-w-0">
                <strong className="text-white block truncate max-w-[220px]" title={bill.bill_title}>{bill.bill_title}</strong>
                <span className="text-[9px] text-slate-500 block mt-0.5">Introduced by {bill.introduced_by}</span>
              </div>
              <span className={`flex-shrink-0 px-1.5 py-0.5 text-[8px] font-bold rounded border ${BILL_COLORS[bill.current_status] || BILL_COLORS.Pending}`}>
                {bill.current_status}
              </span>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
