const BTN =
  'px-3.5 py-1.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 text-slate-300 hover:text-white ' +
  'disabled:opacity-30 disabled:hover:border-slate-800 disabled:hover:text-slate-300 transition-all';

export default function Pagination({ offset, limit, total, noun, onChange }) {
  return (
    <div className="flex items-center justify-between text-xs text-slate-400">
      <div>
        Showing <span className="font-bold text-white">{Math.min(total, offset + 1)}</span> to{' '}
        <span className="font-bold text-white">{Math.min(total, offset + limit)}</span> of{' '}
        <span className="font-bold text-white">{total.toLocaleString('en-IN')}</span> {noun}
      </div>
      <div className="flex gap-2">
        <button onClick={() => onChange(offset - limit)} disabled={offset === 0} className={BTN}>Previous</button>
        <button onClick={() => onChange(offset + limit)} disabled={offset + limit >= total} className={BTN}>Next</button>
      </div>
    </div>
  );
}
