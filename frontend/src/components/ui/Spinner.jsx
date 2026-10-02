export default function Spinner({ label }) {
  return (
    <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
      <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
      {label}
    </div>
  );
}
