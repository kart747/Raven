import React, { useState, useEffect } from 'react';
import { MapContainer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default marker icon paths in webpack/vite environments
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const GEO_NAME_FIXES = {
  'Pondicherry': 'Puducherry',
  'Dadra and Nagar Haveli': 'Dadra and Nagar Haveli and Daman and Diu',
  'Daman and Diu': 'Dadra and Nagar Haveli and Daman and Diu',
};

export default function IndiaMap({ selectedState, onSelectState, stateStats }) {
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [hoveredState, setHoveredState] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load the bundled India GeoJSON (public/india.geojson)
  useEffect(() => {
    setLoading(true);
    fetch(`${import.meta.env.BASE_URL}india.geojson`)
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then((data) => {
        // Align map names with the canonical names used by the backend (app/states.py)
        data.features.forEach((f) => {
          f.properties.name = GEO_NAME_FIXES[f.properties.name] || f.properties.name;
        });
        setGeoJsonData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load India GeoJSON:', err);
        setLoading(false);
      });
  }, []);

  const formatCrore = (val) => {
    if (!val) return '₹0 Cr';
    return `₹${(val / 10000000).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr`;
  };

  // Colour bands are the lower / middle / upper thirds of states by total declared candidate assets
  const values = Object.values(stateStats).map((s) => s.total_assets).filter((v) => v > 0).sort((a, b) => a - b);
  const t1 = values[Math.floor(values.length / 3)] || 0;
  const t2 = values[Math.floor((2 * values.length) / 3)] || 0;

  const getStateColor = (stateName) => {
    const amount = stateStats[stateName]?.total_assets || 0;
    if (!amount) return '#1e293b'; // slate-800: no data
    if (amount >= t2) return '#083344'; // cyan-950
    if (amount >= t1) return '#0c4a6e'; // sky-950
    return '#0f172a'; // slate-900
  };

  const getStyle = (feature) => {
    const stateName = feature.properties.name;
    const isSelected = selectedState === stateName;
    const baseColor = getStateColor(stateName);

    return {
      fillColor: isSelected ? '#164e63' : baseColor, // cyan-900 highlight on selection
      weight: isSelected ? 2.5 : 1,
      opacity: 1,
      color: isSelected ? '#22d3ee' : '#334155', // cyan-400 border vs slate-700
      fillOpacity: isSelected ? 0.8 : 0.6,
    };
  };

  const onEachFeature = (feature, layer) => {
    layer.on({
      mouseover: (e) => {
        const stateName = feature.properties.name;
        const stats = stateStats[stateName] || { total_assets: 0, candidate_count: 0 };
        setHoveredState({ name: stateName, stats });

        const l = e.target;
        l.setStyle({
          fillOpacity: 0.85,
          weight: 2,
          color: '#22d3ee',
        });
      },
      mouseout: (e) => {
        setHoveredState(null);
        const l = e.target;
        l.setStyle(getStyle(feature));
      },
      click: () => {
        const stateName = feature.properties.name;
        onSelectState(stateName);
      },
    });
  };

  return (
    <div className="relative glass-panel rounded-2xl p-5 flex flex-col justify-between min-h-[480px] shadow-lg border border-slate-900">
      <div className="w-full flex justify-between items-start mb-3">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Geographic Transparency Map</h3>
          <p className="text-[10px] text-slate-400">Shaded by total assets declared by Lok Sabha 2024 candidates. Click a state for details.</p>
        </div>
        <button
          onClick={() => onSelectState(null)}
          className={`px-3 py-1 text-[10px] font-bold uppercase rounded-full border transition-all ${
            selectedState === null
              ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
              : 'text-slate-400 border-slate-800 hover:text-white hover:border-slate-700'
          }`}
        >
          All India
        </button>
      </div>

      <div className="relative w-full h-[320px] rounded-xl overflow-hidden border border-slate-900/60 bg-slate-950/40">
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-slate-400 bg-slate-950/50">
            <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
            <span>Loading geopolitical map...</span>
          </div>
        ) : geoJsonData ? (
          <MapContainer
            center={[22.5937, 78.9629]}
            zoom={4}
            scrollWheelZoom={false}
            zoomControl={false}
            className="w-full h-full"
            style={{ background: 'transparent' }}
          >
            <GeoJSON
              key={`${selectedState || 'none'}-${Object.keys(stateStats).length}`}
              data={geoJsonData}
              style={getStyle}
              onEachFeature={onEachFeature}
            />
          </MapContainer>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-red-400">
            Failed to load map boundaries.
          </div>
        )}

        {/* Hover Tooltip Overlay */}
        {hoveredState && (
          <div className="absolute bottom-3 left-3 right-3 glass-panel border-cyan-500/30 bg-slate-950/90 rounded-xl p-3 shadow-2xl pointer-events-none z-[1000] transition-opacity duration-200">
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-white">{hoveredState.name}</span>
              <span className="text-[9px] text-cyan-400 font-bold bg-cyan-950/80 px-2 py-0.5 rounded-full border border-cyan-800/40">
                {hoveredState.stats.candidate_count || 0} Affidavits
              </span>
            </div>
            <div className="mt-1.5 flex justify-between text-[11px]">
              <span className="text-slate-400">Candidates' declared assets (total):</span>
              <span className="text-emerald-400 font-bold">{formatCrore(hoveredState.stats.total_assets)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="w-full mt-3 flex items-center justify-between text-[9px] border-t border-slate-900/60 pt-3 text-slate-500 uppercase font-semibold">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded bg-cyan-950 border border-cyan-500/80"></span>
          <span>≥ {formatCrore(t2)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded bg-sky-950 border border-sky-500/80"></span>
          <span>{formatCrore(t1)} – {formatCrore(t2)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded bg-slate-900 border border-slate-700/80"></span>
          <span>&lt; {formatCrore(t1)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded bg-slate-800"></span>
          <span>No data</span>
        </div>
      </div>
    </div>
  );
}
