const STYLE = {
  mp: 'border-rose-800/50 text-rose-300',
  rs: 'border-fuchsia-800/50 text-fuchsia-300',
  party: 'border-amber-800/50 text-amber-300',
  purchaser: 'border-cyan-800/50 text-cyan-300',
  state: 'border-slate-700 text-slate-300',
};

/** Raven entities named in a headline; each opens its profile. */
export default function MentionChips({ mentions, onOpen }) {
  if (!mentions?.length) return null;
  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {mentions.map((m) => (
        <button key={`${m.kind}-${m.ref}`} onClick={() => onOpen(m)}
          className={`px-1.5 py-0.5 rounded border text-[10px] hover:bg-slate-800 ${STYLE[m.kind]}`}>
          {m.label}
        </button>
      ))}
    </div>
  );
}
