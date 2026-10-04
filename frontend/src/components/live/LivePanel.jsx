import { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ExternalLink, Radio, Rss, Search } from 'lucide-react';
import { apiUrl } from '../../api';
import { useLive, useLiveSources, useLiveTrending } from '../../lib/queries';
import { itemTime, timeAgo } from '../../lib/time';
import Spinner from '../ui/Spinner';
import EmbedButton from '../ui/EmbedButton';
import MentionChips from './MentionChips';
import TopStories from './TopStories';

const CATEGORIES = [
  ['', 'All'], ['government', 'Government'], ['politics', 'Politics'], ['national', 'National'], ['states', 'States'],
  ['courts', 'Courts'], ['factcheck', 'Fact-checks'], ['languages', 'Indian languages'], ['global', 'Global (GDELT)'],
];
const LANGUAGES = [
  ['', 'All'], ['hi', 'हिन्दी'], ['mr', 'मराठी'], ['gu', 'ગુજરાતી'], ['pa', 'ਪੰਜਾਬੀ'], ['bn', 'বাংলা'],
  ['ta', 'தமிழ்'], ['te', 'తెలుగు'], ['kn', 'ಕನ್ನಡ'], ['ml', 'മലയാളം'],
];
const KIND_LABEL = { mp: 'Lok Sabha MPs', rs: 'Rajya Sabha members', party: 'Parties', purchaser: 'Bond purchasers', state: 'States' };

