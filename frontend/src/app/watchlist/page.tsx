"use client";

import React, { useEffect, useState } from "react";
import { BookmarkCheck, AlertOctagon, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { TradingSignal } from "@/lib/types";

export default function WatchlistPage() {
  const [topSetups, setTopSetups] = useState<TradingSignal[]>([]);
  const [noTradeSetups, setNoTradeSetups] = useState<TradingSignal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadWatchlist() {
      try {
        const [topRes, noTradeRes] = await Promise.allSettled([
          api.getSignals("BUY"),
          api.getSignals("NO_TRADE"),
        ]);
        if (topRes.status === "fulfilled" && topRes.value?.items) {
          setTopSetups(topRes.value.items);
        }
        if (noTradeRes.status === "fulfilled" && noTradeRes.value?.items) {
          setNoTradeSetups(noTradeRes.value.items);
        }
      } catch (err) {
        console.error("Watchlist load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadWatchlist();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <BookmarkCheck className="w-5 h-5 text-emerald-400" />
          High-Probability &amp; No-Trade Watchlists
        </h2>
        <p className="text-xs text-slate-400">
          Ranked setups with favorable risk/reward vs setups actively blocked due to conflicting catalysts or excessive volatility.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Stock Watchlist */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Top Stock Setups (Confirmed Catalysts)
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
              {topSetups.length}
            </span>
          </div>

          {topSetups.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No top setups currently meeting strict multi-factor criteria.
            </div>
          ) : (
            <div className="space-y-3">
              {topSetups.map((s) => (
                <div key={s.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white">{s.symbol}</span>
                    <span className="text-emerald-400 font-mono font-semibold">R:R {s.risk_reward}</span>
                  </div>
                  <div className="text-slate-400">Zone: {s.entry_zone} | Target: ₹{s.target_1}</div>
                  <div className="text-slate-500 text-[11px]">{s.reasoning}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* No-Trade Watchlist */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-rose-400 flex items-center gap-2">
              <AlertOctagon className="w-4 h-4" />
              No-Trade Watchlist (Risk Prohibitive)
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 font-mono">
              {noTradeSetups.length}
            </span>
          </div>

          {noTradeSetups.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No high-risk conflicts logged today.
            </div>
          ) : (
            <div className="space-y-3">
              {noTradeSetups.map((s) => (
                <div key={s.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-300">{s.symbol}</span>
                    <span className="text-rose-400 font-semibold uppercase text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10">
                      NO TRADE
                    </span>
                  </div>
                  <div className="text-slate-400 text-[11px]">{s.reasoning}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
