"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Play,
  Shield,
  Layers,
  Award,
  Zap,
  Target,
  ChevronRight,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  PaperTradingMetrics,
  PaperTrade,
  PredictionSummary,
  PredictionResultItem,
  BacktestResult,
} from "@/lib/types";

export default function PerformancePage() {
  const [metrics, setMetrics] = useState<PaperTradingMetrics | null>(null);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [summary, setSummary] = useState<PredictionSummary | null>(null);
  const [predictions, setPredictions] = useState<PredictionResultItem[]>([]);
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);

  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [backtesting, setBacktesting] = useState(false);
  const [backtestPeriod, setBacktestPeriod] = useState<number>(60);
  const [activeTab, setActiveTab] = useState<"predictions" | "paper_trades">("predictions");
  const [notification, setNotification] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      const [metRes, tradesRes, sumRes, predRes] = await Promise.allSettled([
        api.getPaperMetrics(),
        api.getPaperTrades(),
        api.getPredictionSummary(),
        api.getPredictionEvaluations(1),
      ]);

      if (metRes.status === "fulfilled" && metRes.value?.data) setMetrics(metRes.value.data);
      if (tradesRes.status === "fulfilled" && tradesRes.value?.items) setTrades(tradesRes.value.items);
      if (sumRes.status === "fulfilled" && sumRes.value?.data) setSummary(sumRes.value.data);
      if (predRes.status === "fulfilled" && predRes.value?.items) setPredictions(predRes.value.items);
    } catch (e) {
      console.error("Performance load error:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleEvaluateNow() {
    try {
      setEvaluating(true);
      const res = await api.triggerEvaluation(true);
      if (res?.data) {
        setNotification(
          `Evaluated ${res.data.evaluated_count} predictions. Realized ${res.data.accuracy_pct}% directional accuracy!`
        );
        await loadData();
      }
    } catch (e) {
      console.error("Evaluation error:", e);
    } finally {
      setEvaluating(false);
      setTimeout(() => setNotification(null), 5000);
    }
  }

  async function handleRunBacktest() {
    try {
      setBacktesting(true);
      const res = await api.runBacktest(undefined, backtestPeriod);
      if (res?.data) {
        setBacktest(res.data);
        setNotification(`Backtest completed across ${res.data.total_trades_simulated} simulated trades.`);
      }
    } catch (e) {
      console.error("Backtest error:", e);
    } finally {
      setBacktesting(false);
      setTimeout(() => setNotification(null), 5000);
    }
  }

  const brierScore = summary?.brier_score ?? 0.25;
  const isBrierCalibrated = brierScore < 0.20;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
              <Award className="w-3.5 h-3.5" />
              VERIFIABLE ALGORITHMIC CALIBRATION
            </span>
            <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Post-Market Settlement Verification
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Performance, Calibration &amp; Backtesting Engine
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Mathematical calibration metrics comparing predicted price direction against actual settlement
            outcomes without look-ahead bias. Incorporating Brier calibration and rolling multi-asset backtests.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleEvaluateNow}
            disabled={evaluating}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs rounded-lg border border-slate-700 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${evaluating ? "animate-spin text-emerald-400" : ""}`} />
            <span>{evaluating ? "Evaluating..." : "Evaluate Pending"}</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className="bg-emerald-950/40 border border-emerald-500/40 rounded-xl p-3.5 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Directional Accuracy */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Directional Accuracy</div>
          <div className="mt-2 text-2xl font-bold text-white font-mono">
            {summary?.directional_accuracy_pct ? `${summary.directional_accuracy_pct}%` : "0.0%"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            {summary?.correct_direction_count || 0} of {summary?.total_evaluated_predictions || 0} correct
          </div>
        </div>

        {/* Brier Calibration Score */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400 uppercase font-semibold flex items-center justify-between">
            <span>Brier Score</span>
            <Info className="w-3 h-3 text-slate-500" />
          </div>
          <div className={`mt-2 text-2xl font-bold font-mono ${isBrierCalibrated ? "text-emerald-400" : "text-amber-300"}`}>
            {summary?.brier_score !== undefined ? summary.brier_score.toFixed(3) : "0.250"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400 truncate">
            {summary?.calibration_grade || "Calibrated"}
          </div>
        </div>

        {/* Win Rate on Actionable Signals */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Simulated Win Rate</div>
          <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
            {summary?.win_rate_pct ? `${summary.win_rate_pct}%` : (metrics?.win_rate_pct ? `${metrics.win_rate_pct}%` : "0.0%")}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            BUY &amp; SELL Setups
          </div>
        </div>

        {/* Profit Factor */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Profit Factor</div>
          <div className="mt-2 text-2xl font-bold text-white font-mono">
            {summary?.profit_factor || metrics?.profit_factor || 1.0}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Gross Win / Loss</div>
        </div>

        {/* Average Trade Return */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Average Return</div>
          <div className={`mt-2 text-2xl font-bold font-mono ${Number(summary?.average_return_pct || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {summary?.average_return_pct !== undefined ? `${summary.average_return_pct > 0 ? "+" : ""}${summary.average_return_pct}%` : "0.0%"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Per evaluated setup</div>
        </div>

        {/* Realized Paper P&L */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] text-slate-400 uppercase font-semibold">Paper Portfolio P&amp;L</div>
          <div className={`mt-2 text-2xl font-bold font-mono ${Number(metrics?.total_realized_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            ₹{metrics?.total_realized_pnl?.toLocaleString("en-IN") || "0"}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Virtual Capital (0% real)</div>
        </div>
      </div>

      {/* STRATEGY BACKTESTING SECTION */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Historical Strategy Backtesting Engine</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Simulates technical breakout and mean-reversion setups across historical daily candles with rolling indicators and zero look-ahead bias.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={backtestPeriod}
              onChange={(e) => setBacktestPeriod(Number(e.target.value))}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none"
            >
              <option value={30}>30 Days Lookback</option>
              <option value={60}>60 Days Lookback</option>
              <option value={90}>90 Days Lookback</option>
            </select>

            <button
              onClick={handleRunBacktest}
              disabled={backtesting}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded-lg transition"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${backtesting ? "animate-spin" : ""}`} />
              <span>{backtesting ? "Simulating..." : "Run Backtest"}</span>
            </button>
          </div>
        </div>

        {backtest && (
          <div className="space-y-4 pt-1">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Simulated Trades</div>
                <div className="text-lg font-bold text-white font-mono mt-1">{backtest.total_trades_simulated}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Simulated Win Rate</div>
                <div className="text-lg font-bold text-emerald-400 font-mono mt-1">{backtest.win_rate_pct}%</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Profit Factor</div>
                <div className="text-lg font-bold text-white font-mono mt-1">{backtest.profit_factor}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Max Drawdown</div>
                <div className="text-lg font-bold text-rose-400 font-mono mt-1">{backtest.max_drawdown_pct}%</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Cumulative Return</div>
                <div className="text-lg font-bold text-emerald-400 font-mono mt-1">+{backtest.cumulative_return_pct}%</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Simulated Brier Score</div>
                <div className="text-lg font-bold text-blue-400 font-mono mt-1">{backtest.brier_score}</div>
              </div>
            </div>

            {/* Sample Backtest Trades Table */}
            {backtest.sample_trades?.length > 0 && (
              <div className="border border-slate-800 rounded-lg overflow-hidden">
                <div className="bg-slate-950 px-4 py-2 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Recent Simulated Trades ({backtest.sample_trades.length})</span>
                  <span className="text-[11px] text-slate-500">Zero look-ahead forward verification</span>
                </div>
                <div className="overflow-x-auto max-h-60">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
                      <tr>
                        <th className="p-2.5">Date</th>
                        <th className="p-2.5">Symbol</th>
                        <th className="p-2.5">Direction</th>
                        <th className="p-2.5">Entry</th>
                        <th className="p-2.5">Exit</th>
                        <th className="p-2.5">Return (%)</th>
                        <th className="p-2.5">Exit Reason</th>
                        <th className="p-2.5">Outcome</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {backtest.sample_trades.map((t, i) => (
                        <tr key={i} className="hover:bg-slate-800/40 transition">
                          <td className="p-2.5 text-slate-400">{t.date}</td>
                          <td className="p-2.5 font-bold text-white">{t.symbol}</td>
                          <td className="p-2.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${t.direction === "BUY" ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"}`}>
                              {t.direction}
                            </span>
                          </td>
                          <td className="p-2.5">₹{t.entry_price}</td>
                          <td className="p-2.5">₹{t.exit_price}</td>
                          <td className={`p-2.5 font-bold ${t.return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {t.return_pct > 0 ? `+${t.return_pct}%` : `${t.return_pct}%`}
                          </td>
                          <td className="p-2.5 text-[10px] text-slate-400">{t.status}</td>
                          <td className="p-2.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${t.is_win ? "text-emerald-400 bg-emerald-500/20" : "text-rose-400 bg-rose-500/20"}`}>
                              {t.is_win ? "WIN" : "LOSS"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* CONFIDENCE CALIBRATION & SECTOR ACCURACY GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confidence vs Accuracy Calibration Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-400" />
                Confidence vs. Realized Accuracy
              </h3>
              <p className="text-xs text-slate-400">
                Brier score calibration: Model confidence must match realized statistical frequency.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {summary?.confidence_calibration_tiers?.length ? (
              summary.confidence_calibration_tiers.map((tier, idx) => {
                const diff = tier.realized_accuracy_pct - tier.predicted_avg_confidence;
                return (
                  <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-white">{tier.tier_label} Confidence</span>
                      <span className="text-slate-400 font-mono text-[11px]">{tier.sample_count} sample(s)</span>
                    </div>

                    <div className="flex items-center gap-3 text-xs font-mono">
                      <div className="flex-1 space-y-1">
                        <div className="flex justify-between text-[11px] text-slate-400">
                          <span>Target: {tier.predicted_avg_confidence}%</span>
                          <span className={tier.realized_accuracy_pct >= tier.predicted_avg_confidence ? "text-emerald-400 font-bold" : "text-amber-300 font-bold"}>
                            Realized: {tier.realized_accuracy_pct}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden flex">
                          <div
                            className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, tier.realized_accuracy_pct)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-8 text-center text-xs text-slate-500">
                Awaiting evaluated signals to compute confidence calibration curve.
              </div>
            )}
          </div>
        </div>

        {/* Accuracy by Sector */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              Directional Accuracy by Industrial Sector
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated performance segregated across key Indian economic sectors.
            </p>
          </div>

          <div className="space-y-2.5">
            {summary?.sector_accuracy?.length ? (
              summary.sector_accuracy.map((sec, idx) => (
                <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <span className="font-semibold text-white">{sec.sector}</span>
                    <div className="text-[11px] text-slate-500">{sec.sample_count} evaluated signal(s)</div>
                  </div>
                  <div className="text-right">
                    <span className={`text-sm font-bold font-mono ${sec.accuracy_pct >= 60 ? "text-emerald-400" : "text-amber-300"}`}>
                      {sec.accuracy_pct}%
                    </span>
                    <div className="text-[10px] text-slate-400">Accuracy</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-500">
                Awaiting evaluated sector data.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* DETAIL LOG TABLES: TABS FOR PREDICTION LOG VS EXECUTED PAPER TRADES */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab("predictions")}
              className={`text-xs font-semibold pb-1 border-b-2 transition ${
                activeTab === "predictions"
                  ? "border-emerald-400 text-white font-bold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Evaluated Signals &amp; Predictions ({predictions.length})
            </button>
            <button
              onClick={() => setActiveTab("paper_trades")}
              className={`text-xs font-semibold pb-1 border-b-2 transition ${
                activeTab === "paper_trades"
                  ? "border-emerald-400 text-white font-bold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Executed Paper Positions ({trades.length})
            </button>
          </div>

          <span className="text-[11px] text-slate-500 font-mono">
            {activeTab === "predictions" ? "Verification log" : "Simulated positions"}
          </span>
        </div>

        {activeTab === "predictions" ? (
          predictions.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No predictions logged yet. Predictions are automatically registered whenever signals are generated.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3">Symbol</th>
                    <th className="p-3">Horizon</th>
                    <th className="p-3">Predicted</th>
                    <th className="p-3">Confidence</th>
                    <th className="p-3">Price at Call</th>
                    <th className="p-3">Evaluated Price</th>
                    <th className="p-3">Change (%)</th>
                    <th className="p-3">Outcome</th>
                    <th className="p-3">Verification Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
                  {predictions.map((p) => {
                    const isCorrect = p.is_direction_correct;
                    const isPending = !p.is_evaluated;
                    return (
                      <tr key={p.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-semibold text-white">{p.symbol}</td>
                        <td className="p-3 text-slate-400 text-[11px] font-sans">{p.evaluation_horizon}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              p.predicted_direction === "BUY"
                                ? "text-emerald-400 bg-emerald-500/10"
                                : p.predicted_direction === "SELL"
                                ? "text-rose-400 bg-rose-500/10"
                                : "text-slate-400 bg-slate-800"
                            }`}
                          >
                            {p.predicted_direction}
                          </span>
                        </td>
                        <td className="p-3 text-white">{p.predicted_confidence}%</td>
                        <td className="p-3">₹{p.price_at_prediction}</td>
                        <td className="p-3">
                          {p.actual_price_at_eval ? `₹${p.actual_price_at_eval}` : "—"}
                        </td>
                        <td
                          className={`p-3 font-bold ${
                            Number(p.actual_price_change_pct || 0) >= 0
                              ? "text-emerald-400"
                              : "text-rose-400"
                          }`}
                        >
                          {p.actual_price_change_pct !== null && p.actual_price_change_pct !== undefined
                            ? `${p.actual_price_change_pct > 0 ? "+" : ""}${p.actual_price_change_pct}%`
                            : "—"}
                        </td>
                        <td className="p-3">
                          {isPending ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-300 border border-amber-500/20 font-sans">
                              PENDING
                            </span>
                          ) : isCorrect ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-sans flex items-center gap-1 w-fit">
                              <CheckCircle2 className="w-3 h-3" />
                              CORRECT
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/30 font-sans flex items-center gap-1 w-fit">
                              <XCircle className="w-3 h-3" />
                              INCORRECT
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-[11px] text-slate-400 font-sans max-w-xs truncate" title={p.evaluation_notes || ""}>
                          {p.evaluation_notes || "Scheduled for post-market evaluation."}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        ) : (
          trades.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No paper trades recorded yet. Virtual positions are created automatically or via 1-click execution.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800 text-[10px]">
                  <tr>
                    <th className="p-3">Symbol</th>
                    <th className="p-3">Direction</th>
                    <th className="p-3">Entry Price</th>
                    <th className="p-3">Current/Exit</th>
                    <th className="p-3">Stop Loss</th>
                    <th className="p-3">Target 1</th>
                    <th className="p-3">Realized P&amp;L</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
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
          )
        )}
      </div>
    </div>
  );
}
