"use client";

import React, { useEffect, useState } from "react";
import { Sliders, Save, Check, AlertCircle, Shield, Key, DollarSign, Activity } from "lucide-react";
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

  // Security & AI Budget State
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [keySaved, setKeySaved] = useState(false);
  const [securityStatus, setSecurityStatus] = useState<any>(null);
  const [loadingSecurity, setLoadingSecurity] = useState(true);

  useEffect(() => {
    // Load stored API key if available
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("trading_admin_api_key") || "";
      setApiKeyInput(stored);
    }

    // Fetch live security & budget status
    api.getSecurityStatus()
      .then((res) => {
        if (res.data) setSecurityStatus(res.data);
      })
      .catch((err) => console.warn("Failed to load security status:", err))
      .finally(() => setLoadingSecurity(false));
  }, []);

  const handleSaveApiKey = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("trading_admin_api_key", apiKeyInput.trim());
      setKeySaved(true);
      setTimeout(() => setKeySaved(false), 3000);
    }
  };

  const handleClearApiKey = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("trading_admin_api_key");
      setApiKeyInput("");
      setKeySaved(true);
      setTimeout(() => setKeySaved(false), 3000);
    }
  };

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
          Engine Configuration &amp; Security Controls
        </h2>
        <p className="text-xs text-slate-400">
          Fine-tune deterministic multi-factor scoring weights, view real-time AI budget consumption, and manage API security credentials.
        </p>
      </div>

      {/* Security & AI Cost Tracker Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Security & Auth Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span>API Authentication</span>
          </div>
          <div className="text-sm font-bold text-white">
            {securityStatus?.auth_required ? (
              <span className="text-amber-400">Enforced (Key Required)</span>
            ) : (
              <span className="text-emerald-400">Open (Dev Mode)</span>
            )}
          </div>
          <p className="text-[10px] text-slate-400">
            {securityStatus?.admin_key_configured
              ? "Admin key configured on server."
              : "No server key set; open in dev."}
          </p>
        </div>

        {/* AI Budget Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold">
            <DollarSign className="w-4 h-4 text-cyan-400" />
            <span>AI Budget ($5.00 Cap)</span>
          </div>
          <div className="text-sm font-bold text-white">
            ${securityStatus ? securityStatus.ai_spend_today_usd.toFixed(4) : "0.0000"}{" "}
            <span className="text-xs font-normal text-slate-400">
              / ${securityStatus?.daily_ai_budget_usd.toFixed(2) || "5.00"}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                securityStatus?.ai_budget_available !== false ? "bg-emerald-400" : "bg-rose-500"
              }`}
            />
            <span className="text-[10px] text-slate-300">
              {securityStatus?.ai_budget_available !== false
                ? "Budget Active (Deep AI Enabled)"
                : "Cap Reached (Rule-based Fallback)"}
            </span>
          </div>
        </div>

        {/* Rate Limiting Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold">
            <Activity className="w-4 h-4 text-purple-400" />
            <span>Rate Limiting Policies</span>
          </div>
          <div className="text-sm font-bold text-white">
            {securityStatus?.rate_limit_read_per_min || 120}{" "}
            <span className="text-xs font-normal text-slate-400">req/min (Read)</span>
          </div>
          <p className="text-[10px] text-slate-400">
            Mutations throttled at {securityStatus?.rate_limit_mutation_per_min || 30} req/min.
          </p>
        </div>
      </div>

      {/* Admin API Key Configuration */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Key className="w-4 h-4 text-amber-400" />
          <span>Client API Authentication Key</span>
        </div>
        <p className="text-xs text-slate-400">
          If authentication is enforced on the backend, supply your configured <code className="text-slate-300 bg-slate-800 px-1 py-0.5 rounded">ADMIN_API_KEY</code> or <code className="text-slate-300 bg-slate-800 px-1 py-0.5 rounded">SECRET_KEY</code>. It will be stored locally and sent with all mutation requests.
        </p>

        <div className="flex gap-2">
          <input
            type="password"
            placeholder="Enter X-API-Key..."
            value={apiKeyInput}
            onChange={(e) => setApiKeyInput(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
          />
          <button
            onClick={handleSaveApiKey}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition"
          >
            Save Key
          </button>
          {apiKeyInput && (
            <button
              onClick={handleClearApiKey}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
            >
              Clear
            </button>
          )}
        </div>

        {keySaved && (
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <Check className="w-3.5 h-3.5" />
            <span>API key saved to local session.</span>
          </div>
        )}
      </div>

      {/* Signal Scoring Configuration Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <span className="text-sm font-semibold text-white">Multi-Factor Weight Allocation</span>
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
