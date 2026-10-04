import { useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { useLiveStories } from '../../lib/queries';
import { itemTime, timeAgo } from '../../lib/time';
import Spinner from '../ui/Spinner';
import MentionChips from './MentionChips';

const WINDOWS = [[6, '6 h'], [12, '12 h'], [24, '24 h']];

/** Headlines grouped into stories, ranked by how many different publishers carry each one. */
export default function TopStories({ language, onOpenEntity }) {
  const [hours, setHours] = useState(12);
  const [open, setOpen] = useState({});
  const { data, isLoading, isError } = useLiveStories({ hours, language, limit: 30 });
  const stories = data?.stories || [];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] text-slate-500 max-w-xl">
          Stories carried by two or more publishers. {data?.note}
        </p>
        <div className="flex gap-1 flex-shrink-0">
          {WINDOWS.map(([h, label]) => (
            <button key={h} onClick={() => setHours(h)}
              className={`px-2 py-0.5 rounded text-[11px] border ${hours === h ? 'border-cyan-800 text-cyan-300' : 'border-transparent text-slate-500 hover:text-white'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col divide-y divide-slate-900 max-h-[70vh] overflow-y-auto pr-1">
        {isLoading ? <div className="py-10"><Spinner label="Grouping headlines…" /></div>
          : isError ? <div className="py-10 text-center text-xs text-red-400">Could not load stories.</div>
            : stories.length === 0 ? (
              <div className="py-10 text-center text-xs text-slate-500">No story is carried by two or more publishers in this window yet.</div>
            ) : stories.map((s) => {
              const others = s.items.filter((i) => i.id !== s.lead.id);
              const expanded = open[s.lead.id];
              return (
                <div key={s.lead.id} className="py-3">
                  <div className="flex items-center gap-2 text-[10px] text-slate-500">
                    <span className="px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-900 text-cyan-300 font-bold">
                      {s.outlets} outlets
                    </span>
                    <span>{s.headlines} headlines · latest {timeAgo(s.latest)} · first {timeAgo(s.first_seen)}</span>
                  </div>
                  <a href={s.lead.url} target="_blank" rel="noopener noreferrer" lang={s.lead.language}
                    className="mt-1 text-sm font-semibold text-slate-100 hover:text-cyan-300 leading-snug inline-flex gap-1">
                    {s.lead.title} <ExternalLink className="w-3 h-3 mt-1 flex-shrink-0 opacity-40" />
                  </a>
                  <div className="text-[10px] text-slate-500">{s.lead.source}</div>
                  <MentionChips mentions={s.mentions} onOpen={onOpenEntity} />
                  {others.length > 0 && (
                    <div className="mt-1.5 pl-3 border-l border-slate-800 flex flex-col gap-0.5">
                      {(expanded ? others : others.slice(0, 3)).map((i) => (
                        <a key={i.id} href={i.url} target="_blank" rel="noopener noreferrer" lang={i.language}
                          className="text-[11px] text-slate-400 hover:text-slate-100 truncate">
                          <span className="text-slate-500">{i.source}:</span> {i.title}
                          <span className="text-slate-600" title={itemTime(i).title}> · {itemTime(i).text}</span>
                        </a>
                      ))}
                      {others.length > 3 && (
                        <button onClick={() => setOpen({ ...open, [s.lead.id]: !expanded })}
                          className="text-left text-[10px] text-cyan-500 hover:text-cyan-300">
                          {expanded ? 'Show fewer' : `${others.length - 3} more`}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
      </div>
    </div>
  );
}
