"use client";

import React from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  FileCheck2,
  FileText,
  GitBranch,
  Loader2,
  Receipt,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { ExecutionStage, ExecutionStageEvent } from "@/lib/api";

export interface ExecutionTimelineProps {
  events: ExecutionStageEvent[];
  isRunning?: boolean;
  className?: string;
  onSelectEvidence?: (evidenceId: string) => void;
}

const STAGE_CONFIG: Record<
  ExecutionStage,
  { label: string; icon: React.ComponentType<{ className?: string }> }
> = {
  ANOMALY_DETECTED: { label: "Telemetry Anomaly", icon: Activity },
  EVIDENCE_MATCHED: { label: "GraphRAG Evidence", icon: Database },
  QUOTE_RESOLVED: { label: "Vendor RFQ / Quote", icon: FileText },
  POLICY_EVALUATED: { label: "Policy Boundary Gate", icon: ShieldCheck },
  INVOICE_GENERATED: { label: "BOLT11 Invoice", icon: Receipt },
  PAYMENT_AUTHORIZED: { label: "Payment Authorized", icon: Zap },
  SETTLEMENT_CONFIRMED: { label: "Lightning Settlement", icon: FileCheck2 },
  GRAPH_LINKED: { label: "Graph Lineage Linked", icon: GitBranch },
  OUTCOME_RESOLVED: { label: "Work-Order Outcome", icon: CheckCircle2 },
};

export function ExecutionTimeline({
  events,
  isRunning = false,
  className = "",
  onSelectEvidence,
}: ExecutionTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div
        data-testid="execution-timeline-empty"
        className="p-8 border border-dashed border-border rounded-2xl bg-muted/10 text-center text-xs text-muted-foreground"
      >
        <Clock className="w-8 h-8 mx-auto mb-2 opacity-40 animate-pulse" />
        <p className="font-semibold text-foreground/80">Awaiting Judge Scenario Execution</p>
        <p className="mt-1 max-w-sm mx-auto opacity-70">
          Click &quot;▶ RUN INDUSTRIAL EMERGENCY&quot; above to watch real-time telemetry detection, GraphRAG reasoning, spending policy evaluation, and Lightning settlement.
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="execution-timeline"
      className={`space-y-4 p-5 bg-card border border-border/80 rounded-2xl shadow-sm ${className}`}
    >
      <div className="flex items-center justify-between pb-3 border-b border-border/60">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-primary" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
            Live Execution Timeline (Measured Timings)
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-amber-500 font-mono animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Running...
            </span>
          )}
          <span className="text-[11px] font-mono text-muted-foreground">
            {events.length} / 9 Stages
          </span>
        </div>
      </div>

      {/* Restrained Stage Progress Bar (Task 8.2) */}
      <div
        data-testid="execution-progress-bar"
        className="h-1.5 w-full bg-muted/60 rounded-full overflow-hidden"
      >
        <div
          className={`h-full transition-all duration-300 ease-out rounded-full ${
            events.some((e) => e.status === "FAILED")
              ? "bg-rose-500"
              : events.some((e) => e.status === "PENDING_APPROVAL")
              ? "bg-amber-500"
              : events.length >= 9
              ? "bg-emerald-500"
              : "bg-primary"
          }`}
          style={{ width: `${Math.min(100, Math.round((events.length / 9) * 100))}%` }}
        />
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border/60">
        {events.map((evt, idx) => {
          const config = STAGE_CONFIG[evt.stage] || { label: evt.stage, icon: Activity };
          const Icon = config.icon;
          const isSuccess = evt.status === "SUCCESS";
          const isEscalated = evt.status === "PENDING_APPROVAL";
          const isFailed = evt.status === "FAILED";
          const isLatest = idx === events.length - 1;

          // Format measured elapsed time: 0142ms -> 00.14s
          const seconds = (evt.elapsed_ms / 1000).toFixed(2);
          const timeFormatted = `${seconds.padStart(5, "0")}s`;

          return (
            <div
              key={`${evt.stage}-${idx}`}
              data-testid={`timeline-stage-${evt.stage.toLowerCase()}`}
              className="relative group transition-all animate-in fade-in-50 slide-in-from-left-1 duration-200"
            >
              {/* Node Icon on Timeline */}
              <div
                className={`absolute -left-[27px] top-0.5 w-6 h-6 rounded-full flex items-center justify-center border-2 bg-background transition-all duration-200 ${
                  isSuccess
                    ? "border-emerald-500 text-emerald-500"
                    : isEscalated
                    ? "border-amber-500 text-amber-500"
                    : isFailed
                    ? "border-rose-500 text-rose-500"
                    : "border-primary text-primary"
                } ${isLatest && isRunning ? "ring-4 ring-amber-500/30 animate-pulse" : isLatest ? "ring-2 ring-primary/20" : ""}`}
              >
                {isSuccess && <CheckCircle2 className="w-3.5 h-3.5" />}
                {isEscalated && <ShieldAlert className="w-3.5 h-3.5" />}
                {isFailed && <AlertCircle className="w-3.5 h-3.5" />}
              </div>

              {/* Stage Content */}
              <div className="p-3 bg-muted/30 hover:bg-muted/50 rounded-xl border border-border/40 transition-all duration-200">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="font-semibold text-xs text-foreground">
                      {config.label}
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border/40">
                      {evt.stage}
                    </span>
                    {evt.stage === "EVIDENCE_MATCHED" && evt.data?.retrieval_method && (
                      <span
                        data-testid="timeline-retrieval-badge"
                        className={`text-[9px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                          evt.data.retrieval_method === "HYBRID_RETRIEVAL"
                            ? "bg-sky-500/15 text-sky-500 dark:text-sky-400 border-sky-500/30"
                            : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
                        }`}
                      >
                        {evt.data.retrieval_method === "HYBRID_RETRIEVAL"
                          ? "HYBRID_RETRIEVAL"
                          : "CONTROLLED DEMO FIXTURE"}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-semibold text-muted-foreground">
                      {timeFormatted}
                    </span>
                    <span
                      className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        isSuccess
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                          : isEscalated
                          ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                          : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30"
                      }`}
                    >
                      {evt.status}
                    </span>
                  </div>
                </div>

                {/* Human-Readable Message */}
                <p className="text-xs text-foreground/90 font-sans leading-relaxed">
                  {evt.message}
                </p>

                {/* Explicit Truthful Disclosure Notice if present */}
                {evt.data?.disclosure && (
                  <p
                    data-testid="timeline-stage-disclosure"
                    className="text-[10px] text-muted-foreground/80 font-mono mt-1.5 italic"
                  >
                    ℹ {evt.data.disclosure}
                  </p>
                )}

                {/* Evidence References Badges */}
                {evt.evidence_refs && evt.evidence_refs.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 mt-2 pt-2 border-t border-border/30">
                    <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">
                      Citations:
                    </span>
                    {evt.evidence_refs.map((refId) => (
                      <button
                        key={refId}
                        type="button"
                        onClick={() => onSelectEvidence?.(refId)}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-background hover:bg-muted text-foreground/80 border border-border transition-colors hover:border-primary/50"
                      >
                        {refId}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ExecutionTimeline;
