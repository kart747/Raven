import React, { useState, useEffect } from 'react';
import { Sparkles, ExternalLink, Calendar, ShieldAlert } from 'lucide-react';
import { API_BASE } from '../api';

export default function BriefViewer() {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBrief = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/brief/latest`);
      if (res.ok) {
        const data = await res.json();
        setBrief(data);
      }
    } catch (err) {
      console.error("Error fetching latest brief:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrief();
  }, []);

  const renderBriefText = (text) => {
    if (!text) return null;
    
    // Split by sections starting with ##
    const sections = text.split(/(?=##\s)/);
    
    return sections.map((sec, idx) => {
      const lines = sec.trim().split('\n');
      const headerLine = lines[0];
      const bodyLines = lines.slice(1).join('\n').trim();
      
      const isHeader = headerLine.startsWith('##');
      const title = isHeader ? headerLine.replace('##', '').trim() : '';
      
      if (!title && !bodyLines) return null;
      
      return (
        <div key={idx} className="glass-panel rounded-2xl p-6 border border-slate-900 flex flex-col gap-3 shadow-lg hover:border-slate-800 transition-all">
          {title && (
            <h3 className="text-sm font-bold text-white border-b border-slate-900 pb-2.5 flex items-center gap-2">
              <span className="w-1.5 h-3 bg-cyan-500 rounded-full"></span>
              {title}
            </h3>
          )}
          <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
            {bodyLines}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Tab Header Banner */}
      <div className="glass-panel rounded-2xl p-6 shadow-xl border border-slate-900 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            AI Intelligence Briefing
          </h2>
          <p className="text-xs text-slate-400">Weekly non-partisan intelligence summary synthesized from ECI, ADR, and MHA databases</p>
        </div>
        
        {brief && (
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/60 border border-slate-900 px-3.5 py-1.5 rounded-xl self-start sm:self-auto">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            <span>Generated: {new Date(brief.created_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 border border-slate-900">
          <div className="flex items-center justify-center gap-2">
            <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
            <span>Synthesizing data models and generating brief...</span>
          </div>
        </div>
      ) : !brief ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-500 border border-slate-900">
          Failed to load the weekly brief. Please verify backend connection.
        </div>
      ) : brief.brief_unavailable ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 border border-slate-900 flex flex-col items-center justify-center gap-3">
          <ShieldAlert className="w-8 h-8 text-cyan-500 animate-pulse" />
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Brief Generation Unavailable</h3>
          <p className="text-[11px] text-slate-400 max-w-md mx-auto leading-relaxed">
            No brief has been generated yet. It is created in the background when GROQ_API_KEY is set; you can also run `python -m app.cli brief` in the backend.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Brief Content (Lefthand 2 columns) */}
          <div className="lg:col-span-2 flex flex-col gap-5">
            {renderBriefText(brief.brief_text)}
          </div>

          {/* Audit Citations Panel (Righthand column) */}
          <div className="flex flex-col gap-5">
            <div className="glass-panel rounded-2xl p-6 border border-slate-900 shadow-lg flex flex-col gap-4">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-cyan-400" />
                  Audit Citation Index
                </h3>
                <p className="text-[10px] text-slate-400 mt-1">Verifiable audit trail for facts and numbers listed in this intelligence summary</p>
              </div>

              <div className="flex flex-col gap-2.5 mt-2">
                {brief.source_citation?.sources?.length > 0 ? (
                  brief.source_citation.sources.map((src, index) => (
                    <a
                      key={index}
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-3 bg-slate-950/60 border border-slate-900 hover:border-slate-800 rounded-xl flex items-center justify-between text-xs text-cyan-400 hover:text-white transition-all group"
                    >
                      <div className="space-y-0.5">
                        <strong className="text-slate-300 group-hover:text-cyan-400 font-semibold">{src.name}</strong>
                        <span className="text-[10px] text-slate-500 block truncate max-w-[200px]">{src.url}</span>
                      </div>
                      <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
                    </a>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 text-center py-4">No specific audit citations indexed.</div>
                )}
              </div>
            </div>

            {brief.source_citation?.input_data && (
              <details className="glass-panel rounded-2xl p-6 border border-slate-900 text-xs text-slate-400">
                <summary className="cursor-pointer text-white uppercase tracking-wider text-[10px] font-bold">
                  Data given to the model
                </summary>
                <p className="text-[10px] text-slate-500 mt-2">
                  The brief may only use these figures. Check any number in the brief against them.
                </p>
                <pre className="mt-3 whitespace-pre-wrap text-[10px] leading-relaxed text-slate-300">{brief.source_citation.input_data}</pre>
              </details>
            )}

            {/* Model Card Metadata */}
            <div className="glass-panel rounded-2xl p-6 border border-slate-900 text-xs text-slate-400 space-y-3">
              <strong className="text-white block uppercase tracking-wider text-[10px]">Model & Agent Specs</strong>
              <div className="grid grid-cols-2 gap-2 text-[10px] border-t border-b border-slate-900 py-2.5">
                <div>
                  <span className="text-slate-500 block">LLM</span>
                  <strong className="text-slate-300">{brief.source_citation?.model || 'Unknown'}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Provider</span>
                  <strong className="text-slate-300">Groq Cloud</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Agent Role</span>
                  <strong className="text-slate-300">OSINT Auditing</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Temperature</span>
                  <strong className="text-slate-300">0.2</strong>
                </div>
              </div>
              <p className="text-[9px] leading-relaxed text-slate-500">
                AI-generated summary of the loaded datasets only (electoral bonds, FCRA returns, PIB releases, Lok Sabha bills). Regenerated weekly. It can contain mistakes, so verify figures against the data above.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
