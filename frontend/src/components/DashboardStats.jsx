import React from 'react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, Legend
} from 'recharts';
import { Landmark, Users, ArrowUpRight, DollarSign, Activity } from 'lucide-react';

const PARTY_COLORS = {
  BJP: '#f97316',   // Orange
  INC: '#0ea5e9',   // Sky Blue
  AITC: '#10b981',  // Emerald Green
  BRS: '#ec4899',   // Pink
  DMK: '#ef4444',   // Red
  YSRCP: '#14b8a6', // Teal
  TDP: '#eab308',   // Yellow
  SHS: '#a855f7',   // Purple
  AAP: '#6366f1',   // Indigo
  NCP: '#f43f5e',   // Rose
};

const DEFAULT_COLORS = ['#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#10b981'];

export default function DashboardStats({ stats, loading, onOpenDonor }) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-panel h-28 rounded-2xl p-6 animate-pulse flex items-center justify-between">
            <div className="space-y-2">
              <div className="h-3 w-20 bg-slate-800 rounded"></div>
              <div className="h-6 w-32 bg-slate-800 rounded"></div>
            </div>
            <div className="w-10 h-10 bg-slate-800 rounded-xl"></div>
          </div>
        ))}
      </div>
    );
  }

  // Format currency in Indian Style (Crore)
  const formatCrore = (val) => {
    if (val === undefined || val === null) return '₹0 Cr';
    return `₹${(val / 10000000).toFixed(2)} Cr`;
  };

  // Prepare Party data for Pie Chart
  const partyData = stats.party_shares.map(item => ({
    name: item.party_id,
    value: item.amount,
    fullName: item.party_name,
    percentage: item.percentage
  }));

  // Prepare Sector data for Bar Chart
  const sectorData = stats.sector_shares.filter(item => item.sector !== 'Unknown').map(item => ({
    name: item.sector,
    amount: item.amount,
    crores: parseFloat((item.amount / 10000000).toFixed(2)),
    percentage: item.percentage
  })).slice(0, 8); // Top 8 sectors

  // Prepare Yearly Trend
  const yearlyData = stats.yearly_trends.map(item => ({
    year: `FY${item.year}-${String((item.year + 1) % 100).padStart(2, '0')}`,
    amount: parseFloat((item.total_amount / 10000000).toFixed(2))
  }));

  return (
    <div className="flex flex-col gap-6">
      {/* 4 Core Summary Counters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Funding */}
        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full filter blur-xl transition-all group-hover:bg-cyan-500/10"></div>
          <div>
            <span className="text-xs text-slate-400 font-medium">Electoral Bonds Encashed</span>
            <h3 className="text-2xl font-black text-white mt-1 tracking-tight">{formatCrore(stats.total_funding)}</h3>
            <span className="text-[10px] text-slate-500 block mt-1">Apr 2019 – Feb 2024 (SBI disclosure)</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/20 flex items-center justify-center text-cyan-400">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>

        {/* Total Donations Count */}
        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full filter blur-xl transition-all group-hover:bg-indigo-500/10"></div>
          <div>
            <span className="text-xs text-slate-400 font-medium">Bonds Encashed</span>
            <h3 className="text-2xl font-black text-white mt-1 tracking-tight">{stats.total_donations_count}</h3>
            <span className="text-[10px] text-slate-500 block mt-1">Individual bonds</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-800/20 flex items-center justify-center text-indigo-400">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Corporate Donors */}
        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full filter blur-xl transition-all group-hover:bg-emerald-500/10"></div>
          <div>
            <span className="text-xs text-slate-400 font-medium">Purchasers</span>
            <h3 className="text-2xl font-black text-white mt-1 tracking-tight">{stats.total_donors_count}</h3>
            <span className="text-[10px] text-slate-500 block mt-1">Companies & individuals (incl. undisclosed)</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-800/20 flex items-center justify-center text-emerald-400">
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* MP/MLA Affidavits */}
        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full filter blur-xl transition-all group-hover:bg-amber-500/10"></div>
          <div>
            <span className="text-xs text-slate-400 font-medium">Candidate Affidavits</span>
            <h3 className="text-2xl font-black text-white mt-1 tracking-tight">{stats.total_candidates_count}</h3>
            <span className="text-[10px] text-slate-500 block mt-1">Lok Sabha 2024 (MyNeta)</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-950/60 border border-amber-800/20 flex items-center justify-center text-amber-400">
            <Landmark className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Visual Charts Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Party Shares Pie Chart */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between shadow-lg lg:col-span-1 min-h-[350px]">
          <div>
            <h3 className="text-sm font-bold text-white">Party Funding Distribution</h3>
            <p className="text-[10px] text-slate-400">Recipient shares by overall encashed amount</p>
          </div>
          
          <div className="w-full h-52 relative mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={partyData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {partyData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={PARTY_COLORS[entry.name] || DEFAULT_COLORS[index % DEFAULT_COLORS.length]} 
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="glass-panel border-slate-800 rounded-xl p-2.5 shadow-xl text-xs">
                          <div className="font-bold text-white mb-0.5">{data.fullName}</div>
                          <div className="flex items-center justify-between gap-4">
                            <span className="text-slate-400">Amount:</span>
                            <span className="text-emerald-400 font-bold">{formatCrore(data.value)}</span>
                          </div>
                          <div className="flex items-center justify-between gap-4 mt-0.5">
                            <span className="text-slate-400">Share:</span>
                            <span className="text-cyan-400 font-bold">{data.percentage.toFixed(1)}%</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none">
              <span className="text-[10px] text-slate-400">Total Encashed</span>
              <span className="text-sm font-black text-white">{formatCrore(stats.total_funding).split('.')[0]} Cr</span>
            </div>
          </div>

          {/* Inline Legend */}
          <div className="grid grid-cols-3 gap-x-2 gap-y-1.5 mt-4 text-[9px] text-slate-400 border-t border-slate-900 pt-3">
            {partyData.slice(0, 6).map((item, idx) => (
              <div key={item.name} className="flex items-center gap-1.5 overflow-hidden text-ellipsis whitespace-nowrap">
                <span 
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: PARTY_COLORS[item.name] || DEFAULT_COLORS[idx % DEFAULT_COLORS.length] }}
                ></span>
                <span className="font-semibold text-slate-300">{item.name}</span>
                <span>{item.percentage.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Shares Bar Chart */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between shadow-lg lg:col-span-2 min-h-[350px]">
          <div>
            <h3 className="text-sm font-bold text-white">Top Contributing Sectors</h3>
            <p className="text-[10px] text-slate-400">Bond value by purchaser industry, where a sourced industry is on file (₹ Crores)</p>
          </div>

          {sectorData.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-center text-xs text-slate-500 px-8">
              No purchaser industries have been sourced yet. Add data/donor_industry.csv (donor_name, industry, source_url)
              and re-run the bond import to populate this chart.
            </div>
          ) : (
          <div className="w-full h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorData} layout="vertical" margin={{ left: 20, right: 10, top: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" horizontal={true} vertical={false} />
                <XAxis type="number" stroke="#475569" fontSize={9} tickLine={false} axisLine={false} unit=" Cr" />
                <YAxis dataKey="name" type="category" stroke="#475569" fontSize={9} width={130} tickLine={false} axisLine={false} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.015)' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="glass-panel border-slate-800 rounded-xl p-2.5 shadow-xl text-xs">
                          <div className="font-bold text-white mb-0.5">{data.name}</div>
                          <div className="flex items-center justify-between gap-4">
                            <span className="text-slate-400">Total Donated:</span>
                            <span className="text-emerald-400 font-bold">{formatCrore(data.amount)}</span>
                          </div>
                          <div className="flex items-center justify-between gap-4 mt-0.5">
                            <span className="text-slate-400">Industry Share:</span>
                            <span className="text-cyan-400 font-bold">{data.percentage.toFixed(1)}%</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="crores" fill="#06b6d4" radius={[0, 4, 4, 0]}>
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={`rgba(6, 182, 212, ${1 - index * 0.08})`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          )}
        </div>
      </div>

      {/* Annual Trend and Top Corporate Donors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Yearly Trend Chart */}
        <div className="glass-panel rounded-2xl p-5 shadow-lg lg:col-span-2 min-h-[300px] flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Annual Funding Trends</h3>
            <p className="text-[10px] text-slate-400">Electoral bonds encashed per fiscal year, April–March (₹ Crores)</p>
          </div>

          <div className="w-full h-52 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={yearlyData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" />
                <XAxis dataKey="year" stroke="#475569" fontSize={9} tickLine={false} />
                <YAxis stroke="#475569" fontSize={9} tickLine={false} unit=" Cr" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="glass-panel border-slate-800 rounded-xl p-2 shadow-xl text-xs">
                          <span className="text-slate-400 block mb-0.5">FY {payload[0].payload.year}</span>
                          <span className="text-cyan-400 font-bold">₹{payload[0].value} Cr</span>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="amount" 
                  stroke="#06b6d4" 
                  strokeWidth={2}
                  dot={{ fill: '#06b6d4', stroke: '#0284c7', strokeWidth: 1, r: 3 }}
                  activeDot={{ r: 5 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top 5 Corporate Donors list */}
        <div className="glass-panel rounded-2xl p-5 shadow-lg lg:col-span-1 min-h-[300px] flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Top 5 Bond Purchasers</h3>
            <p className="text-[10px] text-slate-400">By value of encashed bonds. Click a name for its profile.</p>
          </div>

          <div className="flex-1 flex flex-col justify-center divide-y divide-slate-900 mt-4">
            {stats.top_donors.filter(d => d.name !== 'UNKNOWN DONOR').slice(0, 5).map((donor, index) => (
              <div key={donor.id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 overflow-hidden mr-2">
                  <span className="w-5 h-5 flex items-center justify-center bg-slate-900 border border-slate-800 text-[10px] text-slate-400 font-bold rounded-md">
                    {index + 1}
                  </span>
                  <div className="overflow-hidden">
                    <button onClick={() => onOpenDonor?.(donor.id)} title={donor.name}
                      className="font-bold text-white hover:text-cyan-400 text-left block w-full overflow-hidden text-ellipsis whitespace-nowrap leading-tight">
                      {donor.name}
                    </button>
                    {donor.industry && donor.industry !== 'Unknown' && <span className="text-[9px] text-slate-500 block mt-0.5">{donor.industry}</span>}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="font-bold text-emerald-400 block">{formatCrore(donor.total_donated)}</span>
                  <span className="text-[9px] text-slate-500">{donor.donation_count} bonds</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
