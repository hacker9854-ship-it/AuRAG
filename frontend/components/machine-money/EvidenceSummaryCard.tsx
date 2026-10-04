"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  ShieldCheck,
  Zap,
} from "lucide-react";

export interface EvidenceSummaryCardProps {
  equipmentId?: string;
  anomalyTitle?: string;
  vibrationValue?: string;
  confidence?: number;
  failureSignatureId?: string;
  governingProcedure?: string;
  relatedWorkOrder?: string;
  workOrderId?: string;
  serviceName?: string;
  costSats?: number;
  policyCap?: number;
  policyStatus?: string;
  crossLayerJustification?: string;
  className?: string;
  onOpenGraphTrail?: () => void;
  onOpenProofDrawer?: () => void;
}

export function EvidenceSummaryCard({
  equipmentId = "P-101A",
  anomalyTitle = "Radial Bearing Vibration Excursion",
  vibrationValue = "5.42 mm/s (Threshold: 4.5 mm/s ISO Zone C)",
  confidence = 0.94,
  failureSignatureId = "FE-001",
  governingProcedure = "PROC-001",
  relatedWorkOrder = "WO-1002",
  workOrderId = "WO-2026-P101",
  serviceName = "Edge AI 20 kHz Wavelet FFT & Diagnostic SLA Reservation",
  costSats = 250,
  policyCap = 500,
  policyStatus = "AUTHORIZED",
  crossLayerJustification = "Because P-101A matched bearing failure signature FE-001 with 94% confidence, WO-1002 shows overdue preventative maintenance, and PROC-001 mandates 20 kHz diagnostic FFT analysis & emergency 4-hr SLA window.",
  className = "",
  onOpenGraphTrail,
  onOpenProofDrawer,
}: EvidenceSummaryCardProps) {
  const confidencePercent = Math.round(confidence * 100);
  const isAuthorized = policyStatus === "AUTHORIZED" || costSats <= policyCap;

  return (
    <div
      data-testid="evidence-summary-card"
      className={`p-6 bg-card border border-border/80 rounded-2xl shadow-sm space-y-5 text-foreground ${className}`}
    >
      {/* Header: Core Question */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-purple-500" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              GraphRAG Evidence Rationale
            </span>
          </div>
          <h3 className="text-base font-bold font-heading mt-1">
            Why Did Machine Money Move? (Autonomous Causality)
          </h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-2xl leading-relaxed">
            <span className="font-semibold text-purple-400">Why GraphRAG over a simple SCADA threshold?</span> A raw sensor threshold only detects physical symptoms (5.42 mm/s); GraphRAG justifies financial expenditure by verifying active OEM warranty, historical work orders (WO-1002), and plant SOPs (PROC-001) before satoshis are released.
          </p>
        </div>

        {/* Confidence Meter Badge */}
        <div className="flex items-center gap-2 bg-muted/40 px-3 py-1.5 rounded-xl border border-border/40">
          <span className="text-xs text-muted-foreground">Confidence:</span>
          <span className="text-xs font-mono font-bold text-foreground">
            {confidencePercent}%
          </span>
          <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* 4 Pillars Grid: Anomaly -> Graph -> Service -> Policy */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        {/* Pillar 1: Telemetry Anomaly */}
        <div className="p-3 bg-muted/30 rounded-xl border border-border/40 space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground text-[11px] font-medium">
            <Activity className="w-3.5 h-3.5 text-amber-500" />
            <span>1. Telemetry Anomaly</span>
          </div>
          <p className="font-bold text-foreground text-xs">{equipmentId}: {anomalyTitle}</p>
          <p className="font-mono text-[11px] text-amber-600 dark:text-amber-400">{vibrationValue}</p>
        </div>

        {/* Pillar 2: Graph Evidence */}
        <div className="p-3 bg-muted/30 rounded-xl border border-border/40 space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground text-[11px] font-medium">
            <Database className="w-3.5 h-3.5 text-purple-500" />
            <span>2. Matched Evidence</span>
          </div>
          <p className="font-bold text-foreground text-xs">Signature: {failureSignatureId}</p>
          <div className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground">
            <span>Cites:</span>
            <span className="bg-background px-1 rounded border">{governingProcedure}</span>
            <span className="bg-background px-1 rounded border">{relatedWorkOrder}</span>
          </div>
        </div>

        {/* Pillar 3: Authorized Service Action */}
        <div className="p-3 bg-muted/30 rounded-xl border border-border/40 space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground text-[11px] font-medium">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>3. Service Action</span>
          </div>
          <p className="font-bold text-foreground text-xs truncate" title={serviceName}>
            {serviceName}
          </p>
          <p className="font-mono text-[11px] text-foreground font-semibold">
            {costSats} sats <span className="text-[10px] font-normal text-muted-foreground">(Work Order {workOrderId})</span>
          </p>
        </div>

        {/* Pillar 4: Policy Gate */}
        <div className="p-3 bg-muted/30 rounded-xl border border-border/40 space-y-1">
          <div className="flex items-center gap-1.5 text-muted-foreground text-[11px] font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>4. Policy Gate</span>
          </div>
          <div className="flex items-center gap-1">
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                isAuthorized
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30"
              }`}
            >
              {isAuthorized ? "AUTHORIZED" : "PENDING_APPROVAL"}
            </span>
          </div>
          <p className="font-mono text-[10px] text-muted-foreground">
            {costSats} sats ≤ {policyCap} sats Cap
          </p>
        </div>
      </div>

      {/* Cross-Layer Grounded Natural Language Justification */}
      <div className="p-3.5 bg-muted/40 rounded-xl border border-border/40 text-xs space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-primary" />
            Cross-Layer Grounded Justification
          </span>
          <div className="flex items-center gap-3">
            {onOpenProofDrawer && (
              <button
                type="button"
                data-testid="open-proof-drawer-btn"
                onClick={onOpenProofDrawer}
                className="text-[10px] font-medium normal-case text-amber-500 hover:text-amber-400 hover:underline flex items-center gap-1"
              >
                <ShieldCheck className="w-3 h-3" />
                <span>View Cryptographic Proof Drawer</span>
              </button>
            )}
            {onOpenGraphTrail && (
              <button
                type="button"
                onClick={onOpenGraphTrail}
                className="text-[10px] font-normal normal-case text-primary hover:underline flex items-center gap-1"
              >
                <span>Inspect Neo4j Graph Trail</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
        <p className="text-foreground/90 font-sans leading-relaxed text-xs">
          {crossLayerJustification}
        </p>
      </div>
    </div>
  );
}

export default EvidenceSummaryCard;
