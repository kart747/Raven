import { Activity } from 'lucide-react';
import { useDataQuality } from '../lib/queries';
import Spinner from './ui/Spinner';

const when = (iso) => (iso ? new Date(iso).toLocaleString() : 'never');

function MetricValue({ metric }) {
  if (metric.value === null || metric.value === undefined) return <span className="text-slate-500">—</span>;
  const text = typeof metric.value === 'number' ? metric.value.toLocaleString('en-IN') : metric.value;
  return <span className="text-slate-100 font-semibold">{metric.unit === '₹ Cr' ? `₹${text} Cr` : `${text}${metric.unit || ''}`}</span>;
}

/** Live coverage and freshness for every dataset, from /api/v1/data-quality. */
export default function DataQualityPanel() {
  const { data, isLoading, isError } = useDataQuality();

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-900 flex flex-col gap-4">
      <div>
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" /> Data quality &amp; coverage
        </h2>
        <p className="text-[10px] text-slate-400">Computed live from the database. Gaps are shown, not filled.</p>
      </div>
      {isLoading ? <Spinner label="Checking datasets..." /> : isError ? (
        <div className="text-xs text-red-400">Could not load data-quality report.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.map((d) => (
            <div key={d.id} className={`rounded-xl border p-4 bg-slate-950/50 ${d.rows ? 'border-slate-800' : 'border-amber-800/50'}`}>
              <div className="flex justify-between items-baseline gap-2">
                <h3 className="text-xs font-bold text-white">{d.label}</h3>
                <span className={`text-xs font-black ${d.rows ? 'text-cyan-400' : 'text-amber-400'}`}>
                  {d.rows ? d.rows.toLocaleString('en-IN') : 'not loaded'}
                </span>
              </div>
              <div className="text-[10px] text-slate-500 mb-2">Last loaded: {when(d.last_loaded)}</div>
              <dl className="flex flex-col gap-1 text-[11px]">
                {d.metrics.map((m) => (
                  <div key={m.label} className="flex justify-between gap-3">
                    <dt className="text-slate-400">{m.label}</dt>
                    <dd className="text-right"><MetricValue metric={m} /></dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
