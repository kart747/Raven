import { ArrowUpRight } from 'lucide-react';
import { useInsights } from '../../lib/queries';
import { useT } from '../../lib/i18n';

const KIND_COLOURS = {
  bonds: 'border-l-cyan-500',
  candidates: 'border-l-rose-500',
  ngos: 'border-l-emerald-500',
  parliament: 'border-l-amber-500',
};

/** Factual statements computed live from the data; each opens the record or view behind it. */
export default function KeyFacts({ onNavigate }) {
  const t = useT();
  const { data: facts = [], isLoading } = useInsights();
  if (isLoading || facts.length === 0) return null;

  const open = (link) => {
    if (link.url) window.open(link.url, '_blank', 'noopener');
    else onNavigate(link);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">{t('facts.title')}</h2>
        <span className="text-[10px] text-slate-500">{t('facts.note')}</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {facts.map((f) => (
          <button key={f.id} onClick={() => open(f.link)}
            className={`group text-left glass-panel rounded-xl p-4 border border-slate-900 border-l-4 ${KIND_COLOURS[f.kind] || ''} hover:border-slate-700 transition-all`}>
            <p className="text-[13px] leading-snug text-slate-200">{f.text}</p>
            <span className="mt-2 inline-flex items-center gap-1 text-[10px] text-slate-500 group-hover:text-cyan-400">
              {t('facts.view')} <ArrowUpRight className="w-3 h-3" />
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
