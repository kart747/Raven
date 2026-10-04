import { ExternalLink, Rss } from 'lucide-react';
import { apiUrl } from '../../api';
import { useLive } from '../../lib/queries';
import { itemTime } from '../../lib/time';

/** Recent headlines naming this entity (exact name match), for profile windows. */
export default function InTheNews({ kind, refId, title = 'In the news' }) {
  const { data } = useLive({ kind, ref: String(refId), limit: 8 });
  const items = data?.data || [];
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">{title} ({items.length})</h4>
        <a href={apiUrl('/api/v1/live/rss', { kind, ref: refId })} target="_blank" rel="noopener noreferrer"
          title="Follow new headlines that name this in any feed reader"
          className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-cyan-300">
          <Rss className="w-3 h-3" /> Follow (RSS)
        </a>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-slate-500">No recent headlines name this exactly.</p>
      ) : (
        <div className="flex flex-col gap-1">
          {items.map((i) => (
            <a key={i.id} href={i.url} target="_blank" rel="noopener noreferrer"
              className="flex justify-between gap-3 text-xs p-1.5 rounded hover:bg-slate-900">
              <span className="text-slate-200" lang={i.language}>{i.title} <span className="text-slate-500">· {i.source}</span></span>
              <span className="text-slate-500 flex-shrink-0 flex items-center gap-1" title={itemTime(i).title}>
                {itemTime(i).text} <ExternalLink className="w-3 h-3" />
              </span>
            </a>
          ))}
        </div>
      )}
      <p className="text-[10px] text-slate-500 mt-1">Headlines from public feeds that name this exactly; may include others with the same name.</p>
    </div>
  );
}
