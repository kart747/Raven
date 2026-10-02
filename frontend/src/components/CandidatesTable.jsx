import React, { useState, useEffect } from 'react';
import { Search, Download, ShieldAlert, Award, TrendingUp, ExternalLink } from 'lucide-react';
import { API_BASE } from '../api';

export default function CandidatesTable({ parties, initialFilterState }) {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedParty, setSelectedParty] = useState('');
  const [selectedState, setSelectedState] = useState(initialFilterState || '');
  const [sortBy, setSortBy] = useState('');
  const [limit, setLimit] = useState(10);
  const [offset, setOffset] = useState(0);

  // States list
  const states = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
    "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli", "Daman and Diu",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
  ];

  // Sync state filter when user clicks map
  useEffect(() => {
    if (initialFilterState !== undefined) {
      setSelectedState(initialFilterState || '');
      setOffset(0);
    }
  }, [initialFilterState]);

  // Fetch candidates from backend
  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });
      if (search) params.append('search', search);
      if (selectedParty) params.append('party_id', selectedParty);
      if (selectedState) params.append('state', selectedState);
      if (sortBy) params.append('sort_by', sortBy);

      const response = await fetch(`${API_BASE}/api/v1/candidates?${params.toString()}`);
      if (response.ok) {
        const res = await response.json();
        setData(res.data);
        setTotal(res.total);
      }
    } catch (err) {
      console.error("Error fetching candidates:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [search, selectedParty, selectedState, sortBy, limit, offset]);

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
    if (selectedState) params.append('state', selectedState);
    if (sortBy) params.append('sort_by', sortBy);

    window.open(`${API_BASE}/api/v1/candidates?${params.toString()}`);
  };

  // Format currency in Indian Style (Crore/Lakh)
  const formatINR = (val) => {
    if (!val) return '₹0';
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    } else if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} Lakh`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
      {/* Header controls */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-cyan-400" />
            2024 Candidate Spotlight (Curated Sample)
          </h2>
          <p className="text-xs text-slate-400">Selected affidavit records from ADR/MyNeta, presented as a curated sample rather than a full bulk import.</p>
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
            placeholder="Search candidate or constituency..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
            className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-all"
          />
        </div>

        {/* State Filter */}
        <div className="relative">
          <select
            value={selectedState}
            onChange={(e) => { setSelectedState(e.target.value); setOffset(0); }}
            className="w-full px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">All States</option>
            {states.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
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

        {/* Sort By Filter */}
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setOffset(0); }}
            className="w-full px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">Sort (Default)</option>
            <option value="assets">Assets: High to Low</option>
            <option value="criminal_cases">Declared Cases: High to Low</option>
          </select>
        </div>

        {/* Clear Filters */}
        <button
          onClick={() => {
            setSearch('');
            setSelectedParty('');
            setSelectedState('');
            setSortBy('');
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
              <th className="p-4">Candidate Details</th>
              <th className="p-4">Constituency & State</th>
              <th className="p-4">Education</th>
              <th className="p-4 text-center">Declared Criminal Cases</th>
              <th className="p-4 text-right">Declared Assets</th>
              <th className="p-4 text-right">Declared Liabilities</th>
              <th className="p-4">Audit Citation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900 text-sm">
            {loading ? (
              <tr>
                <td colSpan="7" className="p-8 text-center text-slate-400">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                    Loading dossiers...
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan="7" className="p-8 text-center text-slate-500">
                  No matching candidate records found. If this table is empty without filters, candidate affidavits
                  (MyNeta) have not been imported yet.
                </td>
              </tr>
            ) : (
              data.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/20 transition-all">
                  <td className="p-4">
                    <div className="font-bold text-white text-xs tracking-wide">{item.name}</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="w-7 h-5 flex items-center justify-center bg-cyan-950/50 border border-cyan-800/20 text-[10px] font-bold text-cyan-400 rounded">
                        {item.party_id}
                      </span>
                      <span className="text-[10px] text-slate-400">{item.party_name}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-xs font-semibold text-slate-300">{item.constituency}</div>
                    <span className="text-[10px] text-slate-500">{item.state} ({item.year})</span>
                  </td>
                  <td className="p-4">
                    <span className="text-xs text-slate-300 font-medium">{item.education}</span>
                  </td>
                  <td className="p-4 text-center">
                    <span className={`inline-flex items-center justify-center min-w-7 h-7 text-xs font-bold rounded-full ${
                      item.criminal_cases > 0 
                        ? 'bg-red-950/60 border border-red-800/40 text-red-400' 
                        : 'bg-slate-900 border border-slate-800 text-slate-400'
                    }`}>
                      {item.criminal_cases}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-emerald-400 font-bold tracking-tight">{formatINR(item.assets)}</span>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-slate-400 font-bold tracking-tight">{formatINR(item.liabilities)}</span>
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
          <span className="font-bold text-white">{total}</span> candidates
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
