import { Calendar, ExternalLink, X } from 'lucide-react';
import { fiscalYear, formatInr } from '../../lib/format';
import { useNgoDetail } from '../../lib/queries';
import Spinner from '../ui/Spinner';
import { STATUS_COLORS, statusLabel } from './constants';

export default function NgoDetailModal({ ngoId, onClose }) {
  const { data: ngo, isLoading, isError } = useNgoDetail(ngoId);
  if (ngoId == null) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col border-cyan-500/20" onClick={(e) => e.stopPropagation()}>
        {isLoading ? (
          <div className="p-12"><Spinner label="Loading NGO..." /></div>
        ) : isError || !ngo ? (
          <div className="p-12 text-center text-xs text-red-400">Could not load this NGO.</div>
        ) : (
          <>
            <div className="p-6 border-b border-slate-900 flex justify-between items-start gap-4">
              <div>
                <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold border mb-1.5 ${STATUS_COLORS[ngo.registration_status]}`}>
                  {statusLabel(ngo.registration_status)}
                </span>
                <h3 className="text-base font-bold text-white">{ngo.name}</h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  FCRA: {ngo.fcra_registration_number} | State: {ngo.state} | Sector (inferred): {ngo.sector}
                  {ngo.data_as_of && ` | ${ngo.data_as_of}`}
                </p>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-all">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 flex flex-col gap-2 overflow-y-auto max-h-[350px]">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Annual returns</h4>
              {[...ngo.donations].sort((a, b) => a.year - b.year).map((don) => (
                <div key={don.id} className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl flex items-center justify-between text-xs">
                  <span className="text-slate-300 flex items-center gap-1.5"><Calendar className="w-3 h-3" /> {fiscalYear(don.year)}</span>
                  <span className="flex items-center gap-3">
                    <span className="text-emerald-400 font-bold">{formatInr(don.amount)}</span>
                    <a href={don.source_url} target="_blank" rel="noopener noreferrer" title={don.source_name}
                      className="p-1 bg-slate-900 border border-slate-800 hover:border-slate-700 text-cyan-400 hover:text-white rounded">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
