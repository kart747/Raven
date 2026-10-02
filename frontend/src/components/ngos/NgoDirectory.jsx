import { useState } from 'react';
import { Building2, Search } from 'lucide-react';
import { formatInr } from '../../lib/format';
import { useNgos } from '../../lib/queries';
import Pagination from '../ui/Pagination';
import Spinner from '../ui/Spinner';
import { INPUT, RESET_BTN, SECTOR_COLORS, STATUS_COLORS, statusLabel } from './constants';

const LIMIT = 10;

export default function NgoDirectory({ onOpenNgo }) {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [sector, setSector] = useState('');
  const [offset, setOffset] = useState(0);
  const { data, isLoading, isError } = useNgos({ search, status, sector, limit: LIMIT, offset });
  const rows = data?.data || [];
  const update = (setter) => (e) => { setter(e.target.value); setOffset(0); };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
      <div>
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Building2 className="w-5 h-5 text-cyan-400" /> NGO Directory
        </h2>
        <p className="text-xs text-slate-400">All NGOs in the FCRA returns data with their total foreign contributions</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input type="text" placeholder="Search NGO name or FCRA No..." value={search} onChange={update(setSearch)} className={`w-full pl-10 pr-4 ${INPUT}`} />
        </div>
        <select value={status} onChange={update(setStatus)} className={`${INPUT} appearance-none`}>
          <option value="">All Statuses</option>
          <option value="Active">Active</option>
          <option value="Suspended">Suspended</option>
          <option value="Cancelled">Cancelled</option>
          <option value="Unknown">Unverified</option>
        </select>
        <select value={sector} onChange={update(setSector)} className={`${INPUT} appearance-none`}>
          <option value="">All Sectors</option>
          {Object.keys(SECTOR_COLORS).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={() => { setSearch(''); setStatus(''); setSector(''); setOffset(0); }} className={RESET_BTN}>Reset Filters</button>
      </div>

      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold tracking-wider text-slate-400">
              <th className="p-4">NGO Name & FCRA No.</th>
              <th className="p-4">State</th>
              <th className="p-4" title="Inferred from the organisation name">Sector (inferred)</th>
              <th className="p-4 text-center">Status</th>
              <th className="p-4 text-right">Total Foreign Funding</th>
              <th className="p-4 text-center">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900 text-sm">
            {isLoading ? (
              <tr><td colSpan="6" className="p-8"><Spinner label="Loading NGO registry..." /></td></tr>
            ) : isError ? (
              <tr><td colSpan="6" className="p-8 text-center text-red-400 text-xs">Could not load NGOs. Is the API running?</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan="6" className="p-8 text-center text-slate-500">No matching NGO records found.</td></tr>
            ) : rows.map((ngo) => (
              <tr key={ngo.id} className="hover:bg-slate-900/20 transition-all">
                <td className="p-4">
                  <span className="font-bold text-white text-xs tracking-wide block">{ngo.name}</span>
                  <span className="text-[10px] text-slate-500">FCRA Registration: {ngo.fcra_registration_number}</span>
                </td>
                <td className="p-4 text-xs text-slate-300">{ngo.state}</td>
                <td className="p-4 text-xs text-slate-300">{ngo.sector}</td>
                <td className="p-4 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold border ${STATUS_COLORS[ngo.registration_status]}`}>
                    {statusLabel(ngo.registration_status)}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <span className="text-emerald-400 font-bold tracking-tight">{formatInr(ngo.total_foreign_funding)}</span>
                  <span className="text-[9px] text-slate-500 block mt-0.5">{ngo.donation_count} annual returns</span>
                </td>
                <td className="p-4 text-center">
                  <button onClick={() => onOpenNgo(ngo.id)}
                    className="px-2.5 py-1 bg-slate-950 hover:bg-slate-900 border border-slate-800 text-[10px] text-cyan-400 hover:text-white transition-all font-semibold rounded">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination offset={offset} limit={LIMIT} total={data?.total || 0} noun="NGOs" onChange={setOffset} />
    </div>
  );
}
