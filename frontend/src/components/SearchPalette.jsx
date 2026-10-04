import { useEffect, useRef, useState } from 'react';
import { Award, Building2, ExternalLink, Flag, Landmark, MessageSquareText, Search, UserCheck, X } from 'lucide-react';
import { useSearch } from '../lib/queries';
import Spinner from './ui/Spinner';
import { useT } from '../lib/i18n';

const GROUPS = [
  { key: 'parties', label: 'Parties', icon: Flag },
  { key: 'purchasers', label: 'Bond purchasers', icon: Landmark },
  { key: 'candidates', label: 'Candidates & MLAs', icon: Award },
  { key: 'ngos', label: 'NGOs', icon: Building2 },
  { key: 'mps', label: 'Lok Sabha MPs', icon: UserCheck },
  { key: 'questions', label: 'Lok Sabha questions', icon: MessageSquareText },
];

function useDebounced(value, ms) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
}

function describe(group, item) {
  switch (group) {
    case 'parties': return { title: item.name, sub: item.id };
    case 'purchasers': return { title: item.name };
    case 'candidates': return { title: item.name, sub: `${item.constituency}, ${item.state} · ${item.election || ''}${item.is_winner ? ' · won' : ''}` };
    case 'ngos': return { title: item.name, sub: `${item.state} · FCRA ${item.fcra_registration_number}` };
    case 'mps': return { title: item.name, sub: `${item.constituency}, ${item.state} · ${item.party}` };
    case 'questions': return { title: item.title, sub: `${item.date} · ${item.representative}`, href: item.official_url };
    default: return { title: '' };
  }
}

/** Search across every dataset. Opens with the header button or the "/" key. */
export default function SearchPalette({ open, onClose, onOpenDonor, onOpenNgo, onOpenState, onOpenParty, onOpenMp, onOpenCandidate }) {
  const t = useT();
  const [q, setQ] = useState('');
  const input = useRef(null);
  const debounced = useDebounced(q, 250);
  const { data, isFetching, isError } = useSearch(debounced);

  useEffect(() => { if (open) setTimeout(() => input.current?.focus(), 0); }, [open]);
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  if (!open) return null;

  const choose = (group, item) => {
    if (group === 'parties') onOpenParty(item.id);
    else if (group === 'purchasers') onOpenDonor(item.id);
    else if (group === 'ngos') onOpenNgo(item.id);
    else if (group === 'mps') onOpenMp(item.id);
    else if (group === 'candidates') onOpenCandidate(item.id);
    else return; // candidates and questions are links to the source
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[10vh] bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-2xl rounded-2xl shadow-2xl border border-slate-800 overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-4 border-b border-slate-900">
          <Search className="w-4 h-4 text-slate-500" />
          <input ref={input} value={q} onChange={(e) => setQ(e.target.value)}
            placeholder={t('search.placeholder')}
            className="flex-1 py-4 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none" />
          {isFetching && <Spinner />}
          <button onClick={onClose} className="p-1 text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-2">
          {debounced.trim().length < 2 ? (
            <p className="p-6 text-center text-xs text-slate-500">{t('search.hint')}</p>
          ) : isError ? (
            <p className="p-6 text-center text-xs text-red-400">Search failed. Is the API running?</p>
          ) : data && GROUPS.every((g) => !data[g.key]?.total) ? (
            <p className="p-6 text-center text-xs text-slate-500">No matches for "{debounced}".</p>
          ) : data && GROUPS.map(({ key, label, icon: Icon }) => data[key]?.total ? (
            <div key={key} className="mb-2">
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 flex justify-between">
                <span className="flex items-center gap-1.5"><Icon className="w-3 h-3" /> {label}</span>
                <span>{data[key].total.toLocaleString('en-IN')}</span>
              </div>
              {data[key].items.map((item) => {
                const d = describe(key, item);
                const body = (
                  <>
                    <div className="min-w-0">
                      <div className="text-sm text-slate-100 truncate">{d.title}</div>
                      {d.sub && <div className="text-[11px] text-slate-500 truncate">{d.sub}</div>}
                    </div>
                    {d.href && <ExternalLink className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />}
                  </>
                );
                const cls = 'w-full text-left px-3 py-2 rounded-lg hover:bg-slate-900 flex items-center justify-between gap-3';
                return d.href ? (
                  <a key={item.id} href={d.href} target="_blank" rel="noopener noreferrer" className={cls}>{body}</a>
                ) : (
                  <button key={item.id} onClick={() => choose(key, item)} className={cls}>{body}</button>
                );
              })}
            </div>
          ) : null)}
        </div>
      </div>
    </div>
  );
}
