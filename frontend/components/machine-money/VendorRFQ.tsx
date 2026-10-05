"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Wrench,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  TrendingDown,
  Gauge,
  Layers,
  Sparkles,
  Copy,
  Check,
} from "lucide-react";
import {
  type SelectionStrategy,
  type VendorQuoteCandidate,
  type VendorRFQResponse,
  requestVendorRFQ,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface VendorRFQProps {
  serviceId?: string;
  equipmentId?: string;
  policyCapSats?: number;
  initialRFQ?: VendorRFQResponse | null;
  onSelectCandidate?: (candidate: VendorQuoteCandidate) => void;
  className?: string;
}

export function VendorRFQ({
  serviceId = "bearing-inspection",
  equipmentId = "P-101A",
  policyCapSats = 500,
  initialRFQ,
  onSelectCandidate,
  className = "",
}: VendorRFQProps) {
  const [strategy, setStrategy] = useState<SelectionStrategy>("FASTEST_SLA");
  const [rfq, setRfq] = useState<VendorRFQResponse | null>(initialRFQ || null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(
    initialRFQ?.selected_vendor?.candidate_id || null
  );
  const [copiedPubkey, setCopiedPubkey] = useState<string | null>(null);

  const onSelectCandidateRef = useRef(onSelectCandidate);
  useEffect(() => {
    onSelectCandidateRef.current = onSelectCandidate;
  }, [onSelectCandidate]);

  // Fetch or update RFQ when strategy changes
  useEffect(() => {
    let isMounted = true;
    requestVendorRFQ({
      equipment_id: equipmentId,
      service_id: serviceId,
      strategy: strategy,
      max_budget_sats: policyCapSats,
    })
      .then((res) => {
        if (!isMounted) return;
        setRfq(res);
        setSelectedCandidateId(res.selected_vendor.candidate_id);
        if (onSelectCandidateRef.current) {
          onSelectCandidateRef.current(res.selected_vendor);
        }
      })
      .catch((err) => {
        console.error("Failed to load RFQ:", err);
      });

    return () => {
      isMounted = false;
    };
  }, [strategy, serviceId, equipmentId, policyCapSats]);

  const handleCopyPubkey = (pubkey: string, id: string) => {
    navigator.clipboard.writeText(pubkey);
    setCopiedPubkey(id);
    setTimeout(() => setCopiedPubkey(null), 2000);
  };

  const handleManualSelect = (candidate: VendorQuoteCandidate) => {
    setSelectedCandidateId(candidate.candidate_id);
    if (onSelectCandidate) {
      onSelectCandidate(candidate);
    }
  };

  return (
    <div
      data-testid="vendor-rfq-container"
      className={`p-6 bg-card border border-border/80 rounded-2xl shadow-sm space-y-6 text-foreground ${className}`}
    >
      {/* Header & Disclosure */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-500">
              <Wrench className="w-4 h-4" />
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              Autonomous RFQ Marketplace
            </span>
            <Badge variant="outline" className="text-[10px] font-mono text-muted-foreground">
              FR-04 Multi-Vendor
            </Badge>
          </div>
          <h3 className="text-base font-bold font-heading mt-1">
            Competitive Maintenance Bidding &amp; Selection
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Illustrative multi-vendor bidding simulation (Apex Diagnostics, Precision Dynamics, Quantum Reliability) evaluated against spending policies and SLA constraints.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] font-mono text-muted-foreground uppercase bg-muted/60 px-2.5 py-1 rounded-lg border">
            Cap: <strong className="text-emerald-500">{policyCapSats} sats</strong>
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2 py-1 rounded-lg border border-purple-500/20">
            PRE-APPROVED DEMO VENDOR NODES
          </span>
          <span className="text-[9px] font-semibold uppercase text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
            [Illustrative Bidding Simulation]
          </span>
        </div>
      </div>

      {/* Strategy Toggle Controls */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 uppercase tracking-wider text-[10px]">
          <Gauge className="w-3.5 h-3.5 text-primary" />
          <span>Autonomous Selection Strategy:</span>
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            {
              id: "FASTEST_SLA",
              label: "Fastest SLA",
              sub: "Speed Priority",
              badge: "Recommended",
              icon: Clock,
            },
            {
              id: "LOWEST_COST",
              label: "Lowest Cost",
              sub: "Treasury Saver",
              badge: "Frugal",
              icon: TrendingDown,
            },
            {
              id: "HIGHEST_RELIABILITY",
              label: "Top Reliability",
              sub: "Zero Failure",
              badge: "Quality",
              icon: ShieldCheck,
            },
            {
              id: "BALANCED",
              label: "Balanced",
              sub: "Multi-Objective",
              badge: "Weighted",
              icon: Layers,
            },
          ].map((strat) => {
            const isSelected = strategy === strat.id;
            const Icon = strat.icon;
            return (
              <button
                key={strat.id}
                type="button"
                data-testid={`strategy-${strat.id.toLowerCase()}`}
                onClick={() => setStrategy(strat.id as SelectionStrategy)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/40"
                    : "bg-muted/30 border-border/50 hover:bg-muted/60 hover:border-border"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <Icon className={`w-4 h-4 ${isSelected ? "text-primary" : "text-muted-foreground"}`} />
                  <span
                    className={`text-[9px] uppercase font-bold px-1.5 py-0.2 rounded ${
                      isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {strat.badge}
                  </span>
                </div>
                <div className="font-bold text-xs">{strat.label}</div>
                <div className="text-[10px] text-muted-foreground">{strat.sub}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Competing Vendor Bids Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold text-[11px] uppercase tracking-wider">
            Candidate Bids ({rfq?.candidates.length || 0} Registered Nodes)
          </span>
          <span className="text-[11px] text-muted-foreground">
            Click candidate to manually override selection
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {rfq?.candidates.map((c) => {
            const activeId = selectedCandidateId || rfq?.selected_vendor?.candidate_id;
            const isWinner = c.candidate_id === activeId;
            const exceedsCap = !c.within_policy_cap;
            const isOverride = isWinner && rfq && rfq.selected_vendor && c.candidate_id !== rfq.selected_vendor.candidate_id;

            return (
              <div
                key={c.candidate_id}
                data-testid={`vendor-card-${c.vendor_id}`}
                onClick={() => handleManualSelect(c)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between space-y-3 relative overflow-hidden ${
                  isWinner
                    ? "bg-card border-amber-500 shadow-md ring-1 ring-amber-500/50"
                    : "bg-muted/30 border-border/60 hover:border-border hover:bg-muted/50"
                }`}
              >
                {/* Winner Accent Bar */}
                {isWinner && (
                  <div className="absolute top-0 left-0 right-0 h-1.5 bg-amber-500" />
                )}

                <div className="space-y-2">
                  {/* Top Status & Tier */}
                  <div className="flex items-center justify-between gap-1 pt-1">
                    <span className="font-mono text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border/40">
                      {c.candidate_id}
                    </span>
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20">
                        {c.reputation_tier} Tier
                      </span>
                      {isWinner && (
                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-emerald-500 text-slate-950 flex items-center gap-0.5">
                          <CheckCircle2 className="w-2.5 h-2.5" /> {isOverride ? "Override" : "Best"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Vendor Name */}
                  <div>
                    <div className="flex items-center justify-between gap-1">
                      <h4 className="font-bold text-xs leading-snug truncate" title={c.vendor_name}>
                        {c.vendor_name}
                      </h4>
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[10px] text-muted-foreground font-mono truncate">
                        {c.vendor_id}
                      </span>
                      <span className="text-[8px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-1 py-0.5 rounded border border-purple-500/20">
                        {c.vendor_node_type || "DEMO VENDOR NODE"}
                      </span>
                    </div>
                  </div>

                  {/* Price & SLA Highlights */}
                  <div className="p-2.5 rounded-xl bg-background/80 border border-border/50 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-muted-foreground uppercase">Quote:</span>
                      <div className="text-right">
                        <span className="font-mono text-sm font-bold text-amber-500">
                          {c.amount_sats} sats
                        </span>
                        <span className="text-[9px] text-muted-foreground block font-mono">
                          (M2M Compute SLA)
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-muted-foreground">Dispatch SLA:</span>
                      <span className="font-mono font-semibold text-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3 text-blue-400" />
                        {c.sla_hours} hrs
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-muted-foreground">Reliability:</span>
                      <span className="font-mono font-bold text-emerald-500">
                        {Math.round(c.reliability_score * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* Policy Cap Badge */}
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-muted-foreground">Policy Gate:</span>
                    {exceedsCap ? (
                      <span className="font-semibold text-rose-500 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20 flex items-center gap-0.5">
                        <AlertTriangle className="w-2.5 h-2.5" /> Exceeds Cap
                      </span>
                    ) : (
                      <span className="font-semibold text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex items-center gap-0.5">
                        <ShieldCheck className="w-2.5 h-2.5" /> Within Cap
                      </span>
                    )}
                  </div>

                  {/* Deliverables & SLA Scope */}
                  {c.parts_included && c.parts_included.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[9px] uppercase tracking-wider text-muted-foreground block">
                        Diagnostic Scope &amp; SLA:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {c.parts_included.map((part, i) => (
                          <span
                            key={i}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-muted/60 text-muted-foreground truncate max-w-[130px]"
                            title={part}
                          >
                            {part}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Node Pubkey & Selection Footer */}
                <div className="pt-2 border-t border-border/40 space-y-2">
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span className="font-mono truncate max-w-[110px]" title={c.node_pubkey}>
                      {c.node_pubkey.slice(0, 10)}...
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyPubkey(c.node_pubkey, c.candidate_id);
                      }}
                      className="hover:text-foreground p-0.5"
                    >
                      {copiedPubkey === c.candidate_id ? (
                        <Check className="w-3 h-3 text-emerald-500" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>

                  <Button
                    size="sm"
                    variant={isWinner ? "default" : "outline"}
                    className={`w-full h-6 text-[10px] ${
                      isWinner ? "bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold" : ""
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleManualSelect(c);
                    }}
                  >
                    {isWinner ? (isOverride ? "Selected Winner (Override)" : "Selected Winner") : "Select Quote"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Explainable Decision Rationale Box */}
      {rfq && (() => {
        const activeId = selectedCandidateId || rfq.selected_vendor?.candidate_id;
        const activeCandidate = rfq.candidates.find((c) => c.candidate_id === activeId) || rfq.selected_vendor;
        const isOverride = activeCandidate && rfq.selected_vendor && activeCandidate.candidate_id !== rfq.selected_vendor.candidate_id;

        return (
          <div
            data-testid="rfq-rationale-box"
            className="p-4 bg-muted/40 rounded-xl border border-border/60 space-y-2 text-xs"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                <span>
                  {isOverride
                    ? "Operator Manual Selection (Override Active)"
                    : "Explainable Autonomous Selection Rationale"}
                </span>
              </span>
              <span className="font-mono text-[10px] text-muted-foreground bg-muted/80 px-2 py-0.5 rounded border border-border/40">
                {isOverride ? "Mode: Operator Override" : `Rule: ${String(rfq.scoring_model?.rule || rfq.strategy)}`}
              </span>
            </div>
            <p className="text-muted-foreground leading-relaxed text-xs">
              {isOverride
                ? `Operator manually selected ${activeCandidate.vendor_name} (${activeCandidate.vendor_id}) overriding the autonomous recommendation (${rfq.selected_vendor.vendor_name}). Dispatching diagnostic quote of ${activeCandidate.amount_sats} sats with ${activeCandidate.sla_hours}h SLA.`
                : rfq.selection_rationale}
            </p>
            <div className="p-2 rounded-lg bg-background/60 border border-border/40 flex items-center justify-between text-[11px] font-mono">
              <span className="text-muted-foreground text-[10px] uppercase font-bold">Scoring Model:</span>
              <span className="text-primary text-[10px]">Score = (0.5 &times; CostNorm) + (0.3 &times; LatencyNorm) + (0.2 &times; SLANorm)</span>
            </div>
            <div className="pt-2 border-t border-border/40 flex flex-wrap items-center justify-between gap-2 text-[10px] text-muted-foreground">
              <span>
                RFQ ID: <strong className="font-mono text-foreground">{rfq.rfq_id}</strong>
              </span>
              <span>
                Selected Provider: <strong className="text-foreground">{activeCandidate.vendor_name}</strong>
              </span>
              <span>
                Sats: <strong className="font-mono text-amber-500">{activeCandidate.amount_sats} sats</strong>
              </span>
              {activeCandidate.score !== undefined && (
                <span>
                  Composite Score: <strong className="font-mono text-emerald-500">{activeCandidate.score}/100</strong>
                </span>
              )}
            </div>
          </div>
        );
      })()}
    </div>
  );
}

export default VendorRFQ;
