"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  Zap,
  Clock,
  ExternalLink,
  ChevronRight,
  FileText,
} from "lucide-react";
import { api } from "@/lib/api";
import { TradingSignal, PaperTradingMetrics, DailyReport } from "@/lib/types";

export default function DashboardPage() {
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [metrics, setMetrics] = useState<PaperTradingMetrics | null>(null);
  const [preMarketReport, setPreMarketReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [sigRes, metRes, repRes] = await Promise.allSettled([
          api.getTopSignals(),
          api.getPaperMetrics(),
          api.getLatestPreMarketReport(),
        ]);
        if (sigRes.status === "fulfilled" && sigRes.value?.data) {
          setSignals(sigRes.value.data);
        }
        if (metRes.status === "fulfilled" && metRes.value?.data) {
          setMetrics(metRes.value.data);
        }
        if (repRes.status === "fulfilled" && repRes.value?.data) {
          setPreMarketReport(repRes.value.data);
        }
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Welcome & Pre-Market Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold mb-3">
            <Zap className="w-3.5 h-3.5" />
            <span>INDIAN MARKET INTELLIGENCE ENGINE</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            NSE & BSE Algorithmic Decision Support
          </h2>
          <p className="text-slate-400 text-sm mt-1 leading-relaxed">
            Multi-factor decision engine integrating 5-minute global financial news, macro sector mapping,
            and technical momentum. Operating in simulated paper-trading mode.
          </p>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Actionable Signals</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {signals.filter((s) => s.direction === "BUY" || s.direction === "SELL").length}
          </div>
          <div className="mt-1 text-xs text-emerald-400 flex items-center gap-1">
            <span>High confidence setups</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Paper Trading Win Rate</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {metrics?.win_rate_pct ? `${metrics.win_rate_pct}%` : "0.0%"}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            <span>{metrics?.closed_trades || 0} evaluated paper trades</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Realized Paper P&L</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className={`mt-2 text-2xl font-bold ${Number(metrics?.total_realized_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            ₹{metrics?.total_realized_pnl?.toLocaleString("en-IN") || "0"}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            <span>Virtual simulated capital</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Execution Mode</span>
            <Shield className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-lg font-bold text-amber-300">
            PAPER TRADING
          </div>
          <div className="mt-1 text-xs text-slate-400">
            <span>Real orders disabled</span>
          </div>
        </div>
      </div>

      {/* Main Content: Signals & NIFTY Outlook */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Signals Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Top Actionable Setups</h3>
                <p className="text-xs text-slate-400">Ranked by combined news + technical + sector score</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono">
                {signals.length} Active
              </span>
            </div>

            {signals.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                No active signals generated yet. Click &quot;Run Cycle&quot; in the header or check Signal Engine.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-3">Symbol</th>
                      <th className="p-3">Direction</th>
                      <th className="p-3">Entry Zone</th>
                      <th className="p-3">Stop Loss</th>
                      <th className="p-3">Target</th>
                      <th className="p-3">R:R</th>
                      <th className="p-3">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {signals.map((sig) => (
                      <tr key={sig.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-semibold text-white">{sig.symbol}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded font-semibold text-[11px] ${
                              sig.direction === "BUY"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : sig.direction === "SELL"
                                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {sig.direction}
                          </span>
                        </td>
                        <td className="p-3 font-mono">{sig.entry_zone}</td>
                        <td className="p-3 font-mono text-rose-400">{sig.stop_loss ? `₹${sig.stop_loss}` : "—"}</td>
                        <td className="p-3 font-mono text-emerald-400">{sig.target_1 ? `₹${sig.target_1}` : "—"}</td>
                        <td className="p-3 font-mono">{sig.risk_reward}</td>
                        <td className="p-3 font-semibold text-white">{sig.confidence}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* NIFTY Pre-Open Outlook (1 Col) */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-base font-bold text-white mb-1">Indian Market Pre-Open Outlook</h3>
            <p className="text-xs text-slate-400 mb-4">Latest macro & index synthesis</p>

            {preMarketReport ? (
              <div className="space-y-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-white">NIFTY 50</span>
                    <span className="text-emerald-400 font-bold uppercase">
                      {preMarketReport.nifty_outlook?.sentiment || "NEUTRAL"}
                    </span>
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    Levels: {preMarketReport.nifty_outlook?.levels || "24,700 - 25,000"}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-white">BANK NIFTY</span>
                    <span className="text-blue-400 font-bold uppercase">
                      {preMarketReport.bank_nifty_outlook?.sentiment || "NEUTRAL"}
                    </span>
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    Levels: {preMarketReport.bank_nifty_outlook?.levels || "51,900 - 52,800"}
                  </div>
                </div>

                <div className="text-slate-400 text-[11px] leading-relaxed">
                  <strong>Risk Watch:</strong> Crude oil fluctuations, US bond yields, and opening volatility buffer (09:15-09:30).
                </div>

                <Link
                  href="/reports"
                  className="flex items-center justify-center gap-1.5 w-full py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-lg font-semibold text-xs transition"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>View Full Pre-Market Report</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-center text-xs text-slate-500 space-y-3">
                <div>Pre-market report not generated yet for today.</div>
                <Link
                  href="/reports"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold rounded text-xs transition"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Open Reports Desk</span>
                </Link>
              </div>
            )}
          </div>

          <div className="bg-amber-950/20 border border-amber-600/30 rounded-xl p-4 text-xs text-amber-200/90 leading-relaxed">
            <div className="font-semibold text-amber-300 mb-1 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" />
              Trading Safety Notice
            </div>
            Signals require confirmation from market volume and price action. Never risk capital without strict position sizing and personal stop loss.
          </div>
        </div>
      </div>
    </div>
  );
}
