"use client";

import React, { useEffect, useState } from "react";
import { 
  TrendingUp, 
  TrendingDown,
  Layers, 
  Building2, 
  Clock, 
  Activity, 
  ShieldAlert, 
  BarChart2, 
  RefreshCw,
  Search
} from "lucide-react";
import { api } from "@/lib/api";
import { Stock } from "@/lib/types";

export default function MarketPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [sectors, setSectors] = useState<any[]>([]);
  const [marketStatus, setMarketStatus] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);
  const [selectedStock, setSelectedStock] = useState<string>("RELIANCE");
  const [indicators, setIndicators] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingIndicators, setLoadingIndicators] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [stocksRes, sectorsRes, statusRes, overviewRes] = await Promise.all([
          api.getStocks(),
          api.getSectors(),
          api.getMarketStatus().catch(() => null),
          api.getMarketOverview().catch(() => null),
        ]);
        if (stocksRes?.data) setStocks(stocksRes.data);
        if (sectorsRes?.data) setSectors(sectorsRes.data);
        if (statusRes?.data) setMarketStatus(statusRes.data);
        if (overviewRes?.data) setOverview(overviewRes.data);
      } catch (err) {
        console.error("Market initial data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  useEffect(() => {
    async function loadStockIndicators() {
      if (!selectedStock) return;
      setLoadingIndicators(true);
      try {
        const res = await api.getMarketIndicators(selectedStock);
        if (res?.data) {
          setIndicators(res.data);
        }
      } catch (err) {
        console.error("Failed to load indicators for", selectedStock, err);
      } finally {
        setLoadingIndicators(false);
      }
    }
    loadStockIndicators();
  }, [selectedStock]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const [statusRes, overviewRes, indRes] = await Promise.all([
        api.getMarketStatus().catch(() => null),
        api.getMarketOverview().catch(() => null),
        api.refreshMarketSnapshot(selectedStock).catch(() => null),
      ]);
      if (statusRes?.data) setMarketStatus(statusRes.data);
      if (overviewRes?.data) setOverview(overviewRes.data);
      if (indRes?.data) setIndicators(indRes.data);
    } finally {
      setRefreshing(false);
    }
  };

  const getSessionBadge = () => {
    if (!marketStatus) return null;
    const session = marketStatus.session;
    if (session === "REGULAR") {
      return (
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          NSE OPEN (REGULAR SESSION)
        </span>
      );
    } else if (session === "PRE_OPEN") {
      return (
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          NSE PRE-OPEN DISCOVERY
        </span>
      );
    } else {
      return (
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
          <span className="w-2 h-2 rounded-full bg-slate-500" />
          NSE CLOSED ({marketStatus.session_description || "AFTER HOURS"})
        </span>
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Market Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Indian Stock Market &amp; Technical Engine
            </h2>
            {getSessionBadge()}
          </div>
          <p className="text-xs text-slate-400 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>IST Time: <strong className="text-slate-300">{marketStatus?.current_ist || "Calculating..."}</strong></span>
            <span>•</span>
            <span>Next: <strong className="text-slate-300">{marketStatus?.next_session || "Standard hours"}</strong></span>
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition self-start md:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh Live Data
        </button>
      </div>

      {/* Major Indian Benchmarks & Macro Ribbon */}
      {overview?.benchmarks && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {Object.entries(overview.benchmarks).map(([key, data]: [string, any]) => {
            const isPositive = (data?.change_pct ?? 0) >= 0;
            const names: Record<string, string> = {
              nifty50: "NIFTY 50",
              bank_nifty: "BANK NIFTY",
              crude_oil: "Crude Oil (WTI)",
              gold: "Gold Futures",
              usd_inr: "USD / INR",
            };
            return (
              <div key={key} className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-1">
                <div className="text-[11px] font-medium text-slate-400">{names[key] || key}</div>
                <div className="text-base font-bold text-white font-mono">
                  {key === "usd_inr" ? "₹" : key === "crude_oil" ? "$" : key === "gold" ? "$" : "₹"}
                  {data?.last_price?.toLocaleString("en-IN") || "--"}
                </div>
                <div className={`text-xs font-semibold flex items-center gap-1 ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                  {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  <span>{isPositive ? "+" : ""}{data?.change_pct?.toFixed(2)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Technical Indicators Inspector */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-emerald-400" />
              Technical Indicator &amp; Confirmation Inspector
            </h3>
            <p className="text-xs text-slate-400">
              Evaluates SMA (20, 50, 200), RSI-14, MACD, Camarilla Pivots, and Volatility confirmation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Select Stock:</label>
            <select
              value={selectedStock}
              onChange={(e) => setSelectedStock(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-emerald-500"
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.exchange_ticker} - {s.company_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loadingIndicators ? (
          <div className="py-12 text-center text-xs text-slate-500 animate-pulse">
            Calculating technical indicators for {selectedStock}...
          </div>
        ) : indicators ? (
          <div className="space-y-5">
            {/* Stock Overview Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-white font-mono">{selectedStock}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                    indicators.trend_bias === "BULLISH" 
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : indicators.trend_bias === "BEARISH"
                      ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}>
                    {indicators.trend_bias} BIAS
                  </span>
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  Volume: {indicators.volume?.toLocaleString("en-IN")} • Surge: {indicators.vol_surge_ratio}x
                </div>
              </div>

              <div className="text-right">
                <div className="text-xl font-bold font-mono text-white">
                  ₹{indicators.last_price?.toLocaleString("en-IN")}
                </div>
                <div className={`text-xs font-semibold ${indicators.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {indicators.change_pct >= 0 ? "+" : ""}{indicators.change} ({indicators.change_pct >= 0 ? "+" : ""}{indicators.change_pct}%)
                </div>
              </div>
            </div>

            {/* Indicator Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* RSI 14 Gauge */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">RSI (14-Period)</span>
                  <span className={`font-mono font-bold ${
                    indicators.rsi_14 > 70 ? "text-rose-400" : indicators.rsi_14 < 30 ? "text-blue-400" : "text-emerald-400"
                  }`}>
                    {indicators.rsi_14}
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden flex">
                  <div 
                    className={`h-full transition-all ${
                      indicators.rsi_14 > 70 ? "bg-rose-500" : indicators.rsi_14 < 30 ? "bg-blue-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, indicators.rsi_14))}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>30 Oversold</span>
                  <span>50 Neutral</span>
                  <span>70 Overbought</span>
                </div>
              </div>

              {/* MACD Status */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-xs text-slate-400 font-medium">MACD (12, 26, 9)</div>
                <div className="font-mono text-sm font-bold text-white">
                  Line: {indicators.macd}
                </div>
                <div className="flex justify-between text-[11px] font-mono">
                  <span className="text-slate-400">Signal: {indicators.macd_signal}</span>
                  <span className={indicators.macd_hist >= 0 ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                    Hist: {indicators.macd_hist >= 0 ? "+" : ""}{indicators.macd_hist}
                  </span>
                </div>
              </div>

              {/* Volatility & ATR */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-xs text-slate-400 font-medium">ATR &amp; Volatility</div>
                <div className="font-mono text-sm font-bold text-white">
                  ATR (14): ₹{indicators.atr_14 || "--"}
                </div>
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Annualized Vol:</span>
                  <span className="text-slate-200 font-mono font-semibold">{indicators.volatility}%</span>
                </div>
              </div>

              {/* VWAP & Gap % */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-xs text-slate-400 font-medium">VWAP &amp; Gap</div>
                <div className="font-mono text-sm font-bold text-white">
                  VWAP: ₹{indicators.vwap || "--"}
                </div>
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Session Gap:</span>
                  <span className={`font-mono font-semibold ${indicators.gap_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {indicators.gap_pct >= 0 ? "+" : ""}{indicators.gap_pct}%
                  </span>
                </div>
              </div>
            </div>

            {/* Moving Averages Matrix & Pivot Points */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Moving Averages */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="text-xs font-bold text-slate-200">Moving Average Alignment</div>
                <div className="space-y-2 text-xs">
                  {[
                    { label: "SMA 20 (Short-Term)", val: indicators.sma_20 },
                    { label: "EMA 20 (Exponential)", val: indicators.ema_20 },
                    { label: "SMA 50 (Intermediate)", val: indicators.sma_50 },
                    { label: "SMA 200 (Long-Term)", val: indicators.sma_200 },
                  ].map((ma) => {
                    const isAbove = indicators.last_price >= (ma.val ?? 0);
                    return (
                      <div key={ma.label} className="flex justify-between items-center p-2 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-400">{ma.label}</span>
                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-slate-200">₹{ma.val ?? "--"}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                            isAbove ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                          }`}>
                            {isAbove ? "ABOVE" : "BELOW"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Pivot Points */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="text-xs font-bold text-slate-200">Support &amp; Resistance Pivots</div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Classic Pivots</div>
                    <div className="flex justify-between text-slate-300">
                      <span>R2:</span> <span className="text-rose-400 font-semibold">₹{indicators.pivot_levels?.r2}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>R1:</span> <span className="text-rose-300 font-semibold">₹{indicators.pivot_levels?.r1}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Pivot (P):</span> <span className="text-amber-300 font-semibold">₹{indicators.pivot_levels?.pivot}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>S1:</span> <span className="text-emerald-300 font-semibold">₹{indicators.pivot_levels?.s1}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>S2:</span> <span className="text-emerald-400 font-semibold">₹{indicators.pivot_levels?.s2}</span>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Camarilla Levels</div>
                    <div className="flex justify-between text-slate-300">
                      <span>R4 (Breakout):</span> <span className="text-rose-400 font-semibold">₹{indicators.pivot_levels?.cam_r4}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>R3 (Reversal):</span> <span className="text-rose-300 font-semibold">₹{indicators.pivot_levels?.cam_r3}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>S3 (Reversal):</span> <span className="text-emerald-300 font-semibold">₹{indicators.pivot_levels?.cam_s3}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>S4 (Breakout):</span> <span className="text-emerald-400 font-semibold">₹{indicators.pivot_levels?.cam_s4}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-500">
            Select a stock to view its technical indicator calculations.
          </div>
        )}
      </div>

      {/* Sector Impact Matrix */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          Configurable Sector Sensitivity Matrix
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {sectors.map((sec) => (
            <div key={sec.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-2">
              <div className="font-semibold text-white">{sec.name}</div>
              <p className="text-slate-400 text-[11px]">{sec.description}</p>
              {sec.sensitivities && (
                <div className="pt-2 border-t border-slate-800/80 space-y-1">
                  {Object.entries(sec.sensitivities).map(([k, v]) => (
                    <div key={k} className="flex justify-between items-center text-[10px]">
                      <span className="text-slate-500 font-mono">{k}</span>
                      <span className="font-semibold text-slate-300">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Tracked Indian Stocks */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Building2 className="w-4 h-4 text-blue-400" />
          Tracked Indian Equities ({stocks.length})
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Ticker</th>
                <th className="p-3">Company Name</th>
                <th className="p-3">Sector</th>
                <th className="p-3">NIFTY 50</th>
                <th className="p-3">Bank NIFTY</th>
                <th className="p-3">Cap Tier</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {stocks.map((stk) => (
                <tr key={stk.id} className="hover:bg-slate-800/40 transition">
                  <td className="p-3 font-mono font-semibold text-white">{stk.exchange_ticker}</td>
                  <td className="p-3">{stk.company_name}</td>
                  <td className="p-3 text-slate-400">{stk.sector?.name || "General"}</td>
                  <td className="p-3">
                    {stk.is_nifty50 ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium">YES</span>
                    ) : "No"}
                  </td>
                  <td className="p-3">
                    {stk.is_bank_nifty ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-medium">YES</span>
                    ) : "No"}
                  </td>
                  <td className="p-3 text-slate-400">{stk.market_cap_tier}</td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => setSelectedStock(stk.symbol)}
                      className="text-[11px] px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                    >
                      Inspect Technicals
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
