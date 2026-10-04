import { useLive } from '../../lib/queries';
import { timeAgo } from '../../lib/time';

/** Scrolling strip of the latest headlines across all live sources. */
export default function LiveTicker({ onOpenLive }) {
  const { data, isLoading, isError } = useLive({ limit: 20 });
  const items = data?.data || [];

  return (
    <div className="glass-panel rounded-2xl p-4 shadow-lg border border-slate-900 overflow-hidden relative">
      <div className="flex items-center justify-between border-b border-slate-900/60 pb-2.5 mb-2.5">
        <button onClick={onOpenLive} className="flex items-center gap-2 group">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider group-hover:text-cyan-300">Live headlines</h3>
        </button>
        <button onClick={onOpenLive} className="text-[9px] text-slate-500 font-semibold uppercase hover:text-slate-300">
          Government, politics, courts &amp; more · open Live →
        </button>
      </div>
      {isLoading ? (
        <div className="h-7 flex items-center justify-center text-xs text-slate-500">Loading…</div>
      ) : isError || items.length === 0 ? (
        <div className="h-7 flex items-center justify-center text-xs text-slate-500">No live headlines yet.</div>
      ) : (
        <div className="relative flex items-center h-8 overflow-hidden bg-slate-950/40 rounded-lg border border-slate-900/60 px-3">
          <div className="animate-marquee whitespace-nowrap flex gap-12 text-xs">
            {items.concat(items).map((i, idx) => (
              <span key={`${i.id}-${idx}`} className="inline-flex items-center gap-2">
                <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[9px] text-slate-400 font-bold">{i.source}</span>
                <a href={i.url} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 font-semibold text-slate-300">{i.title}</a>
                <span className="text-[10px] text-slate-500">{timeAgo(i.published_at)}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
