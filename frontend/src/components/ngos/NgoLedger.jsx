import { useState } from 'react';
import { Download, ExternalLink, Globe, Search } from 'lucide-react';
import { apiUrl } from '../../api';
import { fiscalYear, formatInr } from '../../lib/format';
import { useNgoDonations } from '../../lib/queries';
import Pagination from '../ui/Pagination';
import Spinner from '../ui/Spinner';
import { FISCAL_YEARS, INPUT, RESET_BTN } from './constants';

const LIMIT = 10;

export default function NgoLedger({ onOpenNgo }) {
  const [search, setSearch] = useState('');
  const [year, setYear] = useState('');
  const [offset, setOffset] = useState(0);
  const { data, isLoading, isError } = useNgoDonations({ search, year, limit: LIMIT, offset });
  const rows = data?.data || [];

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-cyan-400" /> Annual Foreign Contribution Returns
          </h2>
          <p className="text-xs text-slate-400">Foreign contribution declared by each NGO per fiscal year</p>
        </div>
        <button onClick={() => window.open(apiUrl('/api/v1/ngo-donations', { export_csv: true, search, year }))}
          className="flex items-center gap-2 self-start lg:self-center px-4 py-2 bg-cyan-950/80 border border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/50 hover:text-white rounded-xl text-xs font-semibold transition-all">
          <Download className="w-3.5 h-3.5" /> Export CSV
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input type="text" placeholder="Search NGO name or registration..." value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }} className={`w-full pl-10 pr-4 ${INPUT}`} />
        </div>
        <select value={year} onChange={(e) => { setYear(e.target.value); setOffset(0); }} className={`${INPUT} appearance-none`}>
          <option value="">All Years</option>
          {FISCAL_YEARS.map((y) => <option key={y} value={y}>{fiscalYear(y)}</option>)}
        </select>
        <button onClick={() => { setSearch(''); setYear(''); setOffset(0); }} className={RESET_BTN}>Reset Filters</button>
      </div>

      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold tracking-wider text-slate-400">
              <th className="p-4">Recipient NGO</th>
              <th className="p-4 text-center">Fiscal Year</th>
              <th className="p-4 text-right">Amount (INR)</th>
              <th className="p-4">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900 text-sm">
            {isLoading ? (
              <tr><td colSpan="4" className="p-8"><Spinner label="Loading returns..." /></td></tr>
            ) : isError ? (
              <tr><td colSpan="4" className="p-8 text-center text-red-400 text-xs">Could not load returns.</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan="4" className="p-8 text-center text-slate-500">No returns match these filters.</td></tr>
            ) : rows.map((don) => (
              <tr key={don.id} className="hover:bg-slate-900/20 transition-all">
                <td className="p-4">
                  <span className="font-bold text-white text-xs tracking-wide block hover:text-cyan-400 cursor-pointer" onClick={() => onOpenNgo(don.ngo_id)}>
                    {don.ngo_name}
                  </span>
                  <span className="text-[9px] text-slate-500">FCRA: {don.fcra_registration_number}</span>
                </td>
                <td className="p-4 text-center text-xs text-slate-400">{fiscalYear(don.year)}</td>
                <td className="p-4 text-right text-emerald-400 font-bold tracking-tight">{formatInr(don.amount)}</td>
                <td className="p-4">
                  <a href={don.source_url} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-950 hover:bg-slate-900 border border-slate-800 text-[10px] text-cyan-400 hover:text-white transition-all font-semibold">
                    {don.source_name} <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination offset={offset} limit={LIMIT} total={data?.total || 0} noun="returns" onChange={setOffset} />
    </div>
  );
}
