import { useState } from 'react';
import { ResponsiveContainer, Sankey, Tooltip } from 'recharts';
import { formatCrore } from '../../lib/format';
import { useBondFlows } from '../../lib/queries';
import Spinner from '../ui/Spinner';
import EmbedButton from '../ui/EmbedButton';

const truncate = (s, n) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);

function FlowNode({ x, y, width, height, payload, onOpen }) {
  const purchaser = payload.kind === 'purchaser';
  return (
    <g style={{ cursor: 'pointer' }} onClick={() => onOpen(payload)}>
      <rect x={x} y={y} width={width} height={Math.max(height, 1)} rx="2"
        fill={purchaser ? '#22d3ee' : '#f59e0b'} fillOpacity="0.85" />
      <text x={purchaser ? x - 6 : x + width + 6} y={y + height / 2} dy="3"
        textAnchor={purchaser ? 'end' : 'start'} fontSize="10" fill="#cbd5e1">
        {truncate(payload.name, purchaser ? 34 : 12)}
      </text>
    </g>
  );
}

/** Where the money from the largest identified bond purchasers went. */
export default function BondFlows({ onOpenDonor, onOpenParty }) {
  const [top, setTop] = useState(15);
  const { data, isLoading, isError } = useBondFlows(top);
  const open = (node) => (node.kind === 'purchaser' ? onOpenDonor(node.ref) : onOpenParty(node.ref));

  return (
    <div className="glass-panel rounded-2xl p-5 shadow-lg border border-slate-900">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-white">Follow the money: largest purchasers → parties</h3>
          <p className="text-[10px] text-slate-400">
            Electoral bonds matched by bond number.
            {data && ` These ${top} purchasers account for ${formatCrore(data.covered_amount, 0)} (${data.share_of_all_bonds}% of all bonds).`}
            {' '}Click a name to open its profile.
          </p>
        </div>
        <div className="flex gap-1 items-center">
          <EmbedButton id="flows" height={620} />
          {[10, 15, 25].map((n) => (
            <button key={n} onClick={() => setTop(n)}
              className={`px-2.5 py-1 rounded-md text-[11px] border ${top === n ? 'border-cyan-700 text-cyan-300 bg-cyan-950/50' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
              Top {n}
            </button>
          ))}
        </div>
      </div>
      <div className="w-full mt-4" style={{ height: 160 + top * 26 }}>
        {isLoading ? <div className="h-full flex items-center justify-center"><Spinner label="Tracing flows..." /></div>
          : isError || !data?.links.length ? <div className="h-full flex items-center justify-center text-xs text-slate-500">No bond data loaded.</div>
            : (
              <ResponsiveContainer width="100%" height="100%">
                <Sankey data={data} nodePadding={8} nodeWidth={10} iterations={64}
                  margin={{ left: 230, right: 110, top: 8, bottom: 8 }}
                  node={<FlowNode onOpen={open} />}
                  link={{ stroke: 'rgba(34, 211, 238, 0.35)' }}>
                  <Tooltip content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0].payload;
                    const label = d.source && d.target ? `${d.source.name} → ${d.target.name}` : d.name;
                    return (
                      <div className="glass-panel border-slate-800 rounded-xl p-2.5 text-xs">
                        <div className="font-bold text-white">{label}</div>
                        <div className="text-emerald-400 font-bold">{formatCrore(d.value)}</div>
                      </div>
                    );
                  }} />
                </Sankey>
              </ResponsiveContainer>
            )}
      </div>
    </div>
  );
}
