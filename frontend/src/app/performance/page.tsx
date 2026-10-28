"use client";

import React, { useEffect, useState } from "react";
import { BarChart3, TrendingUp, CheckCircle, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { PaperTradingMetrics, PaperTrade } from "@/lib/types";

export default function PerformancePage() {
  const [metrics, setMetrics] = useState<PaperTradingMetrics | null>(null);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [predictionSummary, setPredictionSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [metRes, tradesRes, predRes] = await Promise.allSettled([
          api.getPaperMetrics(),
          api.getPaperTrades(),
          api.getPredictionSummary(),
        ]);
        if (metRes.status === "fulfilled" && metRes.value?.data) setMetrics(metRes.value.data);
        if (tradesRes.status === "fulfilled" && tradesRes.value?.items) setTrades(tradesRes.value.items);
        if (predRes.status === "fulfilled" && predRes.value?.data) setPredictionSummary(predRes.value.data);
      } catch (e) {
        console.error("Performance load error:", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-emerald-400" />
          Paper-Trading &amp; Prediction Calibration Performance
        </h2>
        <p className="text-xs text-slate-400">
          Transparent algorithmic tracking comparing predicted direction vs actual subsequent price movement.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-xs text-slate-400">Directional Accuracy</div>
          <div className="mt-2 text-2xl font-bold text-white">
            {predictionSummary?.directional_accuracy_pct ? `${predictionSummary.directional_accuracy_pct}%` : "0.0%"}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {predictionSummary?.total_evaluated_predictions || 0} evaluated predictions
          </div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-xs text-slate-400">Simulated Win Rate</div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            {metrics?.win_rate_pct ? `${metrics.win_rate_pct}%` : "0.0%"}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {metrics?.winning_trades || 0}W / {metrics?.losing_trades || 0}L
          </div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-xs text-slate-400">Profit Factor</div>
          <div className="mt-2 text-2xl font-bold text-white">
            {metrics?.profit_factor || 1.0}
          </div>
          <div className="mt-1 text-xs text-slate-400">Gross Profit / Gross Loss</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-xs text-slate-400">Total Simulated P&amp;L</div>
          <div className={`mt-2 text-2xl font-bold ${Number(metrics?.total_realized_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            ₹{metrics?.total_realized_pnl?.toLocaleString("en-IN") || "0"}
          </div>
          <div className="mt-1 text-xs text-slate-400">Virtual paper capital</div>
        </div>
      </div>

      {/* Historical Paper Trades Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-base font-bold text-white">Executed Paper Trades</h3>

        {trades.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No paper trades recorded yet. Virtual positions are automatically created as high-confidence signals trigger.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Symbol</th>
                  <th className="p-3">Direction</th>
                  <th className="p-3">Entry Price</th>
                  <th className="p-3">Current/Exit</th>
                  <th className="p-3">Stop Loss</th>
                  <th className="p-3">Target</th>
                  <th className="p-3">Realized P&amp;L</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
                {trades.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-3 font-semibold text-white">{t.symbol}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${t.direction === "BUY" ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"}`}>
                        {t.direction}
                      </span>
                    </td>
                    <td className="p-3">₹{t.entry_price}</td>
                    <td className="p-3">₹{t.exit_price || t.current_price}</td>
                    <td className="p-3 text-rose-400">₹{t.stop_loss}</td>
                    <td className="p-3 text-emerald-400">₹{t.target_1}</td>
                    <td className={`p-3 font-semibold ${t.realized_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      ₹{t.realized_pnl}
                    </td>
                    <td className="p-3">
                      <span className="text-[10px] uppercase font-sans px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
