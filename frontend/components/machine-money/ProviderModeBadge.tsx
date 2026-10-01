"use client";

import React from "react";
import { ShieldAlert, ShieldCheck, Zap, Activity, Info } from "lucide-react";

export interface ProviderModeBadgeProps {
  providerName?: string;
  network?: string;
  isMock?: boolean;
  latencyMs?: number;
  balanceSats?: number;
  className?: string;
  showDetails?: boolean;
}

export function ProviderModeBadge({
  providerName = "mock",
  network = "regtest",
  isMock = true,
  latencyMs,
  balanceSats,
  className = "",
  showDetails = false,
}: ProviderModeBadgeProps) {
  // Infer mock if providerName is mock or explicitly passed
  const isSimulation = isMock || providerName.toLowerCase().includes("mock");

  return (
    <div
      data-testid="provider-mode-badge"
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
        isSimulation
          ? "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-300"
          : "bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300"
      } ${className}`}
    >
      {/* Icon */}
      {isSimulation ? (
        <ShieldAlert className="w-3.5 h-3.5 text-amber-500 shrink-0" />
      ) : (
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
      )}

      {/* Primary Badge Label */}
      <span data-testid="provider-mode-label" className="font-semibold tracking-wider uppercase text-[11px]">
        {isSimulation ? "MOCK / SIMULATION" : "LIVE LIGHTNING"}
      </span>

      {/* Network Tag */}
      <span className="opacity-40">•</span>
      <span data-testid="provider-network" className="font-mono text-[10px] uppercase opacity-90">
        {network}
      </span>

      {/* Provider Name */}
      <span className="opacity-40">•</span>
      <span data-testid="provider-name" className="font-mono text-[10px] capitalize opacity-90">
        {providerName}
      </span>

      {/* Optional Latency Indicator */}
      {typeof latencyMs === "number" && (
        <>
          <span className="opacity-40">•</span>
          <span className="flex items-center gap-0.5 font-mono text-[10px] opacity-80">
            <Activity className="w-3 h-3 text-current" />
            {latencyMs.toFixed(1)}ms
          </span>
        </>
      )}

      {/* Optional Balance */}
      {typeof balanceSats === "number" && (
        <>
          <span className="opacity-40">•</span>
          <span className="flex items-center gap-0.5 font-mono text-[10px] opacity-90 font-medium">
            <Zap className="w-3 h-3 text-amber-500 fill-amber-500" />
            {balanceSats.toLocaleString()} sats
          </span>
        </>
      )}

      {/* Detailed Tooltip/Disclaimer Tag if requested */}
      {showDetails && isSimulation && (
        <span
          title="Deterministic offline simulation for judging and CI safety. Zero risk, no real bitcoin transferred."
          className="cursor-help opacity-70 hover:opacity-100 transition-opacity"
        >
          <Info className="w-3.5 h-3.5" />
        </span>
      )}
    </div>
  );
}

export default ProviderModeBadge;
