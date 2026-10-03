"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  ShieldCheck,
  Receipt,
  GitBranch,
  FileText,
  Lock,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { getPaymentProofPackage, type ProofPackageResponse } from "@/lib/api";
import { Bolt11QRCode } from "./Bolt11QRCode";
import { ProofVerification } from "./ProofVerification";
import { ProviderModeBadge } from "./ProviderModeBadge";

export interface PaymentProofDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  paymentId?: string;
  initialProofPackage?: ProofPackageResponse | null;
  className?: string;
}

export function PaymentProofDrawer({
  isOpen,
  onClose,
  paymentId,
  initialProofPackage,
  className = "",
}: PaymentProofDrawerProps) {
  const [data, setData] = useState<ProofPackageResponse | null>(initialProofPackage || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"crypto" | "invoice" | "graph" | "audit">("crypto");

  useEffect(() => {
    if (initialProofPackage) {
      setData(initialProofPackage);
      return;
    }
    if (isOpen && paymentId) {
      setLoading(true);
      setError(null);
      getPaymentProofPackage(paymentId)
        .then((res) => setData(res))
        .catch((err) => setError(err?.message || "Failed to load proof package."))
        .finally(() => setLoading(false));
    }
  }, [isOpen, paymentId, initialProofPackage]);

  if (!isOpen) return null;

  return (
    <div
      data-testid="payment-proof-drawer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="proof-drawer-title"
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in-0 duration-200 ${className}`}
    >
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-card border border-border shadow-2xl rounded-3xl flex flex-col overflow-hidden text-foreground">
        {/* Header */}
        <div className="p-5 border-b border-border/60 flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10 text-primary">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="proof-drawer-title" className="font-bold text-base font-heading">
                  Payment Proof &amp; Operational Audit Package
                </h3>
                <span className="font-mono text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border/40">
                  {data?.identity.payment_id || paymentId || "PAY-UNKNOWN"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Cryptographic verification, BOLT11 invoice, and Neo4j operational lineage.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              data-testid="proof-drawer-close-button"
              aria-label="Close payment proof drawer"
              onClick={onClose}
              className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-primary outline-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          role="tablist"
          aria-label="Proof package categories"
          className="flex items-center px-3 sm:px-5 border-b border-border/60 bg-muted/10 text-xs font-semibold gap-1 overflow-x-auto"
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "crypto"}
            data-testid="proof-tab-crypto"
            onClick={() => setActiveTab("crypto")}
            className={`py-3 px-3.5 border-b-2 flex items-center gap-1.5 transition-colors focus-visible:ring-2 focus-visible:ring-primary outline-none ${
              activeTab === "crypto"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Cryptographic Proof</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "invoice"}
            data-testid="proof-tab-invoice"
            onClick={() => setActiveTab("invoice")}
            className={`py-3 px-3.5 border-b-2 flex items-center gap-1.5 transition-colors focus-visible:ring-2 focus-visible:ring-primary outline-none ${
              activeTab === "invoice"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Receipt className="w-3.5 h-3.5" />
            <span>BOLT11 Invoice &amp; QR</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "graph"}
            data-testid="proof-tab-graph"
            onClick={() => setActiveTab("graph")}
            className={`py-3 px-3.5 border-b-2 flex items-center gap-1.5 transition-colors focus-visible:ring-2 focus-visible:ring-primary outline-none ${
              activeTab === "graph"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>Operational Graph Lineage</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "audit"}
            data-testid="proof-tab-audit"
            onClick={() => setActiveTab("audit")}
            className={`py-3 px-3.5 border-b-2 flex items-center gap-1.5 transition-colors focus-visible:ring-2 focus-visible:ring-primary outline-none ${
              activeTab === "audit"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Audit Ledger</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {loading && (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <span>Fetching cryptographic proof package...</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-600 dark:text-rose-400">
              {error}
            </div>
          )}

          {!loading && data && (
            <>
              {/* Tab 1: Cryptographic Proof */}
              {activeTab === "crypto" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold">SHA-256 Preimage Verification</h4>
                      <p className="text-xs text-muted-foreground">
                        Lightning network payments reveal a 32-byte secret preimage upon settlement whose SHA-256 hash equals the payment hash.
                      </p>
                    </div>
                    <ProviderModeBadge
                      providerName={data.provider_mode.includes("MOCK") ? "mock" : "lnbits"}
                      providerMode={data.provider_mode.includes("MOCK") ? "MOCK" : "LIVE"}
                      settlementSource={data.provider_mode.includes("MOCK") ? "SIMULATED" : "LIGHTNING_NODE"}
                      isMock={data.provider_mode.includes("MOCK")}
                      network={data.payment.network}
                    />
                  </div>

                  <ProofVerification
                    paymentHash={data.cryptographic_proof.payment_hash}
                    preimage={data.cryptographic_proof.preimage}
                    isMock={data.provider_mode.includes("MOCK")}
                    settlementSource={data.provider_mode.includes("MOCK") ? "SIMULATED" : "LIGHTNING_NODE"}
                  />

                  {/* Settlement Metadata Row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 text-xs">
                    <div className="p-2.5 bg-muted/40 rounded-lg border border-border/40">
                      <span className="text-[10px] text-muted-foreground uppercase">Amount</span>
                      <p className="font-mono font-bold mt-0.5">{data.payment.amount_sats} sats</p>
                    </div>
                    <div className="p-2.5 bg-muted/40 rounded-lg border border-border/40">
                      <span className="text-[10px] text-muted-foreground uppercase">Fee</span>
                      <p className="font-mono font-bold mt-0.5">{data.payment.fee_sats} sats</p>
                    </div>
                    <div className="p-2.5 bg-muted/40 rounded-lg border border-border/40">
                      <span className="text-[10px] text-muted-foreground uppercase">Status</span>
                      <p className="font-bold text-emerald-500 mt-0.5">{data.payment.status}</p>
                    </div>
                    <div className="p-2.5 bg-muted/40 rounded-lg border border-border/40">
                      <span className="text-[10px] text-muted-foreground uppercase">Settled At</span>
                      <p className="font-mono text-[11px] truncate mt-0.5">
                        {data.identity.settled_at?.split("T")[1]?.slice(0, 8) || "Instant"}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: BOLT11 Invoice & QR */}
              {activeTab === "invoice" && (
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-bold">BOLT11 Payment Request</h4>
                    <p className="text-xs text-muted-foreground">
                      Standards-compliant Lightning payment invoice encoded for machine-to-machine dispatch.
                    </p>
                  </div>

                  <div className="max-w-md mx-auto">
                    <Bolt11QRCode
                      value={data.payment.bolt11}
                      isMock={data.provider_mode.includes("MOCK")}
                      amountSats={data.payment.amount_sats}
                    />
                  </div>
                </div>
              )}

              {/* Tab 3: Operational Graph Lineage */}
              {activeTab === "graph" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold">Neo4j Operational Lineage (Graph Trail)</h4>
                      <p className="text-xs text-muted-foreground">
                        Visual chain connecting physical sensor telemetry to financial settlement and work order execution.
                      </p>
                    </div>
                    <span
                      data-testid="graph-lineage-status-badge"
                      className={`font-mono text-[10px] px-2 py-0.5 rounded border font-semibold ${
                        (data.graph_links as any)?.is_fallback !== false
                          ? "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20"
                          : "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      }`}
                    >
                      {(data.graph_links as any)?.is_fallback !== false ? "DEGRADED / FALLBACK" : "LIVE AURA"}
                    </span>
                  </div>

                  {/* Visual Node Chain */}
                  <div className="p-4 bg-muted/30 rounded-2xl border border-border/60 space-y-3">
                    <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                      {data.graph_links.lineage.map((node, i) => (
                        <React.Fragment key={`${node}-${i}`}>
                          <span className="px-2.5 py-1 rounded-lg bg-card border border-border font-semibold shadow-xs">
                            {node}
                          </span>
                          {i < data.graph_links.lineage.length - 1 && (
                            <ArrowRight className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>

                  {/* Operational Context Card */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-muted/40 rounded-xl border border-border/40 space-y-1">
                      <span className="text-[10px] text-muted-foreground uppercase font-mono">Equipment &amp; Work Order</span>
                      <p className="font-semibold text-foreground">
                        {data.operational_context.equipment_id} → {data.operational_context.work_order_id}
                      </p>
                      <p className="text-muted-foreground">{data.operational_context.reason}</p>
                    </div>

                    <div className="p-3 bg-muted/40 rounded-xl border border-border/40 space-y-1">
                      <span className="text-[10px] text-muted-foreground uppercase font-mono">Service Provider &amp; Node</span>
                      <p className="font-semibold text-foreground flex items-center justify-between">
                        <span>{data.operational_context.vendor_name}</span>
                        {data.operational_context.vendor_id && (
                          <span className="text-[9px] font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border/40">
                            {data.operational_context.vendor_id}
                          </span>
                        )}
                      </p>
                      {data.operational_context.vendor_pubkey && (
                        <p className="font-mono text-[10px] text-muted-foreground truncate" title={data.operational_context.vendor_pubkey}>
                          Pubkey: {data.operational_context.vendor_pubkey.slice(0, 16)}...
                        </p>
                      )}
                      <p className="text-muted-foreground">
                        Governing Standard: {data.operational_context.governing_procedure}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Audit & Governance */}
              {activeTab === "audit" && (
                <div className="space-y-4 text-xs">
                  <div>
                    <h4 className="text-sm font-bold">Audit Ledger &amp; Policy Governance</h4>
                    <p className="text-xs text-muted-foreground">
                      Immutable record committed to SQL database and verified against spending policies.
                    </p>
                  </div>

                  <div className="p-4 bg-muted/30 rounded-xl border border-border/60 space-y-3">
                    <div className="grid grid-cols-2 gap-3 font-mono text-[11px]">
                      <div>
                        <span className="text-muted-foreground text-[10px] uppercase">Ledger Status:</span>
                        <p className="font-bold text-emerald-500">{data.audit.audit_ledger_status}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground text-[10px] uppercase">Storage Table:</span>
                        <p className="font-bold text-foreground">{data.audit.table}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground text-[10px] uppercase">Idempotency Key:</span>
                        <p className="font-bold text-foreground truncate">{data.identity.idempotency_key}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground text-[10px] uppercase">Policy Evaluated:</span>
                        <p className="font-bold text-foreground">{data.policy.policy_id} ({data.policy.decision})</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default PaymentProofDrawer;
