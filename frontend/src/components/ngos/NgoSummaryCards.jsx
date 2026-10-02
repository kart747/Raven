import { Building2, Globe, Landmark, ShieldAlert } from 'lucide-react';
import { formatInr } from '../../lib/format';

function Card({ label, value, note, icon: Icon, tone }) {
  return (
    <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden">
      <div>
        <span className="text-xs text-slate-400 font-medium">{label}</span>
        <h3 className={`text-2xl font-black mt-1 tracking-tight ${tone}`}>{value}</h3>
        <span className="text-[10px] text-slate-500 block mt-1">{note}</span>
      </div>
      <div className="w-10 h-10 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-center text-cyan-400">
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}

export default function NgoSummaryCards({ stats }) {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="glass-panel h-28 rounded-2xl animate-pulse" />)}
      </div>
    );
  }
  const unverified =
    stats.total_ngos_count - stats.active_ngos_count - stats.suspended_ngos_count - stats.cancelled_ngos_count;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card label="Total Foreign Funding" value={formatInr(stats.total_funding)} note="Declared foreign receipts" icon={Globe} tone="text-white" />
      <Card label="Status Unverified" value={unverified.toLocaleString('en-IN')} note="No verified registration status on file" icon={Building2} tone="text-slate-300" />
      <Card label="Suspended / Cancelled" value={`${stats.suspended_ngos_count} / ${stats.cancelled_ngos_count}`} note="Verified MHA records only" icon={ShieldAlert} tone="text-red-400" />
      <Card label="Annual Returns" value={stats.total_donations_count.toLocaleString('en-IN')} note="NGO × fiscal-year filings" icon={Landmark} tone="text-white" />
    </div>
  );
}
