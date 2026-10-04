import { ExternalLink } from 'lucide-react';
import { useLive } from '../../lib/queries';
import { timeAgo } from '../../lib/time';

/** Recent headlines naming this entity (exact name match), for profile windows. */
export default function InTheNews({ kind, refId, title = 'In the news' }) {
  const { data } = useLive({ kind, ref: String(refId), limit: 8 });
  const items = data?.data || [];
  return (
    <div>
      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{title} ({items.length})</h4>
      {items.length === 0 ? (
        <p className="text-xs text-slate-500">No recent headlines name this exactly.</p>
      ) : (
        <div className="flex flex-col gap-1">
          {items.map((i) => (
            <a key={i.id} href={i.url} target="_blank" rel="noopener noreferrer"
              className="flex justify-between gap-3 text-xs p-1.5 rounded hover:bg-slate-900">
              <span className="text-slate-200">{i.title} <span className="text-slate-500">· {i.source}</span></span>
              <span className="text-slate-500 flex-shrink-0 flex items-center gap-1">{timeAgo(i.published_at)} <ExternalLink className="w-3 h-3" /></span>
            </a>
          ))}
        </div>
      )}
      <p className="text-[10px] text-slate-500 mt-1">Headlines from public feeds that name this exactly; may include others with the same name.</p>
    </div>
  );
}
