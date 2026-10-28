"use client";

import React, { useEffect, useState } from "react";
import { Compass, RefreshCw, AlertCircle, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { TradingSignal } from "@/lib/types";

export default function SignalsPage() {
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [directionFilter, setDirectionFilter] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadSignals() {
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
    }
    loadSignals();
  }, [directionFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Compass className="w-5 h-5 text-emerald-400" />
            Deterministic Signal Engine
          </h2>
          <p className="text-xs text-slate-400">
            Multi-factor synthesis: News (35%), Technical (30%), Volume (15%), Market (10%), Sector (10%).
          </p>
        </div>

        {/* Direction Filter Tabs */}
        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs">
          {["", "BUY", "SELL", "WATCH", "NO_TRADE"].map((dir) => (
            <button
              key={dir}
              onClick={() => setDirectionFilter(dir)}
              className={`px-3 py-1 rounded font-medium transition ${
                directionFilter === dir
                  ? "bg-slate-800 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {dir === "" ? "ALL" : dir.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">Evaluating market setups...</div>
      ) : signals.length === 0 ? (
        <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-sm">
          No signals found matching criteria. The engine enforces &quot;NO TRADE&quot; when technical or news criteria conflict.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {signals.map((sig) => {
            const isBuy = sig.direction === "BUY";
            const isSell = sig.direction === "SELL";
            const isWatch = sig.direction === "WATCH";

            return (
              <div
                key={sig.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      {sig.symbol}
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded border ${
                          isBuy
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : isSell
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {sig.direction}
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Confidence: {sig.confidence}% | R:R {sig.risk_reward}</p>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-500 block">Entry Zone</span>
                    <span className="text-xs font-mono font-semibold text-slate-200">{sig.entry_zone}</span>
                  </div>
                </div>

                {/* SL / Target Grid */}
                <div className="grid grid-cols-3 gap-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 text-xs text-center font-mono">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Stop Loss</span>
                    <span className="text-rose-400 font-semibold">{sig.stop_loss ? `₹${sig.stop_loss}` : "—"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Target 1</span>
                    <span className="text-emerald-400 font-semibold">{sig.target_1 ? `₹${sig.target_1}` : "—"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Target 2</span>
                    <span className="text-emerald-400 font-semibold">{sig.target_2 ? `₹${sig.target_2}` : "—"}</span>
                  </div>
                </div>

                {/* Timing Windows */}
                <div className="text-xs text-slate-400 space-y-1">
                  <div>
                    <strong className="text-slate-300">Entry Window:</strong> {sig.entry_time_window}
                  </div>
                  <div>
                    <strong className="text-slate-300">Exit Window:</strong> {sig.exit_time_window}
                  </div>
                </div>

                {/* Invalidation Condition */}
                <div className="text-xs bg-amber-950/20 border border-amber-900/30 rounded p-2 text-amber-200/80">
                  <strong className="text-amber-400">Invalidated If:</strong> {sig.invalidated_if}
                </div>

                {/* Reasoning */}
                <p className="text-xs text-slate-400 leading-relaxed border-t border-slate-800/60 pt-2">
                  {sig.reasoning}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
