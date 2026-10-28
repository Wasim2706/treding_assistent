"use client";

import React, { useEffect, useState } from "react";
import { Newspaper, ExternalLink, Filter, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { api } from "@/lib/api";
import { NewsArticle } from "@/lib/types";

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadNews() {
      try {
        const res = await api.getNews(1, 20);
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

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-emerald-400" />
            Global & Indian Market News Feed
          </h2>
          <p className="text-xs text-slate-400">
            Automated 5-minute collection with AI deduplication, event classification, and sentiment scoring.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">Loading market intelligence feed...</div>
      ) : articles.length === 0 ? (
        <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-sm">
          No news articles collected yet. The engine runs every 5 minutes, or you can click &quot;Run Cycle&quot; in the header.
        </div>
      ) : (
        <div className="space-y-4">
          {articles.map((item) => {
            const sentiment = item.analysis?.sentiment || "NEUTRAL";
            const impact = item.analysis?.impact_score || 0;

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
                    <strong className="text-emerald-400 font-medium">AI Impact Analysis:</strong> {item.analysis.summary}
                  </p>
                )}

                {item.analysis?.affected_stocks && item.analysis.affected_stocks.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
                    <span className="font-semibold text-slate-300">Affected Stocks:</span>
                    {item.analysis.affected_stocks.map((stk) => (
                      <span key={stk} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 font-mono text-[11px]">
                        {stk}
                      </span>
                    ))}
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
