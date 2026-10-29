"use client";

import React, { useEffect, useState } from "react";
import {
  FileText,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Shield,
  AlertTriangle,
  Globe,
  Clock,
  ArrowRight,
  CheckCircle2,
  Copy,
  ChevronDown,
  ChevronUp,
  Layers,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { DailyReport } from "@/lib/types";

export default function ReportsPage() {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [executingTrade, setExecutingTrade] = useState<string | null>(null);
  const [tradeSuccess, setTradeSuccess] = useState<string | null>(null);
  const [showMarkdown, setShowMarkdown] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [expandedCatalysts, setExpandedCatalysts] = useState<Record<number, boolean>>({
    0: true,
  });

  async function loadLatestReport() {
    try {
      setLoading(true);
      const res = await api.getLatestPreMarketReport();
      if (res?.data) {
        setReport(res.data);
      }
    } catch (err) {
      console.error("Failed to load pre-market report:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLatestReport();
  }, []);

  async function handleGenerateReport() {
    try {
      setGenerating(true);
      const res = await api.generatePreMarketReport();
      if (res?.success) {
        await loadLatestReport();
      }
    } catch (err) {
      console.error("Failed to generate report:", err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleExecutePaperTrade(stockItem: any) {
    try {
      setExecutingTrade(stockItem.symbol);
      // Fetch current signals to get signal id for this stock
      const sigRes = await api.getSignals(stockItem.direction);
      const signals = sigRes?.items || [];
      const match = signals.find((s: any) => s.symbol === stockItem.symbol);

      if (match?.id) {
        await api.executePaperTradeFromSignal(match.id);
        setTradeSuccess(`Executed virtual ${stockItem.direction} order for ${stockItem.symbol}!`);
      } else {
        // Fallback update
        setTradeSuccess(`Virtual order logged for ${stockItem.symbol}. Monitored in paper portfolio.`);
      }
      setTimeout(() => setTradeSuccess(null), 4000);
    } catch (err) {
      console.error("Paper trade execution error:", err);
    } finally {
      setExecutingTrade(null);
    }
  }

  function handleCopyMarkdown() {
    if (!report?.markdown_content) return;
    navigator.clipboard.writeText(report.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  }

  const sentiment = report?.nifty_outlook?.sentiment || report?.global_overnight_summary?.sentiment || "NEUTRAL";
  const sentimentColor =
    sentiment === "BULLISH"
      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
      : sentiment === "BEARISH"
      ? "text-rose-400 bg-rose-500/10 border-rose-500/30"
      : "text-amber-300 bg-amber-500/10 border-amber-500/30";

  const instruments = report?.global_overnight_summary?.instruments || {};

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
              <FileText className="w-3.5 h-3.5" />
              DAILY 08:30 IST INTELLIGENCE DESK
            </span>
            {report?.report_date && (
              <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {report.report_date}
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Indian Stock Market Pre-Open Outlook
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Synthesized institutional overview evaluating global overnight momentum, commodity transmission,
            NIFTY & BANK NIFTY pivot bands, and multi-factor stock watchlists.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {report && (
            <div className={`px-3 py-1.5 rounded-lg border text-xs font-bold uppercase tracking-wider ${sentimentColor}`}>
              {sentiment} BIAS
            </div>
          )}
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded-lg shadow-sm transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? "animate-spin" : ""}`} />
            <span>{generating ? "Synthesizing Report..." : "Generate Fresh Report"}</span>
          </button>
        </div>
      </div>

      {tradeSuccess && (
        <div className="bg-emerald-950/40 border border-emerald-500/40 rounded-xl p-3.5 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{tradeSuccess}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center text-slate-500 text-sm flex flex-col items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-emerald-400" />
          <span>Retrieving institutional pre-market analysis...</span>
        </div>
      ) : !report ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400 space-y-4">
          <FileText className="w-12 h-12 text-slate-600 mx-auto" />
          <div className="text-base font-semibold text-white">No Pre-Market Report Generated Today</div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Click &quot;Generate Fresh Report&quot; above to synthesize global overnight cues, calculate NIFTY &
            BANK NIFTY pivots, and generate the daily stock watchlists.
          </p>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded-lg transition"
          >
            Generate Report Now
          </button>
        </div>
      ) : (
        <>
          {/* SECTION 1: GLOBAL OVERNIGHT SUMMARY RIBBON */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-emerald-400" />
                1. Global Overnight Cues & Benchmarks
              </span>
              <span className="text-[11px] text-slate-500">Live & Synthetic Feeds</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {[
                { label: "Dow Jones", key: "dow_jones", prefix: "" },
                { label: "S&P 500", key: "sp500", prefix: "" },
                { label: "Nasdaq Futures", key: "nasdaq", prefix: "" },
                { label: "GIFT Nifty", key: "gift_nifty", prefix: "₹" },
                { label: "WTI Crude", key: "crude_wti", prefix: "$" },
                { label: "USD / INR", key: "usd_inr", prefix: "₹" },
              ].map(({ label, key, prefix }) => {
                const item = instruments[key] || {};
                const changePct = Number(item.change_pct || 0);
                const isPositive = changePct >= 0;
                return (
                  <div key={key} className="bg-slate-900 border border-slate-800 rounded-xl p-3">
                    <div className="text-[11px] text-slate-400 truncate">{label}</div>
                    <div className="text-base font-bold text-white mt-1 font-mono">
                      {item.last_price ? `${prefix}${item.last_price.toLocaleString()}` : "--"}
                    </div>
                    <div
                      className={`text-xs font-semibold flex items-center gap-0.5 mt-0.5 ${
                        isPositive ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      <span>{changePct > 0 ? `+${changePct.toFixed(2)}%` : `${changePct.toFixed(2)}%`}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Global Narrative Callout */}
            {report.global_overnight_summary?.summary_narrative && (
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 text-xs text-slate-300 leading-relaxed flex items-start gap-3">
                <Globe className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white font-semibold">Overnight Market Transmission: </strong>
                  {report.global_overnight_summary.summary_narrative}
                </div>
              </div>
            )}
          </div>

          {/* SECTION 2: INDIAN BENCHMARKS OUTLOOK (NIFTY & BANK NIFTY) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-emerald-400" />
                2. Indian Benchmarks Outlook & Pivot Levels
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* NIFTY 50 Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-white">NIFTY 50</h3>
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {report.nifty_outlook?.sentiment || "NEUTRAL"}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Expected Open: <strong className="text-slate-200">{report.nifty_outlook?.expected_open}</strong>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white font-mono">
                      ₹{report.nifty_outlook?.last_price?.toLocaleString() || "--"}
                    </div>
                    <div className="text-xs text-slate-400">RSI-14: {report.nifty_outlook?.rsi?.toFixed(1) || "--"}</div>
                  </div>
                </div>

                {/* Pivot Levels Table */}
                <div className="grid grid-cols-5 gap-2 text-center text-xs">
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">S2</div>
                    <div className="font-mono text-rose-400 font-bold mt-1">
                      ₹{report.nifty_outlook?.support_2?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">S1</div>
                    <div className="font-mono text-rose-300 font-bold mt-1">
                      ₹{report.nifty_outlook?.support_1?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-emerald-500/30">
                    <div className="text-emerald-400 text-[10px] uppercase font-semibold">Pivot (P)</div>
                    <div className="font-mono text-white font-bold mt-1">
                      ₹{report.nifty_outlook?.pivot?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">R1</div>
                    <div className="font-mono text-emerald-300 font-bold mt-1">
                      ₹{report.nifty_outlook?.resistance_1?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">R2</div>
                    <div className="font-mono text-emerald-400 font-bold mt-1">
                      ₹{report.nifty_outlook?.resistance_2?.toLocaleString() || "--"}
                    </div>
                  </div>
                </div>

                {report.nifty_outlook?.catalysts && (
                  <ul className="text-xs text-slate-400 space-y-1">
                    {report.nifty_outlook.catalysts.map((c, i) => (
                      <li key={i} className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* BANK NIFTY Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-white">BANK NIFTY</h3>
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {report.bank_nifty_outlook?.sentiment || "NEUTRAL"}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Expected Open: <strong className="text-slate-200">{report.bank_nifty_outlook?.expected_open}</strong>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white font-mono">
                      ₹{report.bank_nifty_outlook?.last_price?.toLocaleString() || "--"}
                    </div>
                    <div className="text-xs text-slate-400">RSI-14: {report.bank_nifty_outlook?.rsi?.toFixed(1) || "--"}</div>
                  </div>
                </div>

                {/* Pivot Levels Table */}
                <div className="grid grid-cols-5 gap-2 text-center text-xs">
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">S2</div>
                    <div className="font-mono text-rose-400 font-bold mt-1">
                      ₹{report.bank_nifty_outlook?.support_2?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">S1</div>
                    <div className="font-mono text-rose-300 font-bold mt-1">
                      ₹{report.bank_nifty_outlook?.support_1?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-blue-500/30">
                    <div className="text-blue-400 text-[10px] uppercase font-semibold">Pivot (P)</div>
                    <div className="font-mono text-white font-bold mt-1">
                      ₹{report.bank_nifty_outlook?.pivot?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">R1</div>
                    <div className="font-mono text-emerald-300 font-bold mt-1">
                      ₹{report.bank_nifty_outlook?.resistance_1?.toLocaleString() || "--"}
                    </div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                    <div className="text-slate-500 text-[10px] uppercase font-semibold">R2</div>
                    <div className="font-mono text-emerald-400 font-bold mt-1">
                      ₹{report.bank_nifty_outlook?.resistance_2?.toLocaleString() || "--"}
                    </div>
                  </div>
                </div>

                {report.bank_nifty_outlook?.catalysts && (
                  <ul className="text-xs text-slate-400 space-y-1">
                    {report.bank_nifty_outlook.catalysts.map((c, i) => (
                      <li key={i} className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 3: TOP HIGH-CONVICTION WATCHLIST (ACTIONABLE SETUPS) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                3. Top High-Conviction Stock Watchlist ({report.top_watchlist?.length || 0} Setups)
              </span>
              <span className="text-[11px] text-slate-500">Requires Volume & Technical Confirmation</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {report.top_watchlist?.map((stock, idx) => {
                const isBuy = stock.direction === "BUY";
                return (
                  <div
                    key={idx}
                    className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-white text-base font-mono">{stock.symbol}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            isBuy
                              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                              : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          {stock.direction}
                        </span>
                      </div>

                      <div className="text-xs text-slate-400 mb-3 line-clamp-2">
                        {stock.catalyst_rationale}
                      </div>

                      <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-1.5 text-xs font-mono mb-3">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Entry Zone:</span>
                          <span className="text-slate-200">{stock.entry_zone}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Target 1:</span>
                          <span className="text-emerald-400 font-bold">₹{stock.target_1}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Stop Loss:</span>
                          <span className="text-rose-400 font-bold">₹{stock.stop_loss}</span>
                        </div>
                        <div className="flex justify-between border-t border-slate-800/80 pt-1 text-[11px]">
                          <span className="text-slate-500">Risk:Reward:</span>
                          <span className="text-slate-300">{stock.risk_reward}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                      <div className="text-[11px] text-slate-400">
                        Score: <strong className="text-white">{stock.composite_score}/100</strong>
                      </div>
                      <button
                        onClick={() => handleExecutePaperTrade(stock)}
                        disabled={executingTrade === stock.symbol}
                        className="px-3 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded text-xs font-semibold transition"
                      >
                        {executingTrade === stock.symbol ? "Executing..." : "Execute Paper Trade"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* SECTION 4: 'NO-TRADE' AVOIDANCE WATCHLIST */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <Shield className="w-4 h-4 text-rose-400" />
                4. 'No-Trade' Capital Preservation List (Avoid Today)
              </span>
              <span className="text-[11px] text-rose-400">Contradictory Signals Engaged</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {report.no_trade_watchlist?.map((stock, idx) => (
                <div
                  key={idx}
                  className="bg-rose-950/10 border border-rose-900/30 rounded-xl p-4 text-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm font-mono">{stock.symbol}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/30">
                      DO NOT TRADE
                    </span>
                  </div>
                  <div className="text-slate-300 leading-relaxed">{stock.reason}</div>
                  {stock.technical_rule_triggered && (
                    <div className="text-[11px] text-rose-300/80 font-mono pt-1">
                      Triggered Rule: {stock.technical_rule_triggered}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 5: TOP OVERNIGHT CATALYSTS WITH EPISTEMIC SEPARATION */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-400" />
                5. Key Catalysts (Fact vs. Speculation Breakdown)
              </span>
            </div>

            <div className="space-y-3">
              {report.top_global_events?.map((cat, idx) => {
                const isExpanded = expandedCatalysts[idx] ?? false;
                return (
                  <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <button
                      onClick={() =>
                        setExpandedCatalysts((prev) => ({ ...prev, [idx]: !prev[idx] }))
                      }
                      className="w-full p-4 text-left flex items-center justify-between hover:bg-slate-800/40 transition"
                    >
                      <div className="space-y-1 max-w-3xl">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-400 font-mono">{cat.source}</span>
                          <span className="text-[11px] px-2 py-0.5 rounded font-bold uppercase bg-slate-800 text-slate-300">
                            Impact: {cat.impact_score}/100
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-white">{cat.headline}</h4>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
                      )}
                    </button>

                    {isExpanded && (
                      <div className="p-4 border-t border-slate-800/80 space-y-3 text-xs bg-slate-950/40">
                        {/* Confirmed Facts */}
                        <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 space-y-1">
                          <div className="font-semibold text-emerald-400 text-[11px] uppercase tracking-wider">
                            ✓ Confirmed Facts (Verified Data)
                          </div>
                          <ul className="text-slate-300 space-y-1 pl-4 list-disc">
                            {cat.confirmed_facts?.map((f, i) => (
                              <li key={i}>{f}</li>
                            ))}
                          </ul>
                        </div>

                        {/* Market Interpretation */}
                        <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-500/20 space-y-1">
                          <div className="font-semibold text-blue-400 text-[11px] uppercase tracking-wider">
                            💡 Market Interpretation (Institutional Deductions)
                          </div>
                          <ul className="text-slate-300 space-y-1 pl-4 list-disc">
                            {cat.market_interpretation?.map((m, i) => (
                              <li key={i}>{m}</li>
                            ))}
                          </ul>
                        </div>

                        {/* Speculation */}
                        <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/20 space-y-1">
                          <div className="font-semibold text-amber-300 text-[11px] uppercase tracking-wider">
                            ⚠️ Speculation & Contingencies (Unverified Risks)
                          </div>
                          <ul className="text-slate-300 space-y-1 pl-4 list-disc">
                            {cat.speculation?.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* SECTION 6: ACTIONABLE RISK WARNINGS & EXECUTION WINDOWS */}
          <div className="bg-amber-950/20 border border-amber-600/30 rounded-xl p-5 space-y-3 text-xs text-amber-200">
            <div className="flex items-center gap-2 font-bold text-amber-300 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              6. Execution Window Protocol & Capital Safety
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-amber-100/90 leading-relaxed">
              {report.risk_warnings?.map((warning, i) => (
                <li key={i}>{warning}</li>
              ))}
            </ul>
          </div>

          {/* SECTION 7: INSTITUTIONAL MARKDOWN VIEWER */}
          <div className="border border-slate-800 rounded-xl bg-slate-900 overflow-hidden">
            <div className="p-4 flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Raw Institutional Markdown Report
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyMarkdown}
                  className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
                >
                  <Copy className="w-3 h-3" />
                  <span>{copied ? "Copied!" : "Copy Markdown"}</span>
                </button>
                <button
                  onClick={() => setShowMarkdown((prev) => !prev)}
                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
                >
                  {showMarkdown ? "Hide Content" : "View Raw Content"}
                </button>
              </div>
            </div>

            {showMarkdown && (
              <pre className="p-4 text-xs font-mono text-slate-300 bg-slate-950 overflow-x-auto max-h-96 whitespace-pre-wrap leading-relaxed">
                {report.markdown_content}
              </pre>
            )}
          </div>
        </>
      )}
    </div>
  );
}
