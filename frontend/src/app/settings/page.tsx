"use client";

import React, { useEffect, useState } from "react";
import { Sliders, Save, Check, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [weights, setWeights] = useState({
    weight_news: 0.35,
    weight_technical: 0.30,
    weight_volume: 0.15,
    weight_market: 0.10,
    weight_sector: 0.10,
  });
  const [saved, setSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const currentTotal = Math.round(
    (weights.weight_news +
      weights.weight_technical +
      weights.weight_volume +
      weights.weight_market +
      weights.weight_sector) *
      100
  );

  const handleSave = async () => {
    setErrorMsg("");
    setSaved(false);
    if (currentTotal !== 100) {
      setErrorMsg(`Weights must sum to 100% (current sum: ${currentTotal}%)`);
      return;
    }
    try {
      await api.updateWeights(weights);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update weights");
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Sliders className="w-5 h-5 text-emerald-400" />
          Signal Engine Scoring Weights &amp; Rules
        </h2>
        <p className="text-xs text-slate-400">
          Fine-tune the relative influence of factors in the deterministic signal generator. Weights must sum to 1.0 (100%).
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <span className="text-sm font-semibold text-white">Weight Allocation Total</span>
          <span className={`text-sm font-mono font-bold ${currentTotal === 100 ? "text-emerald-400" : "text-rose-400"}`}>
            {currentTotal}% / 100%
          </span>
        </div>

        <div className="space-y-4 text-xs">
          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span>News &amp; Sentiment Impact Weight</span>
              <span className="font-mono font-semibold">{Math.round(weights.weight_news * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.weight_news}
              onChange={(e) => setWeights({ ...weights, weight_news: parseFloat(e.target.value) })}
              className="w-full accent-emerald-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span>Technical Indicators (SMA, EMA, RSI, MACD, VWAP) Weight</span>
              <span className="font-mono font-semibold">{Math.round(weights.weight_technical * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.weight_technical}
              onChange={(e) => setWeights({ ...weights, weight_technical: parseFloat(e.target.value) })}
              className="w-full accent-emerald-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span>Volume &amp; Volatility (ATR, Volume Avg) Weight</span>
              <span className="font-mono font-semibold">{Math.round(weights.weight_volume * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.weight_volume}
              onChange={(e) => setWeights({ ...weights, weight_volume: parseFloat(e.target.value) })}
              className="w-full accent-emerald-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span>Broad Market (NIFTY 50) Trend Weight</span>
              <span className="font-mono font-semibold">{Math.round(weights.weight_market * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.weight_market}
              onChange={(e) => setWeights({ ...weights, weight_market: parseFloat(e.target.value) })}
              className="w-full accent-emerald-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-slate-300 mb-1">
              <span>Sector Trend &amp; Sensitivity Matrix Weight</span>
              <span className="font-mono font-semibold">{Math.round(weights.weight_sector * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.weight_sector}
              onChange={(e) => setWeights({ ...weights, weight_sector: parseFloat(e.target.value) })}
              className="w-full accent-emerald-500"
            />
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {saved && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <Check className="w-4 h-4 shrink-0" />
            <span>Settings saved successfully!</span>
          </div>
        )}

        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
        >
          <Save className="w-4 h-4" />
          <span>Save Scoring Configuration</span>
        </button>
      </div>
    </div>
  );
}
