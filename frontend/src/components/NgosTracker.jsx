import { Calendar, Globe } from 'lucide-react';
import { useNgoStats } from '../lib/queries';
import NgoSummaryCards from './ngos/NgoSummaryCards';
import NgoCharts from './ngos/NgoCharts';
import NgoAlerts from './ngos/NgoAlerts';
import NgoDirectory from './ngos/NgoDirectory';
import NgoLedger from './ngos/NgoLedger';

export default function NgosTracker({ onOpenNgo }) {
  const { data: stats, isError } = useNgoStats();

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-900 pb-5">
        <div>
          <h1 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
            <Globe className="w-5 h-5 text-cyan-400" /> NGO Foreign Funding
          </h1>
          <p className="text-xs text-slate-400 mt-1">Foreign contributions declared in FCRA annual returns, by NGO and year.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-950/40 border border-amber-800/30 text-amber-400 text-xs font-semibold self-start md:self-center">
          <Calendar className="w-4 h-4" /> FCRA annual returns, FY2016-17 to FY2020-21
        </div>
      </div>

      {isError && <div className="text-xs text-red-400">Could not load NGO statistics. Is the API running?</div>}
      <NgoSummaryCards stats={stats} />
      {stats && <NgoCharts stats={stats} />}
      {stats && <NgoAlerts stats={stats} onOpenNgo={onOpenNgo} />}
      <NgoDirectory onOpenNgo={onOpenNgo} />
      <NgoLedger onOpenNgo={onOpenNgo} />
    </div>
  );
}
