"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  Clock,
  Database,
  DollarSign,
  Play,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import {
  executeJudgeMode,
  resetJudgeMode,
  type JudgeExecutionResponse,
} from "@/lib/api";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { ProviderModeBadge } from "./ProviderModeBadge";

export interface JudgeModeProps {
  onExecutionComplete?: (response: JudgeExecutionResponse) => void;
  className?: string;
}

export function JudgeMode({ onExecutionComplete, className = "" }: JudgeModeProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [response, setResponse] = useState<JudgeExecutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunScenario = async (
    scenario: "INDUSTRIAL_EMERGENCY" | "POLICY_ESCALATION" | "PROVIDER_FAILURE" = "INDUSTRIAL_EMERGENCY",
    costOverride?: number
  ) => {
    setIsRunning(true);
    setError(null);
    try {
      const res = await executeJudgeMode({
        scenario,
        equipment_id: "P-101A",
        override_cost_sats: costOverride,
        auto_approve: true,
      });
      setResponse(res);
      onExecutionComplete?.(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Execution failed. Check backend connectivity.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleReset = async () => {
    setIsRunning(true);
    setError(null);
    try {
      await resetJudgeMode();
      setResponse(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Reset failed.");
    } finally {
      setIsRunning(false);
    }
  };

  const isSuccess = response?.status === "SUCCESS";
  const isEscalated = response?.status === "PENDING_APPROVAL";

  return (
    <div
      data-testid="judge-mode-console"
      className={`p-6 bg-gradient-to-br from-card via-card to-muted/20 border-2 border-primary/20 hover:border-primary/40 rounded-3xl shadow-lg transition-all ${className}`}
    >
      {/* Top Banner: Judge Briefing & Status */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-bold text-[10px] uppercase tracking-wider border border-amber-500/30 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              Judge Mode • One-Click Autonomous M2M Pipeline
            </span>
            {response && (
              <span className="font-mono text-[10px] text-muted-foreground">
                ID: {response.execution_id}
              </span>
            )}
          </div>
          <h2 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-foreground flex items-center gap-2">
            Industrial Emergency Autonomous Settlement
          </h2>
          <p className="text-xs text-muted-foreground max-w-2xl mt-1">
            Watch AuRAG detect a real-time sensor anomaly on pump <strong className="text-foreground">P-101A</strong>, ground it in GraphRAG evidence, evaluate automated spending policy, and settle a BOLT11 Lightning micro-payment.
          </p>
        </div>

        {/* Live Provider & Status Badge */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 shrink-0">
          <ProviderModeBadge
            providerName={response?.provider_mode?.includes("MOCK") ? "mock" : "lnbits"}
            isMock={response ? response.provider_mode.includes("MOCK") : true}
            network="regtest"
            showDetails={true}
          />
        </div>
      </div>

      {/* 5-Question Orientation Ribbon (Task 8.1 Above-The-Fold Value Prop) */}
      <div
        data-testid="judge-value-ribbon"
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 py-4 border-b border-border/40"
      >
        <div className="p-2.5 rounded-xl bg-card/70 border border-border/60 flex flex-col gap-1 hover:border-amber-500/40 transition-colors">
          <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
            <Activity className="w-3 h-3 text-amber-500" />
            1. Why We Pay
          </span>
          <span className="text-xs font-semibold text-foreground">
            Telemetry Anomaly
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            Vibration &gt; 4.5 mm/s (Zone C)
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-card/70 border border-border/60 flex flex-col gap-1 hover:border-sky-500/40 transition-colors">
          <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
            <Database className="w-3 h-3 text-sky-500" />
            2. Justified By
          </span>
          <span className="text-xs font-semibold text-foreground">
            GraphRAG Evidence
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            FE-001 &bull; PROC-001 (94%)
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-card/70 border border-border/60 flex flex-col gap-1 hover:border-emerald-500/40 transition-colors">
          <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-500" />
            3. Why Allowed
          </span>
          <span className="text-xs font-semibold text-foreground">
            Autonomous Policy
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            250 sats &le; 500 sat cap
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-card/70 border border-border/60 flex flex-col gap-1 hover:border-amber-500/40 transition-colors">
          <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
            <Zap className="w-3 h-3 text-amber-500" />
            4. Settlement
          </span>
          <span className="text-xs font-semibold text-foreground">
            Lightning Micro-Pay
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            Instant BOLT11 + Preimage
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-card/70 border border-border/60 flex flex-col gap-1 col-span-2 sm:col-span-1 hover:border-emerald-500/40 transition-colors">
          <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
            <DollarSign className="w-3 h-3 text-emerald-500" />
            5. Business Impact
          </span>
          <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
            $1.17M Loss Averted
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            4.5h Outage Avoided
          </span>
        </div>
      </div>

      {/* Control Buttons Grid */}
      <div className="py-4 flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3">
        {/* Primary CTA */}
        <button
          type="button"
          data-testid="run-emergency-button"
          onClick={() => handleRunScenario("INDUSTRIAL_EMERGENCY", 250)}
          disabled={isRunning}
          className="relative group overflow-hidden px-6 py-3.5 bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700 hover:from-amber-600 hover:to-amber-800 text-slate-950 font-bold text-sm rounded-xl shadow-lg hover:shadow-amber-500/25 transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 cursor-pointer active:scale-95 ring-2 ring-amber-500/40 hover:ring-amber-500 w-full sm:w-auto"
        >
          <Play className={`w-4 h-4 fill-current ${isRunning ? "animate-spin" : "group-hover:translate-x-0.5 transition-transform"}`} />
          <span>RUN INDUSTRIAL EMERGENCY</span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-black/20 text-white font-medium">
            250 sats
          </span>
        </button>

        {/* Secondary Policy Escalation Trigger */}
        <button
          type="button"
          data-testid="run-escalation-button"
          onClick={() => handleRunScenario("POLICY_ESCALATION", 1200)}
          disabled={isRunning}
          className="px-4 py-3 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-semibold text-xs rounded-xl border border-border transition-all flex items-center justify-center gap-2 disabled:opacity-50 w-full sm:w-auto"
        >
          <ShieldAlert className="w-4 h-4 text-amber-500" />
          <span>Run Policy Escalation (&gt;500 sats)</span>
          <span className="text-[10px] font-mono opacity-70">1,200 sats</span>
        </button>

        {/* Provider Failure Trigger (Task 6.3 / FE-03) */}
        <button
          type="button"
          data-testid="run-provider-failure-button"
          onClick={() => handleRunScenario("PROVIDER_FAILURE", 250)}
          disabled={isRunning}
          className="px-4 py-3 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-semibold text-xs rounded-xl border border-border transition-all flex items-center justify-center gap-2 disabled:opacity-50 hover:border-rose-500/40 w-full sm:w-auto"
        >
          <AlertOctagon className="w-4 h-4 text-rose-500" />
          <span>Run Provider Failure</span>
          <span className="text-[10px] font-mono opacity-70">250 sats</span>
        </button>

        {/* Reset State Button */}
        <button
          type="button"
          data-testid="reset-scenario-button"
          onClick={handleReset}
          disabled={isRunning}
          className="px-3.5 py-3 hover:bg-muted text-muted-foreground hover:text-foreground text-xs font-medium rounded-xl border border-transparent hover:border-border transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 w-full sm:w-auto"
          title="Reset demonstration state"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset</span>
        </button>

        {/* Execution Summary Tag */}
        {response && (
          <div className="ml-auto flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 font-mono text-muted-foreground">
              <Clock className="w-3.5 h-3.5 text-primary" />
              <span>Total Runtime:</span>
              <strong className="text-foreground">{response.total_elapsed_ms}ms</strong>
            </div>
            <span
              className={`px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border ${
                isSuccess
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                  : isEscalated
                  ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
                  : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30"
              }`}
            >
              {response.status}
            </span>
          </div>
        )}
      </div>

      {/* Provider Failure Scenario Status & Retry Guidance (Task 6.3) */}
      {response?.status === "FAILED" && (
        <div
          data-testid="provider-failure-alert"
          className="mb-4 p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-xs space-y-2.5 animate-in fade-in"
        >
          <div className="flex items-center gap-2 font-bold text-rose-600 dark:text-rose-400">
            <AlertOctagon className="w-4 h-4 shrink-0 text-rose-500" />
            <span>Payment Unsettled — Simulated Provider Failure</span>
          </div>
          <p className="text-muted-foreground text-xs leading-relaxed">
            {response.summary || "Payment halted at settlement stage. Outbound channel route liquidity exhausted."}
          </p>
          <div className="p-3 bg-card/80 border border-rose-500/20 rounded-xl space-y-1">
            <span className="font-semibold text-rose-600 dark:text-rose-400 text-[11px] block">
              Retry &amp; Remediation Guidance:
            </span>
            <p className="font-mono text-[11px] text-foreground">
              {response.payment_record?.retry_guidance ||
                "Payment not executed. Zero satoshis deducted. Retry guidance: Re-balance payment channel via LSP or route through alternative peering node."}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-muted-foreground pt-0.5">
            <span>Audit: <strong className="text-rose-600 dark:text-rose-400 font-semibold">PAYMENT_SETTLEMENT_FAILED</strong></span>
            <span>Settled Sats: <strong className="text-foreground">0</strong></span>
            <span>Duplicate Risk: <strong className="text-emerald-600 dark:text-emerald-400">PREVENTED</strong></span>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-600 dark:text-rose-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Embedded Live Execution Timeline */}
      <div className="mt-2">
        <ExecutionTimeline
          events={response?.events || []}
          isRunning={isRunning}
        />
      </div>
    </div>
  );
}

export default JudgeMode;
