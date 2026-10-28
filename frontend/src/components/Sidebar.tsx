"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Newspaper,
  Compass,
  BookmarkCheck,
  TrendingUp,
  BarChart3,
  Sliders,
  ShieldAlert,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/news", label: "News Feed", icon: Newspaper },
  { href: "/signals", label: "Signal Engine", icon: Compass },
  { href: "/watchlist", label: "Watchlist", icon: BookmarkCheck },
  { href: "/market", label: "Market & Sectors", icon: TrendingUp },
  { href: "/performance", label: "Performance & P&L", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Sliders },
  { href: "/system-health", label: "System Health", icon: ShieldAlert },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-1">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href === "/dashboard" && pathname === "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                isActive
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="mt-auto p-4 border-t border-slate-800/80">
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
          <div className="text-slate-400 font-medium">Session Status</div>
          <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Paper Trading Active
          </div>
          <div className="text-slate-500 text-[11px] pt-1">
            Real orders disabled by architecture.
          </div>
        </div>
      </div>
    </aside>
  );
};
