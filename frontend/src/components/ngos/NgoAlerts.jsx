import { ShieldAlert, TrendingUp } from 'lucide-react';
import { fiscalYear, formatInr } from '../../lib/format';
import { useNgos } from '../../lib/queries';
import { STATUS_COLORS } from './constants';

/** Year-over-year spikes and verified suspensions/cancellations (queried across the whole registry). */
export default function NgoAlerts({ stats, onOpenNgo }) {
  const suspended = useNgos({ status: 'Suspended', limit: 50 });
  const cancelled = useNgos({ status: 'Cancelled', limit: 50 });
  const flagged = [...(suspended.data?.data || []), ...(cancelled.data?.data || [])];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="glass-panel rounded-2xl p-5 shadow-lg flex flex-col gap-4">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-cyan-400" /> Year-over-year increases
          </h3>
          <p className="text-[10px] text-slate-400">Largest rupee increases where a year at least doubled (base ≥ ₹1 Lakh, rise ≥ ₹25 Lakh); top 100. An increase is not by itself a sign of wrongdoing.</p>
        </div>
        <div className="divide-y divide-slate-900 overflow-y-auto max-h-[260px] pr-1">
          {stats.flagged_spikes.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">No increases matching the threshold.</div>
          ) : stats.flagged_spikes.map((s) => (
            <div key={`${s.ngo_id}-${s.year}`} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div className="space-y-0.5">
                <strong className="text-white block hover:text-cyan-400 cursor-pointer" onClick={() => onOpenNgo(s.ngo_id)}>{s.ngo_name}</strong>
                <span className="text-[9px] text-slate-500 block">FCRA No: {s.fcra_registration_number} | State: {s.state}</span>
              </div>
              <div className="text-right flex-shrink-0 flex items-center gap-3">
                <div>
                  <span className="text-[9px] text-slate-500 block">{fiscalYear(s.year - 1)} → {fiscalYear(s.year)}</span>
                  <span className="text-emerald-400 font-bold">{formatInr(s.previous_amount)} → {formatInr(s.current_amount)}</span>
                </div>
                <div className="px-2 py-1 rounded bg-emerald-950/60 border border-emerald-800/40 text-emerald-400 font-bold text-[10px]">
                  +{s.percentage_increase.toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-panel rounded-2xl p-5 shadow-lg flex flex-col gap-4">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-red-400" /> Verified registration actions
          </h3>
          <p className="text-[10px] text-slate-400">Only statuses loaded from official MHA lists are shown</p>
        </div>
        <div className="divide-y divide-slate-900 overflow-y-auto max-h-[260px] pr-1">
          {flagged.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">
              No verified suspensions or cancellations loaded. Registration status is not part of the FCRA returns data —
              import MHA's lists with <code className="text-slate-300">python -m app.cli ingest-fcra-status</code>.
            </div>
          ) : flagged.map((ngo) => (
            <div key={ngo.id} className="py-3 flex items-center justify-between gap-3 text-xs">
              <div className="space-y-0.5">
                <strong className="text-white block hover:text-cyan-400 cursor-pointer" onClick={() => onOpenNgo(ngo.id)}>{ngo.name}</strong>
                <span className="text-[9px] text-slate-500 block">FCRA No: {ngo.fcra_registration_number} | {ngo.state}</span>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${STATUS_COLORS[ngo.registration_status]}`}>
                {ngo.registration_status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
