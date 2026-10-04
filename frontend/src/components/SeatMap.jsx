import { useContext, useEffect, useMemo, useState } from 'react';
import { GeoJSON, MapContainer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { formatCrore } from '../lib/format';
import { useLokSabhaSeats } from '../lib/queries';
import { LangContext } from '../lib/i18n';
import EmbedButton from './ui/EmbedButton';

// Party colours for the largest parties; everything else is grey
const PARTY_COLOURS = {
  BJP: '#f97316', INC: '#3b82f6', SP: '#e11d48', AITC: '#10b981', DMK: '#a855f7', TDP: '#eab308',
  JDU: '#84cc16', 'Shiv Sena (Uddhav Balasaheb Thackeray)': '#f59e0b', 'NCP-Sharadchandra Pawar': '#06b6d4',
  SHS: '#fb923c', RJD: '#14b8a6', 'CPI(M)': '#dc2626', YSRCP: '#0ea5e9', IND: '#94a3b8',
};
const OTHER = '#475569';
const NONE = '#1e293b';

function FitToData({ data }) {
  const map = useMap();
  useEffect(() => {
    if (data) map.fitBounds(L.geoJSON(data).getBounds(), { padding: [6, 6] });
  }, [data, map]);
  return null;
}

function useGeo(path) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}${path}`).then((r) => r.json()).then(setData).catch(() => setData(null));
  }, [path]);
  return data;
}

const LAYERS = [
  { id: 'party', label: 'Winning party' },
  { id: 'cases', label: 'Winner declared cases' },
  { id: 'assets', label: 'Winner assets' },
  { id: 'field', label: 'Candidates contesting' },
];

/** Lok Sabha 2024 at constituency level. */
export default function SeatMap({ onOpenMp, onShowStates }) {
  const lang = useContext(LangContext);
  const seatsGeo = useGeo('india-pc.geojson');
  const statesGeo = useGeo('india.geojson');
  const { data: seats = {} } = useLokSabhaSeats();
  const [layer, setLayer] = useState('party');
  const [hover, setHover] = useState(null);

  const seatOf = (f) => (f.properties.seat ? seats[`${f.properties.state}|${f.properties.seat}`] : null);

  // Tertile thresholds for numeric layers
  const bands = useMemo(() => {
    const vals = (fn) => Object.values(seats).map(fn).filter((v) => v != null).sort((a, b) => a - b);
    const cut = (v) => [v[Math.floor(v.length / 3)] || 0, v[Math.floor((2 * v.length) / 3)] || 0];
    return { assets: cut(vals((s) => s.winner?.assets)), field: cut(vals((s) => s.candidates)) };
  }, [seats]);

  const partyCounts = useMemo(() => {
    const c = {};
    Object.values(seats).forEach((s) => { if (s.winner) c[s.winner.party_id] = (c[s.winner.party_id] || 0) + 1; });
    return Object.entries(c).sort((a, b) => b[1] - a[1]);
  }, [seats]);
  const partyName = (id) => Object.values(seats).find((s) => s.winner?.party_id === id)?.winner.party || id;

  const shade = (s) => {
    if (!s?.winner) return NONE;
    const ramp = (v, [t1, t2]) => (v >= t2 ? '#06b6d4' : v >= t1 ? '#0e7490' : '#1e4d5c');
    if (layer === 'party') return PARTY_COLOURS[s.winner.party_id] || OTHER;
    if (layer === 'cases') return s.winner.criminal_cases >= 5 ? '#dc2626' : s.winner.criminal_cases > 0 ? '#f59e0b' : '#1e4d5c';
    if (layer === 'assets') return ramp(s.winner.assets, bands.assets);
    return ramp(s.candidates, bands.field);
  };

  const style = (f) => ({ fillColor: shade(seatOf(f)), fillOpacity: 0.85, color: '#0f172a', weight: 0.5 });
  const onEach = (f, l) => {
    l.on({
      mouseover: (e) => { setHover(f); e.target.setStyle({ weight: 2, color: '#e2e8f0' }); },
      mouseout: (e) => { setHover(null); e.target.setStyle(style(f)); },
      click: () => {
        const s = seatOf(f);
        if (s?.mp_id) onOpenMp(s.mp_id);
        else if (s?.winner?.source_url) window.open(s.winner.source_url, '_blank', 'noopener');
      },
    });
  };

  const h = hover ? seatOf(hover) : null;
  const legend = layer === 'party'
    ? [...partyCounts.filter(([id]) => PARTY_COLOURS[id]).slice(0, 9).map(([id, n]) => [PARTY_COLOURS[id], `${id} ${n}`]), [OTHER, 'Others']]
    : layer === 'cases' ? [['#dc2626', '5+ cases'], ['#f59e0b', '1–4 cases'], ['#1e4d5c', 'None declared']]
      : layer === 'assets' ? [['#06b6d4', `≥ ${formatCrore(bands.assets[1], 0)}`], ['#0e7490', 'Middle third'], ['#1e4d5c', `< ${formatCrore(bands.assets[0], 0)}`]]
        : [['#06b6d4', `≥ ${bands.field[1]} candidates`], ['#0e7490', 'Middle third'], ['#1e4d5c', `< ${bands.field[0]} candidates`]];

  return (
    <div className="relative glass-panel rounded-2xl p-5 flex flex-col min-h-[480px] shadow-lg border border-slate-900">
      <div className="w-full flex justify-between items-start gap-3 mb-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Lok Sabha 2024 · 543 seats</h3>
          <p className="text-[10px] text-slate-400">Each seat's 2024 general-election winner, from affidavits on MyNeta. Click a seat for its MP.</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <EmbedButton id="seats" height={720} />
          {onShowStates && (
            <button onClick={onShowStates} className="px-3 py-1 text-[10px] font-bold uppercase rounded-full border border-slate-800 text-slate-400 hover:text-white">
              States
            </button>
          )}
        </div>
      </div>
      <div className="flex flex-wrap gap-1 mb-3">
        {LAYERS.map((l) => (
          <button key={l.id} onClick={() => setLayer(l.id)}
            className={`px-2.5 py-1 rounded-md text-[11px] border ${l.id === layer ? 'border-cyan-700 text-cyan-300 bg-cyan-950/50' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
            {l.label}
          </button>
        ))}
      </div>

      <div className="relative w-full h-[520px] rounded-xl overflow-hidden border border-slate-900/60 bg-slate-950/40">
        {seatsGeo && statesGeo ? (
          <MapContainer center={[22.6, 79]} zoom={4} zoomSnap={0.25} scrollWheelZoom={true} attributionControl={false}
            className="w-full h-full" style={{ background: 'transparent' }}>
            <FitToData data={statesGeo} />
            <GeoJSON key={`${layer}-${Object.keys(seats).length}`} data={seatsGeo} style={style} onEachFeature={onEach} />
            {/* Official state boundaries on top, for outline only */}
            <GeoJSON data={statesGeo} interactive={false} style={{ fill: false, color: '#cbd5e1', weight: 1, opacity: 0.6 }} />
          </MapContainer>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-500">Loading seats…</div>
        )}
        {hover && (
          <div className="absolute bottom-3 left-3 right-3 glass-panel border-cyan-500/30 bg-slate-950/90 rounded-xl p-3 pointer-events-none z-[1000] text-xs">
            <div className="flex justify-between gap-3">
              <strong className="text-white">
                {lang === 'hi' && hover.properties.name_hi ? hover.properties.name_hi : hover.properties.name}
                <span className="text-slate-400 font-normal">, {hover.properties.state}</span>
              </strong>
              <span className="text-slate-400">{h ? `${h.candidates} candidates` : ''}</span>
            </div>
            {h?.winner ? (
              <div className="mt-1 text-slate-300">
                {h.winner.name} · {h.winner.party} · {formatCrore(h.winner.assets, 1)} declared ·{' '}
                <span className={h.winner.criminal_cases ? 'text-red-400' : ''}>{h.winner.criminal_cases} pending cases declared</span>
              </div>
            ) : (
              <div className="mt-1 text-slate-500">No match for this outline in the 2024 data{hover.properties.redrawn ? ` (seat redrawn, ${hover.properties.redrawn})` : ''}.</div>
            )}
            {hover.properties.redrawn && h?.winner && (
              <div className="mt-0.5 text-[10px] text-amber-400/80">Outline predates the {hover.properties.redrawn}; approximate.</div>
            )}
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-slate-400">
        {legend.map(([c, label]) => (
          <span key={label} className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded" style={{ background: c }} />{label}</span>
        ))}
      </div>
      <p className="mt-2 text-[9px] text-slate-600">
        Seat boundaries: DataMeet (CC0), 2008 delimitation; Assam (2023) and J&amp;K (2022) seats were later redrawn.
        State outlines as per the Survey of India map.
      </p>
    </div>
  );
}
