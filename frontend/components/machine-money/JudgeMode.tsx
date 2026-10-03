"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
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
import { ProofVerification } from "./ProofVerification";

export interface JudgeModeProps {
  onExecutionComplete?: (response: JudgeExecutionResponse) => void;
  className?: string;
}

export function JudgeMode({ onExecutionComplete, className = "" }: JudgeModeProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [response, setResponse] = useState<JudgeExecutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunScenario = async (
    scenario: "INDUSTRIAL_EMERGENCY" | "POLICY_ESCALATION" | "PROVIDER_FAILURE" | "PUBLIC_DATASET_REPLAY" = "INDUSTRIAL_EMERGENCY",
    costOverride?: number
  ) => {
    setIsRunning(true);
    setError(null);
    try {
      const res = await executeJudgeMode({
        scenario,
        equipment_id: scenario === "PUBLIC_DATASET_REPLAY" ? "REPLAY-ASSET-01" : "P-101A",
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
  const anomalyEvent = response?.events?.find((e) => e.stage === "ANOMALY_DETECTED");
  const evidenceEvent = response?.events?.find((e) => e.stage === "EVIDENCE_MATCHED");
  const isPublicReplay =
    response?.scenario === "PUBLIC_DATASET_REPLAY" ||
    anomalyEvent?.data?.data_source_type === "PUBLIC_DATASET";
  const datasetName =
    (anomalyEvent?.data?.dataset_name as string) ||
    (isPublicReplay ? "NASA IMS Bearing Run-to-Failure (Test 2)" : null);
  const datasetRecordId =
    (anomalyEvent?.data?.dataset_record_id as string) ||
    (isPublicReplay ? "NASA-IMS-T2-REC-042" : null);
  const assetId =
    (anomalyEvent?.data?.equipment_id as string) ||
    (isPublicReplay ? "REPLAY-ASSET-01" : "P-101A");
  const replayTimestamp =
    (anomalyEvent?.data?.record_timestamp as string) ||
    anomalyEvent?.timestamp ||
    (isPublicReplay ? "2004-02-18T09:42:39Z" : null);
  const retrievalMethod =
    (evidenceEvent?.data?.retrieval_method as string) ||
    (response?.evidence_package?.retrieval_method as string) ||
    (isPublicReplay ? "PUBLIC_DATASET" : "CONTROLLED_DEMO_FIXTURE");
  const isHybridRetrieval = retrievalMethod === "HYBRID_RETRIEVAL";

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
            providerMode={response?.provider_mode?.includes("MOCK") ? "MOCK" : "LIVE"}
            settlementSource={response?.provider_mode?.includes("MOCK") ? "SIMULATED" : "LIGHTNING_NODE"}
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
          <div className="flex items-center justify-between gap-1">
            <span className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
              <Database className="w-3 h-3 text-sky-500" />
              2. Justified By
            </span>
            {response && (
              <span
                data-testid="judge-retrieval-method-badge"
                className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border ${
                  isPublicReplay
                    ? "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/30"
                    : isHybridRetrieval
                    ? "bg-sky-500/15 text-sky-500 dark:text-sky-400 border-sky-500/30"
                    : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
                }`}
              >
                {isPublicReplay ? "PUBLIC DATASET / REPLAY" : isHybridRetrieval ? "HYBRID_RETRIEVAL" : "CONTROLLED DEMO FIXTURE"}
              </span>
            )}
          </div>
          <span className="text-xs font-semibold text-foreground">
            GraphRAG Evidence
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            {(evidenceEvent?.data?.matched_failure_event as string) || "FE-001"} &bull;{" "}
            {(evidenceEvent?.data?.governing_procedure as string) || "PROC-001"} (
            {Math.round(
              ((evidenceEvent?.data?.confidence as number) ??
                (response?.evidence_package?.confidence as number) ??
                0.94) * 100
            )}
            %)
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
            $1.17M Modelled Exposure
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            4.5h Synthetic Outage
          </span>
        </div>
      </div>

      {/* Data Provenance Bar (Task 2A.10 / 2A.13) */}
      <div
        data-testid="data-provenance-bar"
        className="my-3 px-4 py-2.5 rounded-xl bg-card/70 border border-border/60 flex flex-wrap items-center justify-between gap-3 text-xs"
      >
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground font-bold">
            Data Source:
          </span>
          {isPublicReplay ? (
            <span
              data-testid="provenance-badge-public"
              className="px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold uppercase tracking-wider bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 flex items-center gap-1.5"
            >
              <Database className="w-3 h-3 text-cyan-500" />
              [PUBLIC DATASET / REPLAY]
            </span>
          ) : (
            <span
              data-testid="provenance-badge-synthetic"
              className="px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1.5"
            >
              <Activity className="w-3 h-3 text-amber-500" />
              [SYNTHETIC DEMO]
            </span>
          )}
          <span className="text-[10px] font-mono text-muted-foreground/60 hidden sm:inline">
            (Live SCADA: Not connected)
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-[11px] font-mono text-muted-foreground">
          <span>
            Asset: <strong className="text-foreground">{assetId}</strong>
          </span>
          {isPublicReplay && datasetName && (
            <>
              <span className="hidden md:inline">
                Dataset: <strong className="text-foreground">{datasetName}</strong>
              </span>
              <span>
                Record: <strong className="text-cyan-600 dark:text-cyan-400">{datasetRecordId}</strong>
              </span>
              {replayTimestamp && (
                <span className="hidden lg:inline">
                  Timestamp: <strong className="text-foreground">{replayTimestamp}</strong>
                </span>
              )}
            </>
          )}
          {!isPublicReplay && (
            <span>
              Sensor: <strong className="text-foreground">VIB-301-BEARING</strong>
            </span>
          )}
        </div>
      </div>

      {/* Control Buttons Grid */}
      <div className="py-4 flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3">
        {/* Primary CTA */}
        <button
          type="button"
          data-testid="run-emergency-button"
          aria-label="Run industrial emergency autonomous settlement scenario (250 satoshis)"
          onClick={() => handleRunScenario("INDUSTRIAL_EMERGENCY", 250)}
          disabled={isRunning}
          className="relative group overflow-hidden px-6 py-3.5 bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700 hover:from-amber-600 hover:to-amber-800 text-slate-950 font-bold text-sm rounded-xl shadow-lg hover:shadow-amber-500/25 transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 cursor-pointer active:scale-95 ring-2 ring-amber-500/40 hover:ring-amber-500 focus-visible:ring-4 focus-visible:ring-amber-400 outline-none w-full sm:w-auto"
        >
          <Play className={`w-4 h-4 fill-current ${isRunning ? "animate-spin" : "group-hover:translate-x-0.5 transition-transform"}`} />
          <span>RUN INDUSTRIAL EMERGENCY</span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-black/20 text-white font-medium">
            250 sats
          </span>
        </button>

        {/* Public Dataset Replay Preset (Task 2A.4 / 2A.13) */}
        <button
          type="button"
          data-testid="run-public-replay-button"
          aria-label="Run public dataset replay scenario (NASA IMS Bearing Outer Race Spall)"
          onClick={() => handleRunScenario("PUBLIC_DATASET_REPLAY", 250)}
          disabled={isRunning}
          className="px-4 py-3 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 font-semibold text-xs rounded-xl border border-cyan-500/30 hover:border-cyan-500/60 transition-all flex items-center justify-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-cyan-500 outline-none w-full sm:w-auto"
        >
          <Database className="w-4 h-4 text-cyan-500" />
          <span>PUBLIC DATASET REPLAY</span>
          <span className="text-[10px] font-mono bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 px-1.5 py-0.5 rounded">
            NASA IMS
          </span>
        </button>

        {/* Secondary Policy Escalation Trigger */}
        <button
          type="button"
          data-testid="run-escalation-button"
          aria-label="Run policy escalation scenario exceeding 500 satoshis limit (1,200 satoshis)"
          onClick={() => handleRunScenario("POLICY_ESCALATION", 1200)}
          disabled={isRunning}
          className="px-4 py-3 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-semibold text-xs rounded-xl border border-border transition-all flex items-center justify-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-primary outline-none w-full sm:w-auto"
        >
          <ShieldAlert className="w-4 h-4 text-amber-500" />
          <span>Run Policy Escalation (&gt;500 sats)</span>
          <span className="text-[10px] font-mono opacity-70">1,200 sats</span>
        </button>

        {/* Provider Failure Trigger (Task 6.3 / FE-03) */}
        <button
          type="button"
          data-testid="run-provider-failure-button"
          aria-label="Run simulated provider failure scenario"
          onClick={() => handleRunScenario("PROVIDER_FAILURE", 250)}
          disabled={isRunning}
          className="px-4 py-3 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-semibold text-xs rounded-xl border border-border transition-all flex items-center justify-center gap-2 disabled:opacity-50 hover:border-rose-500/40 focus-visible:ring-2 focus-visible:ring-rose-500 outline-none w-full sm:w-auto"
        >
          <AlertOctagon className="w-4 h-4 text-rose-500" />
          <span>Run Provider Failure</span>
          <span className="text-[10px] font-mono opacity-70">250 sats</span>
        </button>

        {/* Reset State Button */}
        <button
          type="button"
          data-testid="reset-scenario-button"
          aria-label="Reset demonstration state"
          onClick={handleReset}
          disabled={isRunning}
          className="px-3.5 py-3 hover:bg-muted text-muted-foreground hover:text-foreground text-xs font-medium rounded-xl border border-transparent hover:border-border transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-primary outline-none w-full sm:w-auto"
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

      {/* Policy Escalation Scenario Status & Human Sign-Off (PRD4 Phase 8 Flow) */}
      {response?.status === "PENDING_APPROVAL" && (
        <div
          data-testid="policy-escalation-alert"
          className="mb-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-xs space-y-2.5 animate-in fade-in"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2 font-bold text-amber-600 dark:text-amber-400">
              <ShieldAlert className="w-4 h-4 shrink-0 text-amber-500" />
              <span>Zero-Trust Policy Gate Triggered — Operator Approval Required</span>
            </div>
            <button
              type="button"
              data-testid="approve-escalation-button"
              onClick={() => handleRunScenario("INDUSTRIAL_EMERGENCY", response.payment_record?.amount_sats || 1200)}
              disabled={isRunning}
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-sm transition-all flex items-center justify-center gap-1.5 text-xs cursor-pointer disabled:opacity-50 active:scale-95"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Sign &amp; Approve Settlement</span>
            </button>
          </div>
          <p className="text-muted-foreground text-xs leading-relaxed">
            {response.summary || "Spending policy limit exceeded: 1,200 sats exceeds autonomous cap (500 sats). Escalating to human plant operator review."}
          </p>
          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-muted-foreground pt-0.5">
            <span>Amount: <strong className="text-amber-600 dark:text-amber-400 font-semibold">{response.payment_record?.amount_sats || 1200} sats</strong></span>
            <span>Autonomous Cap: <strong className="text-foreground">500 sats</strong></span>
            <span>Queue Status: <strong className="text-amber-600 dark:text-amber-400">PENDING_APPROVAL</strong></span>
          </div>
        </div>
      )}

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

      {/* Cryptographic Payment Proof Verification (Fix #3 / Invariant sha256(preimage) = payment_hash) */}
      {response?.payment_record?.payment_hash && (
        <div data-testid="judge-crypto-proof-section" className="mt-4 pt-4 border-t border-border/40 animate-in fade-in-50">
          <ProofVerification
            paymentHash={response.payment_record.payment_hash}
            preimage={response.payment_record.preimage}
            isMock={response.provider_mode?.includes("MOCK")}
            settlementSource={response.provider_mode?.includes("MOCK") ? "SIMULATED" : "LIGHTNING_NODE"}
            autoVerify={true}
          />
        </div>
      )}
    </div>
  );
}

export default JudgeMode;
