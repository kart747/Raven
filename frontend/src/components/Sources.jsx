import React, { useState, useEffect } from 'react';
import {
  Database, Link2, Clock, CheckCircle2, ShieldCheck, Globe, Cpu,
  FileText, Github, AlertTriangle, Radio, RefreshCw, BarChart3,
  Zap, Lock, ExternalLink, Info, TrendingUp, Users, Layers
} from 'lucide-react';
import { API_BASE } from '../api';
import DataQualityPanel from './DataQualityPanel';

// ── Live stats pulled from the Raven API ─────────────────────────────
function useLiveStats() {
  const [stats, setStats] = useState(null);
  const [ngoStats, setNgoStats] = useState(null);
  const [legislativeStats, setLegislativeStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/v1/donations/stats`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE}/api/v1/ngos/stats`).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE}/api/v1/legislative/bills?limit=1000`).then(r => r.json()).catch(() => null),
    ]).then(([d, n, l]) => {
      setStats(d);
      setNgoStats(n);
      setLegislativeStats(l);
      setLoading(false);
    });
  }, []);

  return { stats, ngoStats, legislativeStats, loading };
}

const fmt = v => v == null ? '—' : `₹${(v / 1e7).toFixed(2)} Cr`;
const fmtNum = v => v == null ? '—' : Number(v).toLocaleString('en-IN');

// ── Per-source config ─────────────────────────────────────────────────────────
const SOURCES = [
  {
    id: 'pib',
    icon: Radio,
    iconColor: 'text-cyan-400',
    iconBg: 'from-cyan-500/20 to-cyan-500/5',
    borderAccent: 'border-l-cyan-500',
    pill: { label: 'Live Feed', color: 'bg-cyan-950/60 border-cyan-800/40 text-cyan-400' },
    name: 'Press Information Bureau (PIB)',
    subtitle: 'Government of India — Official RSS Intelligence Feed',
    url: 'https://pib.gov.in',
    license: 'Open Government Data / Public Domain',
    licenseUrl: 'https://pib.gov.in/indexd.aspx',
    refresh: 'Live · 15-minute in-memory cache',
    dataType: 'Press releases, policy announcements, ministry briefs',
    description:
      'Official government press releases ingested directly from PIB\'s live RSS Main feed. ' +
      'Covers all central ministries and departments. Data is cached in-memory for 15 minutes ' +
      'to minimise load on the government portal while keeping intelligence fresh.',
    stats: null, // populated dynamically below
    limitation: null,
    datasetUrl: null,
  },
  {
    id: 'fcra',
    icon: Globe,
    iconColor: 'text-emerald-400',
    iconBg: 'from-emerald-500/20 to-emerald-500/5',
    borderAccent: 'border-l-emerald-500',
    pill: { label: 'Active Bulk Ingestion', color: 'bg-emerald-950/60 border-emerald-800/40 text-emerald-400' },
    name: 'FCRA — Foreign Contribution Regulation Act Registry',
    subtitle: 'Ministry of Home Affairs · mkonchady/fcra open dataset (MIT)',
    url: 'https://fcraonline.nic.in',
    license: 'MIT License — mkonchady/fcra',
    licenseUrl: 'https://github.com/mkonchady/fcra/blob/master/LICENSE',
    datasetUrl: 'https://github.com/mkonchady/fcra',
    refresh: 'Static historical import — FY2016-17 to FY2020-21',
    dataType: 'NGO names, states, foreign contribution amounts per fiscal year',
    description:
      'Foreign contribution receipts from MHA FCRA annual returns, via the mkonchady/fcra open dataset ' +
      '(MIT license). Covers five fiscal years of declared foreign inflows, by NGO and state.',
    limitation:
      'Registration status (active / suspended / cancelled) is not part of this dataset and is shown as ' +
      '"Unverified" unless loaded from official MHA lists. Sector labels are inferred from organisation ' +
      'names using keyword rules and may be wrong for individual NGOs.',
  },
  {
    id: 'bonds',
    icon: TrendingUp,
    iconColor: 'text-violet-400',
    iconBg: 'from-violet-500/20 to-violet-500/5',
    borderAccent: 'border-l-violet-500',
    pill: { label: 'Active Bulk Ingestion', color: 'bg-violet-950/60 border-violet-800/40 text-violet-400' },
    name: 'Electoral Bonds — ECI Supreme Court Disclosure',
    subtitle: 'SBI disclosure to the Election Commission of India · cvrajeesh/electoral-bond-data CSVs',
    url: 'https://www.eci.gov.in/disclosure-of-electoral-bonds',
    license: 'Open Public Disclosure — Supreme Court Order (WP Civil 880/2017)',
    licenseUrl: 'https://www.eci.gov.in/disclosure-of-electoral-bonds',
    datasetUrl: 'https://github.com/cvrajeesh/electoral-bond-data',
    refresh: 'Static — one-time import from March 21 2024 final SBI/ECI disclosure',
    dataType: 'Electoral bond encashments matched to purchasers · 20,384 bonds',
    description:
      'Full electoral bond encashment ledger from the March 2024 SBI submission to the Election ' +
      'Commission, mandated by the Supreme Court of India. ' +
      'Purchases and encashments are joined on the unique bond number (prefix + serial) that SBI ' +
      'disclosed on 21 March 2024, giving an exact purchaser → party link for each bond. ' +
      'Each encashment row is stored in both the normalised `donations` table and the raw ' +
      '`electoral_bonds` archive table tracking donor_name, party_name, amount, date, and bank_branch.',
    limitation:
      'About 10% of encashed bonds (≈₹870 Cr) have no purchase record in the disclosure because they ' +
      'were bought before 12 April 2019; these are shown as "UNKNOWN DONOR". Purchaser names are as ' +
      'printed by SBI, so the same company can appear under spelling variants.',
  },
  {
    id: 'myneta',
    icon: Users,
    iconColor: 'text-rose-400',
    iconBg: 'from-rose-500/20 to-rose-500/5',
    borderAccent: 'border-l-rose-500',
    pill: { label: 'Bulk Import', color: 'bg-rose-950/60 border-rose-800/40 text-rose-400' },
    name: 'Candidate Affidavits — MyNeta (ADR)',
    subtitle: 'Association for Democratic Reforms · Lok Sabha 2024',
    url: 'https://myneta.info/LokSabha2024/',
    license: 'ADR open data — attribution to MyNeta / ADR',
    licenseUrl: 'https://myneta.info/',
    datasetUrl: 'https://myneta.info/LokSabha2024/',
    refresh: 'On demand · python -m app.cli ingest-candidates (pages cached locally)',
    dataType: 'Self-declared assets, liabilities, criminal cases and education of every 2024 Lok Sabha candidate',
    description:
      'Candidate affidavit summaries compiled by ADR from nomination papers filed with the Election Commission. ' +
      'Imported from MyNeta\'s public listings with rate-limited requests; each candidate links to their MyNeta page.',
    limitation:
      'Figures are self-declared by candidates. "Criminal cases" are pending cases declared in the affidavit, not convictions.',
  },
  {
    id: 'legislative',
    icon: FileText,
    iconColor: 'text-amber-400',
    iconBg: 'from-amber-500/20 to-amber-500/5',
    borderAccent: 'border-l-amber-500',
    pill: { label: 'Open Legislative Data', color: 'bg-amber-950/60 border-amber-800/40 text-amber-400' },
    name: 'Parliamentary Legislative Data',
    subtitle: 'PRS India / Lok Sabha activity CSVs · ODbL-1.0',
    url: 'https://prsindia.org',
    license: 'ODbL-1.0 / Open Government Data',
    licenseUrl: 'https://opendatacommons.org/licenses/odbl/1-0/',
    datasetUrl: 'https://github.com/Vonter/india-representatives-activity',
    refresh: 'On demand · python -m app.cli ingest-legislative',
    dataType: 'MP attendance, debate, questions, and private member bill metadata',
    description:
      'Lightweight parliamentary activity ingest built from the open PRS-derived activity CSVs. ' +
      'Raven stores only the essential metadata required for state dossiers and brief synthesis: ' +
      'active MP activity rows plus bill title, ministry, status, state representation, and official filing URL. ' +
      'No full bill text PDFs or large document blobs are stored in SQLite.',
    limitation:
      'Current coverage is limited to the current Lok Sabha open activity export and private-member-bill listings. ' +
      'Government bill text, committee reports, and PDF full text are intentionally excluded to keep the local database lightweight.',
  },
  {
    id: 'groq',
    icon: Zap,
    iconColor: 'text-amber-400',
    iconBg: 'from-amber-500/20 to-amber-500/5',
    borderAccent: 'border-l-amber-500',
    pill: { label: 'AI Synthesis Engine', color: 'bg-amber-950/60 border-amber-800/40 text-amber-400' },
    name: 'AI Data Brief — Groq',
    subtitle: 'Groq Cloud API · model set by GROQ_MODEL (default openai/gpt-oss-120b)',
    url: 'https://groq.com',
    license: 'Groq ToS + model licence',
    licenseUrl: 'https://groq.com/terms-of-use',
    datasetUrl: null,
    refresh: 'Regenerated weekly · python -m app.cli brief',
    dataType: 'Automated executive briefs synthesised from local Raven database',
    description:
      'Automated brief generation using an LLM via Groq Cloud. ' +
      'The model is strictly prompted to reference only facts present in the Raven database — ' +
      'electoral bond totals, NGO foreign contribution totals, recent PIB releases, and bills. ' +
      'The exact input figures are shown next to each brief so they can be checked. ' +
      'No external inference, editorialising, or political opinion is permitted by the system prompt.',
    limitation: null,
  },
];

// ── Integrity Guarantee Banner ────────────────────────────────────────────────
function IntegrityBanner() {
  const guarantees = [
    { icon: Lock,      text: 'Raw figures are never altered' },
    { icon: FileText,  text: 'Every number cites its source document' },
    { icon: Users,     text: 'Zero editorial inference or political opinion' },
    { icon: Layers,    text: 'All data is publicly available OSINT' },
  ];
  return (
    <div className="relative overflow-hidden rounded-2xl border border-cyan-800/30 bg-gradient-to-br from-cyan-950/40 via-slate-950/60 to-indigo-950/30 p-6 shadow-lg shadow-cyan-900/10">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-12 -left-12 w-48 h-48 rounded-full bg-cyan-500/5 blur-3xl" />
        <div className="absolute -bottom-8 -right-8 w-36 h-36 rounded-full bg-indigo-500/5 blur-3xl" />
      </div>

      <div className="relative flex flex-col sm:flex-row items-start sm:items-center gap-4">
        {/* Shield icon */}
        <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500/25 to-indigo-500/15 border border-cyan-700/30 flex items-center justify-center shadow-inner">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-black uppercase tracking-widest text-cyan-400">Data Integrity Guarantee</span>
            <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-cyan-900/50 border border-cyan-700/40 text-cyan-300 uppercase tracking-wider">
              Verified
            </span>
          </div>
          <p className="text-sm font-semibold text-white leading-snug">
            Raven strictly aggregates publicly available OSINT data without editorializing or altering raw reported figures.
          </p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            All funding totals, NGO receipts, and candidate affidavit values are reproduced verbatim
            from official government disclosures, gazette filings, and audited Election Commission records.
          </p>
        </div>
      </div>

      {/* Four pillars */}
      <div className="relative mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {guarantees.map(({ icon: Icon, text }) => (
          <div key={text} className="flex items-center gap-2 bg-slate-950/40 border border-slate-800/60 rounded-xl px-3 py-2">
            <Icon className="w-3.5 h-3.5 text-cyan-500 flex-shrink-0" />
            <span className="text-[11px] font-semibold text-slate-300 leading-tight">{text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Live Stats Ticker ─────────────────────────────────────────────────────────
function LiveStatsTicker({ stats, ngoStats, loading }) {
  const items = loading ? [] : [
    { label: 'Electoral Bond Transactions', value: fmtNum(stats?.total_donations_count) },
    { label: 'Total Political Funding Tracked', value: fmt(stats?.total_funding) },
    { label: 'BJP — Top Funded Party', value: fmt(stats?.party_shares?.[0]?.amount) },
    { label: 'AITC — #2', value: fmt(stats?.party_shares?.[1]?.amount) },
    { label: 'INC — #3', value: fmt(stats?.party_shares?.[2]?.amount) },
    { label: 'FCRA NGOs Tracked', value: fmtNum(ngoStats?.total_ngos_count) },
    { label: 'Foreign Contributions (NGOs)', value: fmt(ngoStats?.total_funding) },
    { label: 'Unique Corporate Donors', value: fmtNum(stats?.total_donors_count) },
  ];

  if (loading || items.length === 0) {
    return (
      <div className="h-9 flex items-center gap-2 text-xs text-slate-500 px-4 rounded-xl border border-slate-900 bg-slate-950/40">
        <div className="w-3 h-3 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        Fetching live database metrics…
      </div>
    );
  }

  const doubled = [...items, ...items];
  return (
    <div className="relative flex items-center h-9 overflow-hidden rounded-xl border border-slate-800/60 bg-slate-950/50">
      <div className="absolute left-0 top-0 h-full w-10 bg-gradient-to-r from-slate-950 to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 h-full w-10 bg-gradient-to-l from-slate-950 to-transparent z-10 pointer-events-none" />
      <div className="animate-marquee whitespace-nowrap flex items-center gap-10 px-4 text-xs">
        {doubled.map((item, i) => (
          <span key={i} className="inline-flex items-center gap-2">
            <span className="text-slate-500 uppercase tracking-wider text-[10px]">{item.label}</span>
            <span className="font-black text-cyan-400">{item.value}</span>
            <span className="text-slate-700">·</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Source Card ───────────────────────────────────────────────────────────────
function SourceCard({ src, liveStats }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = src.icon;

  // Attach live stats to relevant cards
  let liveRow = null;
  if (src.id === 'bonds' && liveStats?.stats) {
    const s = liveStats.stats;
    liveRow = [
      { label: 'Transactions in DB', value: fmtNum(s.total_donations_count) },
      { label: 'Grand Total Encashed', value: fmt(s.total_funding) },
      { label: 'Parties Funded', value: fmtNum(s.party_shares?.length) },
      { label: 'Unique Donors', value: fmtNum(s.total_donors_count) },
    ];
  }
  if (src.id === 'fcra' && liveStats?.ngoStats) {
    const n = liveStats.ngoStats;
    liveRow = [
      { label: 'NGOs in DB', value: fmtNum(n.total_ngos_count) },
      { label: 'Total Foreign Contributions', value: fmt(n.total_funding) },
      { label: 'Active FCRA', value: fmtNum(n.active_ngos_count) },
      { label: 'Cancelled / Suspended', value: `${fmtNum(n.cancelled_ngos_count)} / ${fmtNum(n.suspended_ngos_count)}` },
    ];
  }
  if (src.id === 'legislative' && liveStats?.legislativeStats) {
    const l = liveStats.legislativeStats;
    const billRows = Array.isArray(l.data) ? l.data : [];
    const introducedCount = billRows.filter(b => b.current_status === 'Introduced').length;
    const pendingCount = billRows.filter(b => b.current_status === 'Pending').length;
    const passedCount = billRows.filter(b => b.current_status === 'Passed').length;
    liveRow = [
      { label: 'Bills in DB', value: fmtNum(l.total) },
      { label: 'Introduced / Pending', value: `${introducedCount} / ${pendingCount}` },
      { label: 'Passed Bills', value: fmtNum(passedCount) },
      { label: 'Latest State Dossier', value: 'Available via API' },
    ];
  }

  return (
    <div className={`group relative border-l-2 ${src.borderAccent} border border-slate-800/60 bg-slate-950/40 rounded-2xl overflow-hidden transition-all duration-300 hover:border-slate-700/70 hover:shadow-lg hover:shadow-slate-900/50`}>
      {/* Top section */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          {/* Left: icon + title */}
          <div className="flex items-start gap-4 flex-1 min-w-0">
            <div className={`flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${src.iconBg} border border-slate-700/40 flex items-center justify-center`}>
              <Icon className={`w-5 h-5 ${src.iconColor}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-0.5">
                <h3 className="text-sm font-bold text-white leading-tight">{src.name}</h3>
                <span className={`inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full border ${src.pill.color}`}>
                  <CheckCircle2 className="w-2.5 h-2.5" />
                  {src.pill.label}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">{src.subtitle}</p>
            </div>
          </div>

          {/* Right: Visit + expand */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <a
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-600 hover:text-white rounded-lg text-xs font-semibold text-slate-300 transition-all"
            >
              <ExternalLink className="w-3 h-3" />
              Portal
            </a>
            <button
              onClick={() => setExpanded(e => !e)}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-slate-500 hover:text-slate-300 border border-slate-800 hover:border-slate-700 bg-slate-900/50 transition-all"
              title={expanded ? 'Collapse' : 'Expand details'}
            >
              <Info className="w-3 h-3" />
              {expanded ? 'Less' : 'More'}
            </button>
          </div>
        </div>

        {/* Metadata grid */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="flex items-start gap-2">
            <Clock className="w-3.5 h-3.5 text-slate-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[9px] uppercase tracking-wider text-slate-600 font-bold">Refresh Cycle</p>
              <p className="text-[11px] text-slate-300 font-semibold">{src.refresh}</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Cpu className="w-3.5 h-3.5 text-slate-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[9px] uppercase tracking-wider text-slate-600 font-bold">License</p>
              <a
                href={src.licenseUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold transition-all"
              >
                {src.license}
              </a>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <FileText className="w-3.5 h-3.5 text-slate-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[9px] uppercase tracking-wider text-slate-600 font-bold">Data Scope</p>
              <p className="text-[11px] text-slate-300 font-semibold">{src.dataType}</p>
            </div>
          </div>
        </div>

        {/* GitHub dataset link */}
        {src.datasetUrl && (
          <div className="mt-3 flex items-center gap-1.5">
            <Github className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-[10px] text-slate-500">Dataset: </span>
            <a
              href={src.datasetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-cyan-500 hover:text-cyan-400 font-semibold transition-all underline decoration-cyan-500/20"
            >
              {src.datasetUrl.replace('https://github.com/', 'github.com/')}
            </a>
          </div>
        )}
      </div>

      {/* Live DB stats row */}
      {liveRow && (
        <div className="px-5 pb-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 rounded-xl bg-slate-900/60 border border-slate-800/40">
            {liveRow.map(({ label, value }) => (
              <div key={label}>
                <p className="text-[9px] uppercase tracking-wider text-slate-600 font-bold">{label}</p>
                <p className="text-xs font-black text-white">{value}</p>
              </div>
            ))}
          </div>
          <p className="text-[9px] text-slate-600 mt-1.5 flex items-center gap-1">
            <BarChart3 className="w-3 h-3" />
            Live figures pulled from Raven database
          </p>
        </div>
      )}

      {/* Expanded description */}
      {expanded && (
        <div className="border-t border-slate-800/60 px-5 py-4 space-y-3 bg-slate-950/20">
          <p className="text-xs text-slate-300 leading-relaxed">{src.description}</p>
          {src.limitation && (
            <div className="flex gap-2 items-start p-3 bg-amber-950/20 border border-amber-800/30 rounded-xl text-[11px] text-amber-300 leading-relaxed">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-amber-400 mt-0.5" />
              <span>{src.limitation}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function Sources() {
  const { stats, ngoStats, loading } = useLiveStats();

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto">

      {/* Page Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
            <Database className="w-6 h-6 text-cyan-400" />
            Data Provenance &amp; Sources Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1.5 max-w-2xl leading-relaxed">
            Where every dataset comes from, its licence, how it is refreshed, and how complete it currently is.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-500 border border-slate-800 rounded-lg px-3 py-2 bg-slate-900/50 flex-shrink-0">
          <RefreshCw className="w-3 h-3 text-slate-600" />
          {loading ? 'Fetching live stats…' : 'DB stats live'}
        </div>
      </div>

      {/* ── Data Integrity Guarantee Banner ── */}
      <IntegrityBanner />

      {/* ── Live coverage / freshness per dataset ── */}
      <DataQualityPanel />

      {/* ── Live Stats Ticker ── */}
      <LiveStatsTicker stats={stats} ngoStats={ngoStats} loading={loading} />

      {/* ── Source Cards ── */}
      <div className="flex flex-col gap-4">
        {SOURCES.map(src => (
          <SourceCard key={src.id} src={src} liveStats={{ stats, ngoStats }} />
        ))}
      </div>

      {/* ── Compliance block ── */}
      <div className="rounded-2xl border border-slate-800/50 bg-slate-950/30 p-5 flex gap-3 items-start">
        <ShieldCheck className="w-5 h-5 text-slate-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1.5 text-[11px] text-slate-500 leading-relaxed">
          <p className="font-bold text-slate-400 text-xs">Regulatory Compliance &amp; Robot-Exclusion Policy</p>
          <p>
            Raven stores bulk-imported datasets locally to avoid repetitive hits on public government portals.
            All records derive from officially published archives, gazette notifications, or court-mandated public disclosures.
          </p>
          <p>
            Historical datasets are clearly dated. Where limitations exist in the source data
            (e.g., pre-disclosure bond purchasers), they are documented explicitly in each source card above.
          </p>
          <p className="pt-1 border-t border-slate-800/60 text-[10px]">
            Raven does not editorialize, infer political conclusions, or alter raw reported figures.
            The AI brief engine is constrained by a strict system prompt to cite only figures present in the local database.
          </p>
        </div>
      </div>

    </div>
  );
}
