import React, { useState, useEffect } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default marker icon paths in webpack/vite environments
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});


const crore = (v) => `₹${((v || 0) / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr`;
const percent = (v) => `${Math.round(v)}%`;

/** Map layers. Each turns per-state data into one number, with its own formatting and hover detail. */
function buildMetrics({ lsSummary = {}, vsSummary = {}, ngoTotals = {} }) {
  const share = (s) => (s && s.candidate_count ? (100 * s.candidates_with_cases) / s.candidate_count : null);
  return [
    {
      id: 'assets', label: 'Candidate assets', note: "Total assets declared by the state's Lok Sabha 2024 candidates",
      value: (st) => lsSummary[st]?.total_assets || null, format: crore,
      detail: (st) => `${lsSummary[st]?.candidate_count || 0} candidates`,
    },
    {
      id: 'ls_cases', label: 'Candidates with cases', note: 'Share of Lok Sabha 2024 candidates declaring pending criminal cases',
      value: (st) => share(lsSummary[st]), format: percent,
      detail: (st) => `${lsSummary[st]?.candidates_with_cases || 0} of ${lsSummary[st]?.candidate_count || 0} candidates`,
    },
    {
      id: 'mla_cases', label: 'MLAs with cases', note: 'Share of sitting MLAs declaring pending criminal cases',
      value: (st) => share(vsSummary[st]), format: percent,
      detail: (st) => `${vsSummary[st]?.candidates_with_cases || 0} of ${vsSummary[st]?.candidate_count || 0} MLAs`,
    },
    {
      id: 'ngo', label: 'NGO foreign funding', note: 'Foreign contributions declared by NGOs in the state, FY2016-17 to FY2020-21',
      value: (st) => ngoTotals[st] || null, format: crore, detail: () => 'FCRA annual returns',
    },
  ];
}

/** Zoom so the whole country (including Ladakh and the islands) is visible. */
function FitToData({ data }) {
  const map = useMap();
  useEffect(() => {
    if (data) map.fitBounds(L.geoJSON(data).getBounds(), { padding: [6, 6] });
  }, [data, map]);
  return null;
}

const SHADES = { high: '#06b6d4', mid: '#0e7490', low: '#1e4d5c', none: '#1e293b' };

