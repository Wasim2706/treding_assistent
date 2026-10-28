"use client";

import React, { useEffect, useState } from "react";
import { TrendingUp, Layers, Building2 } from "lucide-react";
import { api } from "@/lib/api";
import { Stock } from "@/lib/types";

export default function MarketPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [sectors, setSectors] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [stocksRes, sectorsRes] = await Promise.all([
          api.getStocks(),
          api.getSectors(),
        ]);
        if (stocksRes?.data) setStocks(stocksRes.data);
        if (sectorsRes?.data) setSectors(sectorsRes.data);
      } catch (err) {
        console.error("Market data load error:", err);
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
          <TrendingUp className="w-5 h-5 text-emerald-400" />
          Indian Market &amp; Sector Impact Matrix
        </h2>
        <p className="text-xs text-slate-400">
          Macro sensitivity mapping: Crude oil, US tech trends, RBI interest rate adjustments, and currency fluctuations.
        </p>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
