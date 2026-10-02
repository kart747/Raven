import { usePibReleases } from '../../lib/queries';

export default function PibTicker() {
  const { data, isLoading, isError } = usePibReleases();
  const releases = data?.data || [];

  return (
    <div className="glass-panel rounded-2xl p-4 shadow-lg border border-slate-900 overflow-hidden relative">
      <div className="flex items-center justify-between border-b border-slate-900/60 pb-2.5 mb-2.5">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
          </span>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">PIB Press Releases</h3>
        </div>
        <span className="text-[9px] text-slate-500 font-semibold uppercase">Source: Press Information Bureau RSS</span>
      </div>

      {isLoading ? (
        <div className="h-7 flex items-center justify-center text-xs text-slate-500">Loading feed...</div>
      ) : isError || releases.length === 0 ? (
        <div className="h-7 flex items-center justify-center text-xs text-slate-500">PIB feed unavailable.</div>
      ) : (
        <div className="relative flex items-center h-8 overflow-hidden bg-slate-950/40 rounded-lg border border-slate-900/60 px-3">
          <div className="animate-marquee whitespace-nowrap flex gap-12 text-xs">
            {releases.concat(releases).map((release, index) => (
              <span key={`${release.id}-${index}`} className="inline-flex items-center gap-2">
                <a href={release.source_citation?.source_url} target="_blank" rel="noopener noreferrer"
                  className="hover:text-cyan-400 transition-all font-semibold text-slate-300">
                  {release.title}
                </a>
                <span className="text-[10px] text-slate-500">({new Date(release.published_at).toLocaleString()})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
