export const STATUS_COLORS = {
  Active: 'bg-emerald-950/60 border-emerald-800/40 text-emerald-400',
  Suspended: 'bg-amber-950/60 border-amber-800/40 text-amber-400',
  Cancelled: 'bg-red-950/60 border-red-800/40 text-red-400',
  Unknown: 'bg-slate-900/60 border-slate-700/40 text-slate-400',
};

export const statusLabel = (status) => (status === 'Unknown' ? 'Unverified' : status);

export const SECTOR_COLORS = {
  'Social Relief / Other': '#14b8a6',
  'Education': '#f59e0b',
  'Faith-based': '#10b981',
  'Healthcare & Research': '#0ea5e9',
  'Policy & Advocacy': '#6366f1',
  'Human Rights Advocacy': '#f43f5e',
  'Environmental Advocacy': '#a855f7',
  'Media & Policy': '#f97316',
};

export const FALLBACK_COLORS = ['#22d3ee', '#818cf8', '#34d399', '#fbbf24', '#fb7185'];

export const FISCAL_YEARS = [2016, 2017, 2018, 2019, 2020];

export const INPUT =
  'px-3.5 py-2 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 ' +
  'focus:outline-none focus:border-cyan-500/50 transition-all';
export const RESET_BTN =
  'px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-xl text-xs transition-all';
