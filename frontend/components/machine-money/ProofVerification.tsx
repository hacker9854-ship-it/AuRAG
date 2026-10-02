"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle2, XCircle, ShieldCheck, Copy, Check, Hash, Key, RefreshCw } from "lucide-react";
import { verifyPaymentPreimage } from "@/lib/crypto";

export interface ProofVerificationProps {
  preimage?: string;
  paymentHash?: string;
  isMock?: boolean;
  className?: string;
  autoVerify?: boolean;
}

export function ProofVerification({
  preimage = "",
  paymentHash = "",
  isMock = true,
  className = "",
  autoVerify = true,
}: ProofVerificationProps) {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    isValid: boolean;
    computedHash: string;
    expectedHash: string;
  } | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const runVerification = async () => {
    if (!preimage || !paymentHash) return;
    setIsVerifying(true);
    try {
      const res = await verifyPaymentPreimage(preimage, paymentHash);
      setVerificationResult(res);
    } finally {
      setIsVerifying(false);
    }
  };

  useEffect(() => {
    let isCancelled = false;
    if (autoVerify && preimage && paymentHash) {
      verifyPaymentPreimage(preimage, paymentHash).then((res) => {
        if (!isCancelled) {
          setVerificationResult(res);
          setIsVerifying(false);
        }
      });
    }
    return () => {
      isCancelled = true;
    };
  }, [preimage, paymentHash, autoVerify]);

  const copyToClipboard = async (text: string, fieldName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
    } catch {
      setCopiedField(null);
    }
  };

  if (!paymentHash) {
    return (
      <div
        data-testid="proof-verification-empty"
        className="p-4 border border-dashed border-border rounded-xl text-xs text-muted-foreground text-center"
      >
        Awaiting payment settlement for cryptographic proof verification
      </div>
    );
  }

  const isVerified = verificationResult?.isValid;

  return (
    <div
      data-testid="proof-verification-card"
      className={`p-4 bg-card border border-border/80 rounded-xl shadow-sm text-foreground space-y-3 ${className}`}
    >
      {/* Header with Verification Status */}
      <div className="flex items-center justify-between pb-2 border-b border-border/60">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary" />
          <h4 className="text-xs font-semibold uppercase tracking-wider">
            Cryptographic Proof Verification
          </h4>
        </div>
        <div>
          {isVerified ? (
            <span
              data-testid="proof-status-badge"
              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wider uppercase border ${
                isMock
                  ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
                  : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
              }`}
            >
              <CheckCircle2 className="w-3 h-3 text-current" />
              {isMock
                ? "SIMULATED CRYPTOGRAPHIC VERIFICATION"
                : "CRYPTOGRAPHIC PROOF VERIFIED"}
            </span>
          ) : (
            <span
              data-testid="proof-status-badge"
              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wider uppercase bg-muted text-muted-foreground border border-border"
            >
              {isVerifying ? (
                <>
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  Verifying...
                </>
              ) : (
                "Unverified"
              )}
            </span>
          )}
        </div>
      </div>

      {/* Proof Formula Explainer */}
      <div className="p-2.5 bg-muted/40 rounded-lg border border-border/40 font-mono text-[11px] text-muted-foreground flex items-center justify-between">
        <span>Formula: SHA-256(Preimage) == PaymentHash</span>
        <button
          type="button"
          data-testid="reverify-button"
          onClick={runVerification}
          disabled={isVerifying || !preimage}
          className="text-[10px] font-sans px-2 py-0.5 bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded transition-colors"
        >
          {isVerifying ? "Verifying..." : "Verify Proof"}
        </button>
      </div>

      {/* Payment Hash Row */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Hash className="w-3 h-3" />
            Payment Hash (r_hash):
          </span>
          <button
            type="button"
            onClick={() => copyToClipboard(paymentHash, "hash")}
            className="flex items-center gap-0.5 hover:text-foreground transition-colors"
          >
            {copiedField === "hash" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>Copy</span>
          </button>
        </div>
        <div
          data-testid="proof-payment-hash"
          className="p-2 bg-slate-950 text-slate-100 font-mono text-[10px] rounded border border-slate-800 break-all select-all"
        >
          {paymentHash}
        </div>
      </div>

      {/* Preimage Row */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Key className="w-3 h-3 text-amber-500" />
            Settlement Preimage (secret proof):
          </span>
          {preimage && (
            <button
              type="button"
              onClick={() => copyToClipboard(preimage, "preimage")}
              className="flex items-center gap-0.5 hover:text-foreground transition-colors"
            >
              {copiedField === "preimage" ? (
                <Check className="w-3 h-3 text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
              <span>Copy</span>
            </button>
          )}
        </div>
        <div
          data-testid="proof-preimage"
          className="p-2 bg-slate-950 text-slate-100 font-mono text-[10px] rounded border border-slate-800 break-all select-all"
        >
          {preimage || "Preimage will be disclosed upon settlement confirmation"}
        </div>
      </div>

      {/* Verification Result Feedback */}
      {verificationResult && (
        <div
          data-testid="verification-result-box"
          className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 ${
            verificationResult.isValid
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-300"
              : "bg-rose-500/10 border-rose-500/30 text-rose-800 dark:text-rose-300"
          }`}
        >
          {verificationResult.isValid ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
          )}
          <div className="space-y-0.5">
            <p className="font-semibold">
              {verificationResult.isValid
                ? "Cryptographic Match Confirmed"
                : "Hash Mismatch Detected"}
            </p>
            <p className="text-[11px] opacity-90 font-mono">
              {isMock
                ? "SHA-256(preimage) matches the simulated payment hash. Proof is authentic and unforgeable under deterministic evaluation."
                : "SHA-256(preimage) matches the on-chain/Lightning payment hash. Proof is authentic and unforgeable."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProofVerification;
