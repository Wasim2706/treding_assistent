"use client";

import React, { useState, useEffect } from "react";
import { Activity, Bell, RefreshCw, Clock } from "lucide-react";
import { api } from "@/lib/api";

export const Navbar: React.FC = () => {
  const [istTime, setIstTime] = useState<string>("");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone: "Asia/Kolkata",
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      };
      setIstTime(now.toLocaleTimeString("en-IN", options) + " IST");
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.refreshNews();
      await api.generateSignals();
      window.location.reload();
    } catch (e) {
      console.error("Refresh cycle error:", e);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-lg">
            IN
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
              Indian Market AI Intelligence
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                PAPER TRADING
              </span>
            </h1>
            <p className="text-xs text-slate-400">NSE / BSE Decision Support Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{istTime || "Loading IST..."}</span>
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition disabled:opacity-50"
            title="Trigger 5-minute news & signal cycle"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span className="hidden md:inline">Run Cycle</span>
          </button>
        </div>
      </div>
    </header>
  );
};
