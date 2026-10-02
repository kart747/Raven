import React, { useState, useEffect } from 'react';
import { 
  Building2, Globe, Search, Download, TrendingUp, 
  ShieldAlert, Award, ExternalLink, Calendar, Filter, UserCheck, HelpCircle, FileText
} from 'lucide-react';
import { API_BASE } from '../api';

const STATUS_COLORS = {
  high: 'bg-emerald-950/60 border-emerald-800/40 text-emerald-400',
  avg: 'bg-slate-900/60 border-slate-800/40 text-slate-300',
  low: 'bg-red-950/60 border-red-800/40 text-red-400',
};

export default function LegislativeTracker() {
  // Global States
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Legislator Directory States
  const [mpRows, setMpRows] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedParty, setSelectedParty] = useState('');
  const [selectedOutlier, setSelectedOutlier] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);

  // Fetch stats
  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/mp-activity/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Error fetching legislator stats:", err);
    } finally {
      setStatsLoading(false);
    }
  };

  // Fetch Legislator list
  const fetchLegislators = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });
      if (search) params.append('search', search);
      if (selectedState) params.append('state', selectedState);
      if (selectedParty) params.append('party_name', selectedParty);
      if (selectedOutlier) params.append('outlier', selectedOutlier);
      if (sortBy) params.append('sort_by', sortBy);

      const res = await fetch(`${API_BASE}/api/v1/mp-activity?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setMpRows(data.data);
        setTotalCount(data.total);
      }
    } catch (err) {
      console.error("Error fetching MP activity:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchLegislators();
  }, [search, selectedState, selectedParty, selectedOutlier, sortBy, offset]);

  // CSV Export Trigger
  const handleExportCSV = () => {
    const params = new URLSearchParams({
      export_csv: 'true',
    });
    if (search) params.append('search', search);
    if (selectedState) params.append('state', selectedState);
    if (selectedParty) params.append('party_name', selectedParty);
    if (selectedOutlier) params.append('outlier', selectedOutlier);
    if (sortBy) params.append('sort_by', sortBy);

    window.open(`${API_BASE}/api/v1/mp-activity?${params.toString()}`);
  };

  const getAttendanceStatus = (pct, avg) => {
    if (pct < 50.0) return 'low';
    if (pct >= (avg || 79.0)) return 'high';
    return 'avg';
  };

  // List of states for filtering
  const STATES = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
    "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli", "Daman and Diu",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
  ];

  const PARTIES = [
    "Bharatiya Janata Party",
    "Indian National Congress",
    "Dravida Munnetra Kazhagam",
    "Trinamool Congress",
    "Aam Aadmi Party",
    "YSR Congress Party",
    "Shiv Sena",
    "Janata Dal (United)",
    "Biju Janata Dal",
    "Telugu Desam Party",
    "Communist Party of India (Marxist)",
    "Samajwadi Party",
    "Nationalist Congress Party",
    "Rashtriya Janata Dal",
    "Indian Union Muslim League",
    "National People's Party",
    "Independent",
  ];

  return (
    <div className="flex flex-col gap-8">
      {/* 4 Core Summary Counters */}
      {!stats ? (
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
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Average Attendance */}
          <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full filter blur-xl transition-all group-hover:bg-cyan-500/10"></div>
            <div>
              <span className="text-xs text-slate-400 font-medium">National Average Attendance</span>
              <h3 className="text-2xl font-black text-white mt-1 tracking-tight">{stats.national_average_attendance.toFixed(1)}%</h3>
              <span className="text-[10px] text-slate-500 block mt-1">Average of tracked Lok Sabha MPs</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/20 flex items-center justify-center text-cyan-400">
              <UserCheck className="w-5 h-5" />
            </div>
          </div>

          {/* Total Debates */}
          <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full filter blur-xl transition-all group-hover:bg-emerald-500/10"></div>
            <div>
              <span className="text-xs text-slate-400 font-medium">Debates Participated</span>
              <h3 className="text-2xl font-black text-emerald-400 mt-1 tracking-tight">{stats.total_debates}</h3>
              <span className="text-[10px] text-slate-500 block mt-1">Total MP debate contributions</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-800/20 flex items-center justify-center text-emerald-400">
              <Award className="w-5 h-5" />
            </div>
          </div>

          {/* Total Questions Asked */}
          <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full filter blur-xl transition-all group-hover:bg-indigo-500/10"></div>
            <div>
              <span className="text-xs text-slate-400 font-medium">Questions Submitted</span>
              <h3 className="text-2xl font-black text-indigo-400 mt-1 tracking-tight">{stats.total_questions}</h3>
              <span className="text-[10px] text-slate-500 block mt-1">Star and unstarred queries</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-800/20 flex items-center justify-center text-indigo-400">
              <HelpCircle className="w-5 h-5" />
            </div>
          </div>

          {/* Private Member Bills */}
          <div className="glass-panel rounded-2xl p-5 flex items-center justify-between shadow-lg relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full filter blur-xl transition-all group-hover:bg-purple-500/10"></div>
            <div>
              <span className="text-xs text-slate-400 font-medium">Private Member Bills</span>
              <h3 className="text-2xl font-black text-purple-400 mt-1 tracking-tight">{stats.total_bills}</h3>
              <span className="text-[10px] text-slate-500 block mt-1">Legislation bills introduced</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-950/60 border border-purple-800/20 flex items-center justify-center text-purple-400">
              <FileText className="w-5 h-5" />
            </div>
          </div>
        </div>
      )}

      {/* Factual Outliers Sections */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Low Attendance Outliers */}
          <div className="glass-panel rounded-2xl p-5 shadow-lg flex flex-col gap-4">
            <div>
              <span className="text-[10px] text-red-400 font-bold uppercase tracking-wider flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                Attention Log
              </span>
              <h3 className="text-sm font-bold text-white mt-0.5">Low Attendance Outliers</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Tracked MPs with attendance levels strictly below 50%</p>
            </div>

            <div className="divide-y divide-slate-900 overflow-y-auto h-[260px] pr-1 flex flex-col">
              {stats.low_attendance_outliers.length === 0 ? (
                <div className="my-auto py-8 text-center text-xs text-slate-500">No matching MPs under 50% attendance in current dataset.</div>
              ) : (
                stats.low_attendance_outliers.map((mp) => (
                  <div key={mp.id} className="py-3 flex items-center justify-between gap-2 text-xs">
                    <div className="space-y-0.5">
                      <strong className="text-white block">{mp.mp_name}</strong>
                      <span className="text-[9px] text-slate-500 block">{mp.constituency} ({mp.party_name}) | {mp.state_represented}</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950/60 border border-red-800/40 text-red-400">
                      {mp.attendance_pct}%
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Top Debaters */}
          <div className="glass-panel rounded-2xl p-5 shadow-lg flex flex-col gap-4">
            <div>
              <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1">
                <Award className="w-3.5 h-3.5" />
                Participation Outliers
              </span>
              <h3 className="text-sm font-bold text-white mt-0.5">Top Debaters</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Top 5 MPs sorted by participation count in parliament debates</p>
            </div>

            <div className="divide-y divide-slate-900 overflow-y-auto h-[260px] pr-1 flex flex-col">
              {stats.top_debates_outliers.length === 0 ? (
                <div className="my-auto py-8 text-center text-xs text-slate-500">No debate records discovered.</div>
              ) : (
                stats.top_debates_outliers.map((mp) => (
                  <div key={mp.id} className="py-3 flex items-center justify-between gap-2 text-xs">
                    <div className="space-y-0.5">
                      <strong className="text-white block">{mp.mp_name}</strong>
                      <span className="text-[9px] text-slate-500 block">{mp.constituency} ({mp.party_name}) | {mp.state_represented}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-cyan-400 font-black block">{mp.debates_count} debates</span>
                      <span className="text-[9px] text-slate-500">Attendance: {mp.attendance_pct}%</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Top Interrogators */}
          <div className="glass-panel rounded-2xl p-5 shadow-lg flex flex-col gap-4">
            <div>
              <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider flex items-center gap-1">
                <HelpCircle className="w-3.5 h-3.5" />
                Inquiry Outliers
              </span>
              <h3 className="text-sm font-bold text-white mt-0.5">Top Interrogators</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Top 5 MPs sorted by count of official questions submitted</p>
            </div>

            <div className="divide-y divide-slate-900 overflow-y-auto h-[260px] pr-1 flex flex-col">
              {stats.top_questions_outliers.length === 0 ? (
                <div className="my-auto py-8 text-center text-xs text-slate-500">No question logs discovered.</div>
              ) : (
                stats.top_questions_outliers.map((mp) => (
                  <div key={mp.id} className="py-3 flex items-center justify-between gap-2 text-xs">
                    <div className="space-y-0.5">
                      <strong className="text-white block">{mp.mp_name}</strong>
                      <span className="text-[9px] text-slate-500 block">{mp.constituency} ({mp.party_name}) | {mp.state_represented}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-indigo-400 font-black block">{mp.questions_count} Qs</span>
                      <span className="text-[9px] text-slate-500">Attendance: {mp.attendance_pct}%</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* MP Activity Directory Table */}
      <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 shadow-xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-cyan-400" />
              MP Activity Ledger
            </h2>
            <p className="text-xs text-slate-400">Search and sort parliamentary activity, debate involvement, and bills tabled by Members of Parliament</p>
          </div>

          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 self-start lg:self-center px-4 py-2 bg-cyan-950/80 border border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/50 hover:text-white rounded-xl text-xs font-semibold transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            Export MP Ledger CSV
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search MP or Constituency..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
              className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-all"
            />
          </div>

          <select
            value={selectedState}
            onChange={(e) => { setSelectedState(e.target.value); setOffset(0); }}
            className="px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">All States</option>
            {STATES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={selectedParty}
            onChange={(e) => { setSelectedParty(e.target.value); setOffset(0); }}
            className="px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">All Parties</option>
            {PARTIES.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          <select
            value={selectedOutlier}
            onChange={(e) => { setSelectedOutlier(e.target.value); setOffset(0); }}
            className="px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50 transition-all appearance-none"
          >
            <option value="">No Filter Outliers</option>
            <option value="low_attendance">Low Attendance (&lt;50%)</option>
            <option value="top_debates">Top Debaters</option>
            <option value="top_questions">Top Interrogators</option>
          </select>

          <button
            onClick={() => {
              setSearch('');
              setSelectedState('');
              setSelectedParty('');
              setSelectedOutlier('');
              setSortBy('');
              setOffset(0);
            }}
            className="px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-xl text-xs transition-all"
          >
            Reset Filters
          </button>
        </div>

        {/* Directory Table */}
        <div className="overflow-x-auto border border-slate-900 rounded-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-900 bg-slate-950/40 text-[11px] font-bold tracking-wider text-slate-400">
                <th className="p-4">MP Name & Constituency</th>
                <th className="p-4">State</th>
                <th className="p-4">
                  <button onClick={() => setSortBy(sortBy === 'attendance' ? '' : 'attendance')} className="flex items-center gap-1 hover:text-white font-bold transition-all">
                    Attendance Record
                    {sortBy === 'attendance' && <span className="text-cyan-400">▼</span>}
                  </button>
                </th>
                <th className="p-4 text-right">
                  <button onClick={() => setSortBy(sortBy === 'debates' ? '' : 'debates')} className="flex items-center gap-1 hover:text-white font-bold ml-auto transition-all">
                    Debates
                    {sortBy === 'debates' && <span className="text-cyan-400">▼</span>}
                  </button>
                </th>
                <th className="p-4 text-right">
                  <button onClick={() => setSortBy(sortBy === 'questions' ? '' : 'questions')} className="flex items-center gap-1 hover:text-white font-bold ml-auto transition-all">
                    Questions
                    {sortBy === 'questions' && <span className="text-cyan-400">▼</span>}
                  </button>
                </th>
                <th className="p-4 text-right">
                  <button onClick={() => setSortBy(sortBy === 'bills' ? '' : 'bills')} className="flex items-center gap-1 hover:text-white font-bold ml-auto transition-all">
                    Bills Tabled
                    {sortBy === 'bills' && <span className="text-cyan-400">▼</span>}
                  </button>
                </th>
                <th className="p-4">Source Citation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900 text-sm">
              {loading ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                      Loading parliamentary registers...
                    </div>
                  </td>
                </tr>
              ) : mpRows.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500 font-medium">
                    No matching MP activity records found.
                  </td>
                </tr>
              ) : (
                mpRows.map((mp) => {
                  const status = getAttendanceStatus(mp.attendance_pct, stats?.national_average_attendance);
                  return (
                    <tr key={mp.id} className="hover:bg-slate-900/20 transition-all">
                      <td className="p-4">
                        <span className="font-bold text-white text-xs tracking-wide block">{mp.mp_name}</span>
                        <span className="text-[10px] text-slate-500">Constituency: {mp.constituency} | Party: {mp.party_name}</span>
                      </td>
                      <td className="p-4">
                        <span className="text-xs text-slate-300 font-medium">{mp.state_represented}</span>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1 w-44">
                          <div className="flex items-center justify-between text-[10px]">
                            <span className={`font-bold ${status === 'low' ? 'text-red-400' : status === 'high' ? 'text-emerald-400' : 'text-slate-300'}`}>
                              {mp.attendance_pct.toFixed(0)}%
                            </span>
                            <span className="text-slate-500">Avg: {stats?.national_average_attendance.toFixed(0)}%</span>
                          </div>
                          {/* Premium Progress Bar with dashed average line overlay */}
                          <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden relative border border-slate-800/60">
                            <div 
                              className={`h-full rounded-full ${
                                status === 'low' ? 'bg-red-500/80 shadow-[0_0_8px_rgba(239,68,68,0.2)]' : 
                                status === 'high' ? 'bg-emerald-500/80 shadow-[0_0_8px_rgba(16,185,129,0.2)]' : 
                                'bg-cyan-500/60 shadow-[0_0_8px_rgba(6,182,212,0.2)]'
                              }`} 
                              style={{ width: `${mp.attendance_pct}%` }}
                            ></div>
                            <div 
                              className="absolute top-0 bottom-0 w-0.5 border-l border-dashed border-slate-400/50" 
                              style={{ left: `${stats?.national_average_attendance || 79}%` }}
                              title={`National Average: ${stats?.national_average_attendance.toFixed(1)}%`}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <span className="font-bold text-white text-xs">{mp.debates_count}</span>
                      </td>
                      <td className="p-4 text-right">
                        <span className="font-bold text-white text-xs">{mp.questions_count}</span>
                      </td>
                      <td className="p-4 text-right">
                        <span className="font-bold text-white text-xs">{mp.bills_introduced}</span>
                      </td>
                      <td className="p-4">
                        <a
                          href={mp.official_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-950 hover:bg-slate-900 border border-slate-850 hover:border-slate-800 text-[10px] text-cyan-400 hover:text-white transition-all font-semibold"
                        >
                          <span>Vonter / India Representatives Activity</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="font-bold text-white">{Math.min(totalCount, offset + 1)}</span> to{' '}
            <span className="font-bold text-white">{Math.min(totalCount, offset + limit)}</span> of{' '}
            <span className="font-bold text-white">{totalCount}</span> MPs
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setOffset(offset - limit)}
              disabled={offset === 0}
              className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 text-slate-300 hover:text-white disabled:opacity-30 disabled:hover:border-slate-800 disabled:hover:text-slate-300 transition-all"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= totalCount}
              className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 text-slate-300 hover:text-white disabled:opacity-30 disabled:hover:border-slate-800 disabled:hover:text-slate-300 transition-all"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