export default function IndiaMap({ selectedState, onSelectState, lsSummary, vsSummary, ngoTotals }) {
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [hoveredState, setHoveredState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [metricId, setMetricId] = useState('assets');

  // Load the bundled India GeoJSON (public/india.geojson)
  useEffect(() => {
    setLoading(true);
    fetch(`${import.meta.env.BASE_URL}india.geojson`)
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then((data) => {
        // Boundaries follow the Survey of India map; names already match app/states.py
        setGeoJsonData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load India GeoJSON:', err);
        setLoading(false);
      });
  }, []);

  const metrics = buildMetrics({ lsSummary, vsSummary, ngoTotals });
  const metric = metrics.find((m) => m.id === metricId);
  const stateNames = geoJsonData ? geoJsonData.features.map((f) => f.properties.name) : [];

  // Colour bands are the lower / middle / upper thirds of states for the chosen layer
  const values = stateNames.map((st) => metric.value(st)).filter((v) => v != null && v > 0).sort((a, b) => a - b);
  const t1 = values[Math.floor(values.length / 3)] || 0;
  const t2 = values[Math.floor((2 * values.length) / 3)] || 0;

  const getStateColor = (stateName) => {
    const v = metric.value(stateName);
    if (v == null || v <= 0) return SHADES.none;
    if (v >= t2) return SHADES.high;
    if (v >= t1) return SHADES.mid;
    return SHADES.low;
  };

  const getStyle = (feature) => {
    const isSelected = selectedState === feature.properties.name;
    return {
      fillColor: isSelected ? '#22d3ee' : getStateColor(feature.properties.name),
      weight: isSelected ? 2.5 : 1,
      opacity: 1,
      color: isSelected ? '#a5f3fc' : '#334155',
      fillOpacity: isSelected ? 0.75 : 0.7,
    };
  };

  const onEachFeature = (feature, layer) => {
    layer.on({
      mouseover: (e) => {
        setHoveredState(feature.properties.name);
        e.target.setStyle({ fillOpacity: 0.9, weight: 2, color: '#22d3ee' });
      },
      mouseout: (e) => {
        setHoveredState(null);
        e.target.setStyle(getStyle(feature));
      },
      click: () => onSelectState(feature.properties.name),
    });
  };

  const hoveredValue = hoveredState ? metric.value(hoveredState) : null;

  return (
    <div className="relative glass-panel rounded-2xl p-5 flex flex-col justify-between min-h-[480px] shadow-lg border border-slate-900">
      <div className="w-full flex justify-between items-start gap-3 mb-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">India map</h3>
          <p className="text-[10px] text-slate-400">{metric.note}. Click a state for details.</p>
        </div>
        <button
          onClick={() => onSelectState(null)}
          className={`flex-shrink-0 px-3 py-1 text-[10px] font-bold uppercase rounded-full border transition-all ${
            selectedState === null
              ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
              : 'text-slate-400 border-slate-800 hover:text-white hover:border-slate-700'
          }`}
        >
          All India
        </button>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {metrics.map((m) => (
          <button key={m.id} onClick={() => setMetricId(m.id)}
            className={`px-2.5 py-1 rounded-md text-[11px] border transition-all ${
              m.id === metricId ? 'border-cyan-700 text-cyan-300 bg-cyan-950/50' : 'border-slate-800 text-slate-400 hover:text-white'}`}>
            {m.label}
          </button>
        ))}
      </div>

      <div className="relative w-full h-[400px] rounded-xl overflow-hidden border border-slate-900/60 bg-slate-950/40">
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-slate-400 bg-slate-950/50">
            <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
            <span>Loading map...</span>
          </div>
        ) : geoJsonData ? (
          <MapContainer center={[22.5937, 78.9629]} zoom={4} zoomSnap={0.25} scrollWheelZoom={false} zoomControl={false}
            attributionControl={false} className="w-full h-full" style={{ background: 'transparent' }}>
            <FitToData data={geoJsonData} />
            <GeoJSON
              key={`${metricId}-${selectedState || 'none'}-${values.length}`}
              data={geoJsonData}
              style={getStyle}
              onEachFeature={onEachFeature}
            />
          </MapContainer>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-red-400">Failed to load map boundaries.</div>
        )}

        {hoveredState && (
          <div className="absolute bottom-3 left-3 right-3 glass-panel border-cyan-500/30 bg-slate-950/90 rounded-xl p-3 shadow-2xl pointer-events-none z-[1000]">
            <div className="flex justify-between items-center gap-3">
              <span className="text-xs font-bold text-white">{hoveredState}</span>
              <span className="text-[11px] text-emerald-400 font-bold">{hoveredValue != null ? metric.format(hoveredValue) : 'No data'}</span>
            </div>
            <div className="mt-1 text-[10px] text-slate-400">{metric.label} · {metric.detail(hoveredState)}</div>
          </div>
        )}
      </div>

      <div className="w-full mt-3 flex items-center justify-between text-[9px] border-t border-slate-900/60 pt-3 text-slate-500 uppercase font-semibold">
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded" style={{ background: SHADES.high }}></span><span>≥ {metric.format(t2)}</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded" style={{ background: SHADES.mid }}></span><span>{metric.format(t1)} – {metric.format(t2)}</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded" style={{ background: SHADES.low }}></span><span>&lt; {metric.format(t1)}</span></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded" style={{ background: SHADES.none }}></span><span>No data</span></div>
      </div>
      <p className="mt-2 text-[9px] text-slate-600">
        Boundaries as per the Survey of India map, from{' '}
        <a href="https://github.com/datameet/maps/tree/master/States" target="_blank" rel="noopener noreferrer" className="hover:text-slate-400">DataMeet</a>.
      </p>
    </div>
  );
}
