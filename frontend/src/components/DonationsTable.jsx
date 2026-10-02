import React, { useState, useEffect } from 'react';
import { Search, Download, Calendar, Tag, ShieldCheck, ArrowRight, ExternalLink } from 'lucide-react';
import { API_BASE } from '../api';

export default function DonationsTable({ parties, onOpenDonor }) {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedParty, setSelectedParty] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [limit, setLimit] = useState(10);
  const [offset, setOffset] = useState(0);

  // Years option
  const years = [2019, 2020, 2021, 2022, 2023, 2024];
  const fundingTypes = ['Electoral Bond', 'Direct Contribution'];

  // Fetch donations from backend
  const fetchDonations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });
      if (search) params.append('search', search);
      if (selectedParty) params.append('party_id', selectedParty);
      if (selectedYear) params.append('year', selectedYear);
      if (selectedType) params.append('funding_type', selectedType);

      const response = await fetch(`${API_BASE}/api/v1/donations?${params.toString()}`);
      if (response.ok) {
        const res = await response.json();
        setData(res.data);
        setTotal(res.total);
      }
    } catch (err) {
      console.error("Error fetching donations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDonations();
  }, [search, selectedParty, selectedYear, selectedType, limit, offset]);

  // Handle pagination
  const handlePageChange = (newOffset) => {
    setOffset(newOffset);
  };

  // CSV Export Trigger
  const handleExportCSV = () => {
    const params = new URLSearchParams({
      export_csv: 'true',
    });
    if (search) params.append('search', search);
    if (selectedParty) params.append('party_id', selectedParty);
    if (selectedYear) params.append('year', selectedYear);
    if (selectedType) params.append('funding_type', selectedType);

    window.open(`${API_BASE}/api/v1/donations?${params.toString()}`);
  };

  // Format currency in Indian Style (Crore/Lakh)
  const formatINR = (val) => {
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    } else if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} Lakh`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
      {/* Table Header Controls */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            Political Donations Register
          </h2>
          <p className="text-xs text-slate-400">Strictly sourced contribution disclosures (above ₹20,000 & Electoral Bonds)</p>
        </div>

        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 self-start lg:self-center px-4 py-2 bg-cyan-950/80 border border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/50 hover:text-white rounded-xl text-xs font-semibold transition-all"
        >
          <Download className="w-3.5 h-3.5" />
          Export Filtered CSV
        </button>
      </div>

      {/* Filters bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search donor or party..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
            className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-all"
          />
        </div>

        {/* Party Filter */}
        <div className="relative">
          <select
            value={selectedParty}
            onChange={(e) => { setSelectedParty(e.target.value); setOffset(0); }}
            className="w-full px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">All Parties</option>
            {parties.map((p) => (
              <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
            ))}
          </select>
        </div>

        {/* Year Filter */}
        <div className="relative">
          <select
            value={selectedYear}
            onChange={(e) => { setSelectedYear(e.target.value); setOffset(0); }}
            className="w-full px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">All Years</option>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        {/* Funding Type Filter */}
        <div className="relative">
          <select
            value={selectedType}
            onChange={(e) => { setSelectedType(e.target.value); setOffset(0); }}
            className="w-full px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">All Funding Types</option>
            {fundingTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Clear Filters */}
        <button
          onClick={() => {
            setSearch('');
            setSelectedParty('');
            setSelectedYear('');
            setSelectedType('');
            setOffset(0);
          }}
          className="px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-xl text-xs transition-all"
        >
          Reset Filters
        </button>
      </div>

      {/* Main Table */}
      <div className="overflow-x-auto border border-slate-900 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold tracking-wider text-slate-400">
              <th className="p-4">Donor Details</th>
              <th className="p-4">Recipient Party</th>
              <th className="p-4">Funding Method</th>
              <th className="p-4 text-right">Amount (INR)</th>
              <th className="p-4">Audit Citation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900 text-sm">
            {loading ? (
              <tr>
                <td colSpan="5" className="p-8 text-center text-slate-400">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                    Loading records...
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan="5" className="p-8 text-center text-slate-500">
                  No matching donation records found.
                </td>
              </tr>
            ) : (
              data.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/20 transition-all">
                  <td className="p-4">
                    {item.donor_name === 'UNKNOWN DONOR' ? (
                      <div className="font-bold text-slate-400 text-xs tracking-wide" title="Bought before 12 Apr 2019; the disclosure does not name the purchaser">
                        Purchaser not disclosed
                      </div>
                    ) : (
                      <button onClick={() => onOpenDonor?.(item.donor_id)} className="font-bold text-white hover:text-cyan-400 text-xs tracking-wide text-left">
                        {item.donor_name}
                      </button>
                    )}
                    {item.donor_industry && item.donor_industry !== 'Unknown' && (
                      <span className="inline-block mt-1 text-[10px] bg-slate-900 text-slate-400 px-2 py-0.5 rounded border border-slate-800/40">
                        {item.donor_industry}
                      </span>
                    )}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <span className="w-7 h-5 flex items-center justify-center bg-cyan-950/50 border border-cyan-800/20 text-[10px] font-bold text-cyan-400 rounded">
                        {item.party_id}
                      </span>
                      <span className="text-slate-300 font-medium text-xs">{item.party_name}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-col gap-0.5 text-xs text-slate-300">
                      <span className="font-medium">{item.funding_type}</span>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {item.date || `FY ${item.year}`}
                      </span>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-emerald-400 font-bold tracking-tight">{formatINR(item.amount)}</span>
                  </td>
                  <td className="p-4">
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-950 hover:bg-slate-900 border border-slate-850 hover:border-slate-800 text-[10px] text-cyan-400 hover:text-white transition-all font-semibold"
                    >
                      <span>{item.source_name}</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div>
          Showing <span className="font-bold text-white">{Math.min(total, offset + 1)}</span> to{' '}
          <span className="font-bold text-white">{Math.min(total, offset + limit)}</span> of{' '}
          <span className="font-bold text-white">{total}</span> donations
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => handlePageChange(offset - limit)}
            disabled={offset === 0}
            className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 text-slate-300 hover:text-white disabled:opacity-30 disabled:hover:border-slate-800 disabled:hover:text-slate-300 transition-all"
          >
            Previous
          </button>
          <button
            onClick={() => handlePageChange(offset + limit)}
            disabled={offset + limit >= total}
            className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 text-slate-300 hover:text-white disabled:opacity-30 disabled:hover:border-slate-800 disabled:hover:text-slate-300 transition-all"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
