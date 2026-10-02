import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Sankey, Tooltip, XAxis, YAxis } from 'recharts';
import { Globe, Landmark } from 'lucide-react';
import { formatInr } from '../../lib/format';
import { useNgoDonations } from '../../lib/queries';
import { FALLBACK_COLORS, SECTOR_COLORS } from './constants';
import Spinner from '../ui/Spinner';

const croreTick = (v) => (v / 1e7).toFixed(0);

function ChartTooltip({ active, payload, render }) {
  if (!active || !payload?.length) return null;
  return <div className="glass-panel border-slate-800 rounded-xl p-2.5 shadow-xl text-xs">{render(payload[0].payload)}</div>;
}

function SankeyNode({ x, y, width, height, payload }) {
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill="#06b6d4" fillOpacity="0.8" stroke="#0891b2" rx="2" />
      <text x={x < 200 ? x + width + 6 : x - 6} y={y + height / 2} dy="3" textAnchor={x < 200 ? 'start' : 'end'}
        fontSize="9" fontWeight="bold" fill="#cbd5e1">{payload.name}</text>
    </g>
  );
}

/** Sector -> NGO flows from the largest 250 annual returns (top 6 NGOs per sector). */
function buildSankey(rows) {
  const nodes = [];
  const index = new Map();
  const node = (name) => {
    if (!index.has(name)) { index.set(name, nodes.length); nodes.push({ name }); }
    return index.get(name);
  };
  const flow = {};
  rows.forEach((d) => {
    const sector = d.ngo_sector || 'Other';
    flow[sector] = flow[sector] || {};
    flow[sector][d.ngo_name] = (flow[sector][d.ngo_name] || 0) + (d.amount || 0);
  });
  const links = [];
  Object.entries(flow).forEach(([sector, ngos]) => {
    Object.entries(ngos).sort((a, b) => b[1] - a[1]).slice(0, 3).forEach(([ngo, amount]) => {
      if (amount > 100000) links.push({ source: node(sector), target: node(ngo), value: amount });
    });
  });
  return { nodes, links };
}

export default function NgoCharts({ stats }) {
  const flows = useNgoDonations({ limit: 250 });
  const sankey = flows.data ? buildSankey(flows.data.data) : null;

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel rounded-2xl p-5 shadow-lg min-h-[350px] border border-slate-900">
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            <Landmark className="w-4 h-4 text-cyan-400" /> Top NGOs by Foreign Receipts
          </h3>
          <p className="text-[10px] text-slate-400">Largest recipients across all years (₹ Crore)</p>
          <div className="w-full h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.top_ngos} layout="vertical" margin={{ left: 15, right: 10, top: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" vertical={false} />
                <XAxis type="number" stroke="#475569" fontSize={9} tickLine={false} axisLine={false} unit=" Cr" tickFormatter={croreTick} />
                <YAxis dataKey="ngo_name" type="category" stroke="#475569" fontSize={9} width={130} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.015)' }} content={<ChartTooltip render={(d) => (
                  <>
                    <div className="font-bold text-white mb-0.5">{d.ngo_name}</div>
                    <div className="text-[9px] text-slate-500 mb-1.5">FCRA: {d.fcra_registration_number} | {d.state}</div>
                    <div>Total: <span className="text-emerald-400 font-bold">{formatInr(d.total_funding)}</span></div>
                    <div>Sector (inferred): <span className="text-cyan-400">{d.sector}</span></div>
                  </>
                )} />} />
                <Bar dataKey="total_funding" fill="#06b6d4" radius={[0, 4, 4, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 shadow-lg min-h-[350px]">
          <h3 className="text-sm font-bold text-white">Foreign Funding by Sector (inferred from name)</h3>
          <p className="text-[10px] text-slate-400">₹ Crore across all years</p>
          <div className="w-full h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.sector_shares} layout="vertical" margin={{ left: 15, right: 10, top: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" vertical={false} />
                <XAxis type="number" stroke="#475569" fontSize={9} tickLine={false} axisLine={false} unit=" Cr" tickFormatter={croreTick} />
                <YAxis dataKey="sector" type="category" stroke="#475569" fontSize={9} width={130} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.015)' }} content={<ChartTooltip render={(d) => (
                  <>
                    <div className="font-bold text-white mb-0.5">{d.sector}</div>
                    <div>Total: <span className="text-emerald-400 font-bold">{formatInr(d.amount)}</span></div>
                    <div>Share: <span className="text-cyan-400 font-bold">{d.percentage.toFixed(1)}%</span></div>
                  </>
                )} />} />
                <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                  {stats.sector_shares.map((entry, i) => (
                    <Cell key={entry.sector} fill={SECTOR_COLORS[entry.sector] || FALLBACK_COLORS[i % FALLBACK_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-2xl p-5 shadow-lg min-h-[380px] border border-slate-900">
        <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
          <Globe className="w-4 h-4 text-cyan-400" /> Sector ➔ NGO flows
        </h3>
        <p className="text-[10px] text-slate-400">Largest 250 annual returns, top 3 recipients per sector</p>
        <div className="w-full h-[420px] mt-4 relative bg-slate-950/20 rounded-xl p-2 border border-slate-900/60">
          {flows.isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center"><Spinner label="Building flows..." /></div>
          ) : flows.isError || !sankey?.links.length ? (
            <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-500">No flow data.</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <Sankey data={sankey} node={SankeyNode} nodePadding={14} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
                link={{ stroke: 'rgba(6, 182, 212, 0.15)' }}>
                <Tooltip content={<ChartTooltip render={(d) => (d.source !== undefined && d.target !== undefined ? (
                  <>
                    <div className="font-bold text-white mb-0.5">{d.source.name} ➔ {d.target.name}</div>
                    <div>Amount: <span className="text-emerald-400 font-bold">{formatInr(d.value)}</span></div>
                  </>
                ) : null)} />} />
              </Sankey>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </>
  );
}
