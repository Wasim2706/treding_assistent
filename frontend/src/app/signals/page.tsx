"use client";

import React, { useEffect, useState } from "react";
import { 
  Compass, 
  RefreshCw, 
  AlertCircle, 
  ShieldAlert, 
  Play, 
  CheckCircle2, 
  Sliders,
  TrendingUp,
  TrendingDown,
  Eye,
  Ban
} from "lucide-react";
import { api } from "@/lib/api";
import { TradingSignal } from "@/lib/types";

export default function SignalsPage() {
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [directionFilter, setDirectionFilter] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [executingSignalId, setExecutingSignalId] = useState<number | null>(null);
  const [notification, setNotification] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  const loadSignals = async () => {
    setLoading(true);
    try {
      const res = await api.getSignals(directionFilter || undefined);
      if (res?.items) {
        setSignals(res.items);
      }
    } catch (e) {
      console.error("Failed loading signals:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSignals();
  }, [directionFilter]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await api.generateSignals();
      setNotification({
        msg: `Signal engine executed! Generated ${res?.data?.signals_generated || 0} setups.`,
        type: "success"
      });
      await loadSignals();
    } catch (err: any) {
      setNotification({
        msg: `Failed to trigger signal engine: ${err.message || "Unknown error"}`,
        type: "error"
      });
    } finally {
      setGenerating(false);
      setTimeout(() => setNotification(null), 4000);
    }
  };

  const handleExecutePaperTrade = async (signalId: number) => {
    setExecutingSignalId(signalId);
    try {
      await api.executePaperTradeFromSignal(signalId);
      setNotification({
        msg: `Virtual paper position opened with 2% risk capital sizing!`,
        type: "success"
      });
      await loadSignals();
    } catch (err: any) {
      setNotification({
        msg: `Execution error: ${err.message || "Could not open paper trade"}`,
        type: "error"
      });
    } finally {
      setExecutingSignalId(null);
      setTimeout(() => setNotification(null), 4000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div>
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white">Deterministic Multi-Factor Signal Engine</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Synthesizes News (35%), Technical Indicators (30%), Volume (15%), NIFTY Trend (10%), and Sector Sensitivity (10%).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? "animate-spin" : ""}`} />
            Run Signal Synthesis
          </button>
        </div>
      </div>

      {notification && (
        <div className={`p-3 rounded-lg text-xs font-medium border flex items-center gap-2 ${
          notification.type === "success" 
            ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" 
            : "bg-rose-500/10 text-rose-300 border-rose-500/30"
        }`}>
          {notification.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-1.5 text-xs">
          {["", "BUY", "SELL", "WATCH", "NO_TRADE"].map((dir) => (
            <button
              key={dir}
              onClick={() => setDirectionFilter(dir)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                directionFilter === dir
                  ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {dir === "" ? "ALL SIGNALS" : dir.replace("_", " ")}
            </button>
          ))}
        </div>

        <div className="text-xs text-slate-500">
          Total: <strong className="text-slate-300">{signals.length}</strong>
        </div>
      </div>

      {/* Signals Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs animate-pulse">
          Evaluating deterministic multi-factor setups...
        </div>
      ) : signals.length === 0 ? (
        <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <Ban className="w-8 h-8 text-slate-500 mx-auto" />
          <h4 className="text-sm font-semibold text-slate-300">No signals match current filter</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            The engine strictly defaults to &quot;NO TRADE&quot; when news and technical indicators conflict or data is incomplete.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {signals.map((sig) => {
            const isBuy = sig.direction === "BUY";
            const isSell = sig.direction === "SELL";
            const isWatch = sig.direction === "WATCH";
            const isActionable = (isBuy || isSell) && !sig.is_paper_traded;

            return (
              <div
                key={sig.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-slate-700 transition"
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-white font-mono">{sig.symbol}</span>
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded border uppercase ${
                          isBuy
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : isSell
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : isWatch
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {sig.direction}
                      </span>
                      {sig.is_paper_traded && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">
                          VIRTUAL TRADE ACTIVE
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 flex items-center gap-2">
                      <span>Composite: <strong className="text-white">{sig.composite_score}/100</strong></span>
                      <span>•</span>
                      <span>Confidence: <strong className="text-slate-300">{sig.confidence}%</strong></span>
                      <span>•</span>
                      <span>R:R: <strong className="text-slate-300">{sig.risk_reward}</strong></span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Entry Zone</span>
                    <span className="text-xs font-mono font-bold text-slate-200">{sig.entry_zone}</span>
                  </div>
                </div>

                {/* Score Breakdown Bar */}
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 space-y-1.5 text-[11px]">
                  <div className="flex justify-between text-slate-400">
                    <span>Factor Scores:</span>
                    <span className="font-mono text-slate-300">
                      News: {sig.news_score} | Tech: {sig.technical_score} | Vol: {sig.volume_score} | Mkt: {sig.market_score} | Sec: {sig.sector_score}
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden flex">
                    <div className="bg-blue-500 h-full" style={{ width: `${sig.news_score * 0.35}%` }} title="News 35%" />
                    <div className="bg-emerald-500 h-full" style={{ width: `${sig.technical_score * 0.30}%` }} title="Technical 30%" />
                    <div className="bg-purple-500 h-full" style={{ width: `${sig.volume_score * 0.15}%` }} title="Volume 15%" />
                    <div className="bg-amber-500 h-full" style={{ width: `${sig.market_score * 0.10}%` }} title="Market 10%" />
                    <div className="bg-cyan-500 h-full" style={{ width: `${sig.sector_score * 0.10}%` }} title="Sector 10%" />
                  </div>
                </div>

                {/* Target & Stop Loss Grid */}
                <div className="grid grid-cols-3 gap-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 text-xs text-center font-mono">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Stop Loss</span>
                    <span className="text-rose-400 font-semibold">{sig.stop_loss ? `₹${sig.stop_loss}` : "—"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Target 1</span>
                    <span className="text-emerald-400 font-semibold">{sig.target_1 ? `₹${sig.target_1}` : "—"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Target 2</span>
                    <span className="text-emerald-400 font-semibold">{sig.target_2 ? `₹${sig.target_2}` : "—"}</span>
                  </div>
                </div>

                {/* Execution Windows */}
                <div className="text-xs text-slate-400 space-y-1">
                  <div>
                    <span className="text-slate-500 font-medium">Entry Window:</span> <span className="text-slate-300">{sig.entry_time_window}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-medium">Exit Window:</span> <span className="text-slate-300">{sig.exit_time_window}</span>
                  </div>
                </div>

                {/* Invalidation Rules */}
                <div className="text-xs bg-amber-950/20 border border-amber-900/30 rounded p-2 text-amber-200/80">
                  <strong className="text-amber-400">Invalidated If:</strong> {sig.invalidated_if}
                </div>

                {/* Rationale */}
                <p className="text-xs text-slate-400 leading-relaxed border-t border-slate-800/60 pt-2">
                  {sig.reasoning}
                </p>

                {/* Action Button */}
                {isActionable && (
                  <div className="pt-2 border-t border-slate-800/80 flex justify-end">
                    <button
                      onClick={() => handleExecutePaperTrade(sig.id)}
                      disabled={executingSignalId === sig.id}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      {executingSignalId === sig.id ? "Opening Virtual Position..." : "Execute Virtual Trade (2% Risk)"}
                    </button>
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