/** Headlines from public feeds as they arrive, linked to Raven's people, parties, companies and states. */
export default function LivePanel({ onOpenEntity, compact = false }) {
  const [category, setCategory] = useState('');
  const [language, setLanguage] = useState('');
  const [view, setView] = useState('stories');
  const [q, setQ] = useState('');
  const [query, setQuery] = useState('');
  const [fresh, setFresh] = useState([]);       // items pushed since load
  const [connected, setConnected] = useState(false);
  const { data, isLoading, isError } = useLive({ category, language, q: query, limit: 100 });
  const { data: trending } = useLiveTrending(24);
  const { data: sources = [] } = useLiveSources();
  const client = useQueryClient();

  const base = data?.data || [];
  const latestId = data?.latest_id || 0;

  // Server-sent events: headlines collected after the page loaded appear without reloading
  useEffect(() => {
    if (!latestId) return undefined;
    const es = new EventSource(apiUrl('/api/v1/live/stream', { after: latestId }));
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.addEventListener('item', (e) => {
      const item = JSON.parse(e.data);
      setFresh((prev) => (prev.some((p) => p.id === item.id) ? prev : [item, ...prev].slice(0, 200)));
      client.invalidateQueries({ queryKey: ['live-trending'] });
    });
    return () => es.close();
  }, [latestId, client]);

  useEffect(() => setFresh([]), [category, language, query]);
  useEffect(() => { const t = setTimeout(() => setQuery(q.trim()), 400); return () => clearTimeout(t); }, [q]);

  const items = useMemo(() => {
    const keep = (i) => (!category || i.category === category) && (!language || i.language === language)
      && (!query || query.toLowerCase().split(/\s+/).every((w) => i.title.toLowerCase().includes(w)));
    const seen = new Set();
    // Same order as the API: newest publication time first (a feed can deliver an older story late)
    return [...fresh.filter(keep), ...base].filter((i) => (seen.has(i.id) ? false : seen.add(i.id)))
      .sort((a, b) => (Date.parse(b.published_at) - Date.parse(a.published_at)) || b.id - a.id);
  }, [fresh, base, category, language, query]);
  const freshIds = new Set(fresh.map((i) => i.id));
  const healthy = sources.filter((s) => s.last_status === 'ok' || s.last_status === 'not-modified').length;

  return (
    <div className={`grid grid-cols-1 ${compact ? '' : 'lg:grid-cols-3'} gap-6`}>
      <div className={`${compact ? '' : 'lg:col-span-2'} glass-panel rounded-2xl p-5 flex flex-col gap-4 border border-slate-900`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                {connected && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />}
                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${connected ? 'bg-emerald-500' : 'bg-slate-600'}`} />
              </span>
              Live
              <span className="text-[11px] font-normal text-slate-400">
                {healthy} of {sources.length} sources up · {connected ? 'streaming' : 'refreshing every 5 min'}
              </span>
            </h2>
            <p className="text-[11px] text-slate-400 max-w-2xl">
              Headlines and links from publishers' own feeds and open APIs; read the story on the publisher's site. Tags are
              exact name matches in the headline and can include different people with the same name.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <a href={apiUrl('/api/v1/live/rss', { category, language, q: query })} target="_blank" rel="noopener noreferrer"
              title="This view as an RSS feed, for any feed reader"
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-800 text-[11px] text-slate-400 hover:text-white">
              <Rss className="w-3 h-3" /> RSS
            </a>
            <EmbedButton id="live" height={720} />
          </div>
        </div>

        <div className="flex gap-1">
          {[['stories', 'Top stories'], ['latest', 'Latest']].map(([id, label]) => (
            <button key={id} onClick={() => { setView(id); setLanguage(''); setCategory(''); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${view === id ? 'border-cyan-700 text-cyan-300 bg-cyan-950/50' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
              {label}
            </button>
          ))}
        </div>

        {view === 'stories' ? (
          <>
            <div className="flex flex-wrap gap-1 -mt-1">
              {[['', 'All languages'], ['en', 'English'], ...LANGUAGES.slice(1)].map(([id, label]) => (
                <button key={id || 'all'} onClick={() => setLanguage(id)} lang={id || undefined}
                  className={`px-2 py-0.5 rounded text-[11px] border ${language === id ? 'border-cyan-800 text-cyan-300' : 'border-transparent text-slate-500 hover:text-white'}`}>
                  {label}
                </button>
              ))}
            </div>
            <TopStories language={language} onOpenEntity={onOpenEntity} />
          </>
        ) : (
          <>
          <div className="flex flex-wrap gap-1 items-center">
            {CATEGORIES.map(([id, label]) => (
              <button key={id || 'all'} onClick={() => { setCategory(id); if (id !== 'languages') setLanguage(''); }}
                className={`px-2.5 py-1 rounded-md text-[11px] border ${category === id ? 'border-cyan-700 text-cyan-300 bg-cyan-950/50' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
                {label}
              </button>
            ))}
            <div className="relative ml-auto">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter headlines…"
                className="pl-8 pr-3 py-1.5 bg-slate-900/50 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50" />
            </div>
          </div>

          {category === 'languages' && (
            <div className="flex flex-wrap gap-1 -mt-2">
              {LANGUAGES.map(([id, label]) => (
                <button key={id || 'all'} onClick={() => setLanguage(id)} lang={id || undefined}
                  className={`px-2 py-0.5 rounded text-[11px] border ${language === id ? 'border-cyan-800 text-cyan-300' : 'border-transparent text-slate-500 hover:text-white'}`}>
                  {label}
                </button>
              ))}
            </div>
          )}

          <div className="flex flex-col divide-y divide-slate-900 max-h-[70vh] overflow-y-auto pr-1">
            {isLoading ? <div className="py-10"><Spinner label="Loading headlines…" /></div>
              : isError ? <div className="py-10 text-center text-xs text-red-400">Could not load the live feed.</div>
                : items.length === 0 ? (
                  <div className="py-10 text-center text-xs text-slate-500">
                    Nothing yet. Headlines arrive as sources are polled (or run <code className="text-slate-300">python -m app.cli live-poll</code>).
                  </div>
                ) : items.map((i) => (
                  <div key={i.id} className={`py-2.5 ${freshIds.has(i.id) ? 'bg-emerald-950/20 -mx-2 px-2 rounded' : ''}`}>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500">
                      <span className="text-slate-400 font-semibold">{i.source}</span>
                      <span>·</span>
                      <span title={itemTime(i).title}>{itemTime(i).text}</span>
                      {freshIds.has(i.id) && <span className="text-emerald-400 font-bold">NEW</span>}
                    </div>
                    <a href={i.url} target="_blank" rel="noopener noreferrer"
                      className="text-[13px] text-slate-100 hover:text-cyan-300 leading-snug inline-flex gap-1" lang={i.language}>
                      {i.title} <ExternalLink className="w-3 h-3 mt-1 flex-shrink-0 opacity-40" />
                    </a>
                    <MentionChips mentions={i.mentions} onOpen={onOpenEntity} />
                  </div>
                ))}
          </div>
          </>
        )}
      </div>

      {!compact && (
        <div className="flex flex-col gap-6">
          <div className="glass-panel rounded-2xl p-5 border border-slate-900">
            <h3 className="text-sm font-bold text-white">Named most in the last 24 hours</h3>
            <p className="text-[10px] text-slate-500 mb-3">
              {trending ? `${trending.headlines.toLocaleString('en-IN')} headlines. ` : ''}Being named is not an indication of anything else.
            </p>
            {trending && Object.entries(trending.trending).map(([kind, rows]) => rows.length > 0 && (
              <div key={kind} className="mb-3">
                <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">{KIND_LABEL[kind]}</div>
                {rows.map((r) => (
                  <button key={r.ref} onClick={() => onOpenEntity({ kind, ref: r.ref, label: r.label })}
                    className="w-full flex justify-between text-xs py-0.5 hover:text-cyan-300 text-slate-200">
                    <span className="truncate text-left">{r.label}</span>
                    <span className="text-slate-500 tabular-nums">{r.headlines}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>

          <div className="glass-panel rounded-2xl p-5 border border-slate-900">
            <h3 className="text-sm font-bold text-white flex items-center gap-2"><Radio className="w-4 h-4 text-cyan-400" /> Sources</h3>
            <p className="text-[10px] text-slate-500 mb-3">Polled politely: robots.txt checked, conditional requests, per-source intervals, back-off on errors.</p>
            <div className="flex flex-col gap-1 text-[11px] max-h-[460px] overflow-y-auto pr-1">
              {sources.map((s, n) => {
                const ok = s.last_status === 'ok' || s.last_status === 'not-modified';
                const heading = n === 0 || sources[n - 1].category !== s.category;
                return (
                  <div key={s.key}>
                  {heading && (
                    <div className="text-[10px] uppercase font-bold text-slate-500 mt-2 mb-0.5">
                      {(CATEGORIES.find(([id]) => id === s.category) || [, s.category])[1]}
                    </div>
                  )}
                  <div className="flex items-center justify-between gap-2" title={s.last_status || 'not polled yet'}>
                    <span className="flex items-center gap-1.5 min-w-0">
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${ok ? 'bg-emerald-500' : s.last_status ? 'bg-amber-500' : 'bg-slate-600'}`} />
                      <a href={s.homepage} target="_blank" rel="noopener noreferrer" className="truncate text-slate-300 hover:text-white">{s.name}</a>
                    </span>
                    <span className="text-slate-500 flex-shrink-0">{ok ? `${s.items_24h} new · ${s.last_fetch_at ? timeAgo(s.last_fetch_at) : ''}` : (s.last_status || '—')}</span>
                  </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
