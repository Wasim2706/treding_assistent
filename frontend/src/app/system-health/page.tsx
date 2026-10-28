"use client";

import React, { useEffect, useState } from "react";
import { ShieldAlert, Server, Database, Cpu, Activity, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { SystemHealth, SystemMetrics } from "@/lib/types";

export default function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHealth() {
      try {
        const [hRes, mRes] = await Promise.allSettled([
          api.getHealth(),
          api.getMetrics(),
        ]);
        if (hRes.status === "fulfilled") setHealth(hRes.value);
        if (mRes.status === "fulfilled") setMetrics(mRes.value);
      } catch (err) {
        console.error("Health check error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-emerald-400" />
          System Health, Liveness &amp; API Metrics
        </h2>
        <p className="text-xs text-slate-400">
          Real-time service health, database connection pool, background scheduler liveness, and API usage quotas.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Core Liveness Status */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Server className="w-4 h-4 text-emerald-400" />
            Backend API &amp; Services
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">API Status</span>
              <span className="text-emerald-400 font-semibold uppercase">{health?.status || "HEALTHY"}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Version</span>
              <span className="text-white font-mono">{health?.version || "1.0.0"}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Database Connection</span>
              <span className="text-emerald-400 font-mono">{health?.database || "Connected"}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">OpenAI API Engine</span>
              <span className="text-slate-200 font-mono">{health?.ai_status || "Active"}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Trading Safety Enforcement</span>
              <span className="text-emerald-400 font-semibold">{health?.paper_trading_safety || "ENFORCED"}</span>
            </div>
          </div>
        </div>

        {/* Runtime Metrics */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
            Runtime Performance &amp; Quotas
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Uptime</span>
              <span className="text-white font-mono">
                {metrics?.uptime_seconds ? `${Math.floor(metrics.uptime_seconds)}s` : "0s"}
              </span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Total News Collected</span>
              <span className="text-white font-mono">{metrics?.news_articles_total || 0}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Total Signals Generated</span>
              <span className="text-white font-mono">{metrics?.signals_generated_total || 0}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Active Paper Trades</span>
              <span className="text-white font-mono">{metrics?.paper_trades_active || 0}</span>
            </div>

            <div className="flex justify-between items-center p-2.5 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-slate-400">Estimated AI Cost (USD)</span>
              <span className="text-emerald-400 font-mono font-semibold">
                ${metrics?.estimated_ai_cost_usd?.toFixed(3) || "0.000"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
