import { useState } from 'react';
import { Code2 } from 'lucide-react';

/** Copies an <iframe> snippet that shows just this widget (#embed=<id>), credited to Raven. */
export default function EmbedButton({ id, height = 520 }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    const src = `${window.location.origin}${window.location.pathname}#embed=${id}`;
    const code = `<iframe src="${src}" width="100%" height="${height}" style="border:0" loading="lazy" title="Raven: ${id}"></iframe>`;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      window.prompt('Copy the embed code:', code);
    }
  };
  return (
    <button onClick={copy} title="Copy embed code"
      className="inline-flex items-center gap-1 px-2 py-1 rounded-md border border-slate-800 text-[10px] text-slate-400 hover:text-white">
      <Code2 className="w-3 h-3" /> {copied ? 'Copied' : 'Embed'}
    </button>
  );
}
