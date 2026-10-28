import React from "react";
import { AlertTriangle, ShieldCheck } from "lucide-react";

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-950/60 border-b border-amber-500/30 px-4 py-2 text-xs text-amber-200/90 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong className="text-amber-300 font-semibold uppercase tracking-wider">PAPER TRADING / SIGNAL-ONLY MODE:</strong> Real order execution is strictly disabled. All market predictions and signals are probabilistic algorithmic estimates for educational decision-support. No guaranteed returns.
        </span>
      </div>
      <div className="hidden md:flex items-center gap-1.5 text-emerald-400 font-medium shrink-0">
        <ShieldCheck className="w-4 h-4" />
        <span>Safety Rules Active</span>
      </div>
    </div>
  );
};
