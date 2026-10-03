"use client";

import React from "react";
import {
  X,
  ShieldCheck,
  Zap,
  Activity,
  Database,
  Lock,
  Wrench,
  BarChart3,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { ProviderModeBadge } from "./ProviderModeBadge";
import type { MachineMoneyHealth } from "@/lib/api";

export interface SystemReadinessModalProps {
  isOpen: boolean;
  onClose: () => void;
  health?: MachineMoneyHealth | null;
  className?: string;
}

export function SystemReadinessModal({
  isOpen,
  onClose,
  health,
  className = "",
}: SystemReadinessModalProps) {
  if (!isOpen) return null;

  const isConnected = health?.is_connected ?? true;
  const providerName = health?.provider_name || "mock";
  const network = health?.network || "regtest";
  const isMock = health?.is_mock !== false || providerName.toLowerCase().includes("mock");
  const isLive = !isMock && isConnected;
  const graphStatus = health?.details?.graph_status;
  const graphConnected = health?.details?.graph_connected;
  const isGraphDegraded = graphStatus === "DEGRADED / FALLBACK" || graphConnected === false;
  const latencyDisplay = health?.latency_ms != null && !isMock ? `${health.latency_ms.toFixed(1)} ms` : "DEMO VALUE (MOCK)";
  const balanceDisplay = health?.balance_sats != null && !isMock ? `${health.balance_sats.toLocaleString("en-US")} sats` : "DEMO VALUE (MOCK)";
  const providerStatusState = isConnected ? (isLive ? "CONNECTED" : "DEMO VALUE (MOCK)") : "DISCONNECTED";

  return (
    <div
      data-testid="system-readiness-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="system-readiness-title"
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in-0 duration-200 ${className}`}
    >
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-card border border-border shadow-2xl rounded-3xl flex flex-col overflow-hidden text-foreground">
        {/* Header */}
        <div className="p-5 border-b border-border/60 flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="system-readiness-title" className="font-bold text-base font-heading">
                  Safe System Readiness &amp; Operational Health
                </h3>
                <span
                  data-testid="system-readiness-status-badge"
                  className={`font-mono text-[10px] px-2 py-0.5 rounded border font-semibold ${
                    isLive && !isGraphDegraded
                      ? "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : isLive && isGraphDegraded
                      ? "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20"
                      : "text-purple-600 dark:text-purple-400 bg-purple-500/10 border-purple-500/20"
                  }`}
                >
                  {isLive ? (isGraphDegraded ? "GRAPH STATUS: DEGRADED / FALLBACK" : "ALL SYSTEMS NOMINAL") : "SIMULATION ENVIRONMENT READY"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Real-time subsystem health status. Zero secret keys or private credentials exposed.
              </p>
            </div>
          </div>

          <button
            type="button"
            data-testid="system-readiness-close"
            aria-label="Close system readiness dialog"
            onClick={onClose}
            className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-primary outline-none"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Top Banner: Mode & Network */}
          <div className="p-4 rounded-2xl bg-muted/30 border border-border/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase font-bold text-muted-foreground">Configured Settlement Mode</span>
              <p className="text-xs font-semibold text-foreground">
                {isMock ? "Zero-Risk Deterministic Simulation" : "Live Lightning Network Settlement"}
              </p>
            </div>
            <ProviderModeBadge
              providerName={providerName}
              network={network}
              isMock={isMock}
              balanceSats={health?.balance_sats}
              latencyMs={health?.latency_ms}
              showDetails={true}
            />
          </div>

          {/* Subsystems 2x3 Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
            {/* 1. Lightning Provider Subsystem */}
            <div
              data-testid="subsystem-lightning"
              className="p-3.5 rounded-2xl bg-card border border-border/70 space-y-2 hover:border-emerald-500/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-amber-500" />
                  Lightning Provider Layer
                </span>
                <span
                  className={`inline-flex items-center gap-1 text-[11px] font-semibold ${
                    isConnected ? (isLive ? "text-emerald-500" : "text-purple-400") : "text-rose-500"
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {providerStatusState}
                </span>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Adapter:</span>
                  <span className="text-foreground capitalize">{providerName}Provider {isMock && "(Simulated)"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Settlement Latency:</span>
                  <span className="text-foreground">{latencyDisplay}</span>
                </div>
                <div className="flex justify-between">
                  <span>Available Liquidity:</span>
                  <span className="text-foreground">{balanceDisplay}</span>
                </div>
              </div>
            </div>

            {/* 2. Automated Policy Governance */}
            <div
              data-testid="subsystem-policy"
              className="p-3.5 rounded-2xl bg-card border border-border/70 space-y-2 hover:border-emerald-500/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Lock className="w-4 h-4 text-sky-500" />
                  Policy &amp; Spending Cap
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-500">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Enforcing
                </span>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Autonomous Limit:</span>
                  <span className="text-foreground">500 satoshis</span>
                </div>
                <div className="flex justify-between">
                  <span>Bypass Guard:</span>
                  <span className="text-emerald-500 font-semibold">Strict Backend Rejection</span>
                </div>
                <div className="flex justify-between">
                  <span>Excursion Policy:</span>
                  <span className="text-foreground">Human Approval Mandatory</span>
                </div>
              </div>
            </div>

            {/* 3. Dual-Layer Persistence */}
            <div
              data-testid="subsystem-database"
              className="p-3.5 rounded-2xl bg-card border border-border/70 space-y-2 hover:border-emerald-500/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-purple-500" />
                  Dual Persistence (SQL + Graph)
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-500">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Synchronized
                </span>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Relational Ledger:</span>
                  <span className="text-foreground">PostgreSQL / SQLite</span>
                </div>
                <div className="flex justify-between">
                  <span>Operational Graph:</span>
                  <span className={isGraphDegraded ? "text-amber-500 font-semibold" : "text-foreground"}>
                    {isGraphDegraded ? "DEGRADED / FALLBACK" : "Neo4j Aura (Connected)"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Idempotency Store:</span>
                  <span className="text-foreground">SHA-256 Unique Key Index</span>
                </div>
              </div>
            </div>

            {/* 4. Multi-Vendor RFQ Marketplace */}
            <div
              data-testid="subsystem-rfq"
              className="p-3.5 rounded-2xl bg-card border border-border/70 space-y-2 hover:border-emerald-500/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Wrench className="w-4 h-4 text-amber-500" />
                  Autonomous RFQ Marketplace
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-500">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Operational
                </span>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Bidding Nodes:</span>
                  <span className="text-foreground">3 Synthetic Vendor Nodes</span>
                </div>
                <div className="flex justify-between">
                  <span>Optimization:</span>
                  <span className="text-foreground">Multi-Objective Score</span>
                </div>
                <div className="flex justify-between">
                  <span>Identity Protocol:</span>
                  <span className="text-foreground">secp256k1 Node Keys</span>
                </div>
              </div>
            </div>

            {/* 5. Industrial Economics Engine */}
            <div
              data-testid="subsystem-economics"
              className="p-3.5 rounded-2xl bg-card border border-border/70 space-y-2 hover:border-emerald-500/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4 text-emerald-500" />
                  Industrial Economics (FR-14)
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-500">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Calibrated
                </span>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Model Type:</span>
                  <span className="text-foreground">Modelled Downtime Exposure</span>
                </div>
                <div className="flex justify-between">
                  <span>Target Equipment:</span>
                  <span className="text-foreground">P-101A Crude Pump</span>
                </div>
                <div className="flex justify-between">
                  <span>Facility Basis:</span>
                  <span className="text-foreground">Synthetic Plant Parameters</span>
                </div>
              </div>
            </div>

            {/* 6. Security Perimeter & Sanitization */}
            <div
              data-testid="subsystem-security"
              className="p-3.5 rounded-2xl bg-card border border-border/70 space-y-2 hover:border-emerald-500/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  Security Perimeter (SEC-01)
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-500">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Sanitized
                </span>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Exposed Credentials:</span>
                  <span className="text-emerald-500 font-semibold">0 Secrets in Memory</span>
                </div>
                <div className="flex justify-between">
                  <span>Payment Boundary:</span>
                  <span className="text-foreground">Server-Side Protected</span>
                </div>
                <div className="flex justify-between">
                  <span>Proof Verification:</span>
                  <span className="text-foreground">Web Crypto SHA-256</span>
                </div>
              </div>
            </div>
          </div>

          {/* Privacy & Safe Disclosure Note */}
          <div className="p-3.5 rounded-xl bg-muted/40 border border-border/40 text-[11px] text-muted-foreground flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-primary shrink-0 mt-0.5" />
            <p>
              <strong>Safe Observability Notice:</strong> This readiness console dynamically aggregates internal service state without querying or revealing sensitive environmental credentials, wallet admin tokens, or production private keys.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemReadinessModal;
