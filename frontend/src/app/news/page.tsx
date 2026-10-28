"use client";

import React, { useEffect, useState } from "react";
import {
  Newspaper,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";
import { api } from "@/lib/api";
import { NewsArticle } from "@/lib/types";

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    async function loadNews() {
      try {
        const res = await api.getNews(1, 25);
        if (res?.items) {
          setArticles(res.items);
        }
      } catch (err) {
        console.error("Failed loading news:", err);
      } finally {
        setLoading(false);
      }
    }
    loadNews();
  }, []);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-emerald-400" />
            AI Market Intelligence &amp; News Analysis
          </h2>
          <p className="text-xs text-slate-400">
            OpenAI structured extraction with rigorous separation of confirmed facts, market interpretations, and speculation.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">Loading market intelligence feed...</div>
      ) : articles.length === 0 ? (
        <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-sm">
          No news articles collected yet. Click &quot;Run Cycle&quot; in the header to trigger ingestion and AI analysis.
        </div>
      ) : (
        <div className="space-y-4">
          {articles.map((item) => {
            const sentiment = item.analysis?.sentiment || "NEUTRAL";
            const impact = item.analysis?.impact_score || 0;
            const isExpanded = expandedId === item.id;

            return (
              <div
                key={item.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {item.source}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(item.published_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${
                        sentiment === "BULLISH"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : sentiment === "BEARISH"
                          ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {sentiment}
                    </span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">
                      Impact: {impact}/100
                    </span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      {item.analysis?.event_type || "Market"}
                    </span>
                  </div>
                </div>

                <h3 className="text-sm sm:text-base font-bold text-white hover:text-emerald-400 transition">
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5">
                    {item.title}
                    <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                  </a>
                </h3>

                {item.analysis?.summary && (
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    <strong className="text-emerald-400 font-medium">AI Impact Brief:</strong> {item.analysis.summary}
                  </p>
                )}

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                  {item.analysis?.affected_stocks && item.analysis.affected_stocks.length > 0 ? (
                    <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">Affected Stocks:</span>
                      {item.analysis.affected_stocks.map((stk) => (
                        <span key={stk} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 font-mono text-[11px]">
                          {stk}
                        </span>
                      ))}
                    </div>
                  ) : <div />}

                  <button
                    onClick={() => toggleExpand(item.id)}
                    className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium"
                  >
                    <span>{isExpanded ? "Hide Fact / Speculation Breakdown" : "View Epistemic Breakdown"}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>

                {/* Collapsible Section: Fact vs Speculation (Section 6) */}
                {isExpanded && item.analysis && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-3 text-xs">
                    {/* Confirmed Facts */}
                    <div className="p-3 rounded-lg bg-slate-950 border border-emerald-500/20 space-y-1">
                      <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4" />
                        Confirmed Facts (Verified)
                      </div>
                      <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                        {item.analysis.confirmed_facts?.map((fact, idx) => (
                          <li key={idx}>{fact}</li>
                        )) || <li>{item.title}</li>}
                      </ul>
                    </div>

                    {/* Market Interpretation */}
                    <div className="p-3 rounded-lg bg-slate-950 border border-blue-500/20 space-y-1">
                      <div className="font-semibold text-blue-400 flex items-center gap-1.5">
                        <Lightbulb className="w-4 h-4" />
                        Market Interpretation (Logical Deduction)
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {item.analysis.reasoning}
                      </p>
                    </div>

                    {/* Speculation / Risk Factors */}
                    <div className="p-3 rounded-lg bg-slate-950 border border-amber-500/20 space-y-1">
                      <div className="font-semibold text-amber-400 flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4" />
                        Risk Factors &amp; Catalysts
                      </div>
                      <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                        {item.analysis.risk_factors?.map((risk, idx) => (
                          <li key={idx}>{risk}</li>
                        )) || <li>Headline risk and market opening gap volatility.</li>}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
