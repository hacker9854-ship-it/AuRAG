"use client";

import React, { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { AlertTriangle, Check, Copy, Eye, EyeOff, QrCode, Zap } from "lucide-react";

export interface Bolt11QRCodeProps {
  value: string;
  size?: number;
  isMock?: boolean;
  className?: string;
  label?: string;
  amountSats?: number;
}

/**
 * Validates if the invoice payload follows recognized Lightning BOLT11 invoice conventions.
 * Valid prefixes: lnbc (mainnet), lnbcrt (regtest), lntb (testnet), lntbs (signet).
 */
export function isRecognizedInvoiceFormat(invoice: string): boolean {
  if (!invoice || typeof invoice !== "string") return false;
  const trimmed = invoice.trim().toLowerCase();
  return (
    trimmed.startsWith("lnbc") ||
    trimmed.startsWith("lnbcrt") ||
    trimmed.startsWith("lntb") ||
    trimmed.startsWith("lntbs") ||
    trimmed.startsWith("lnsb")
  );
}

export function Bolt11QRCode({
  value,
  size = 180,
  isMock = true,
  className = "",
  label,
  amountSats,
}: Bolt11QRCodeProps) {
  const [copied, setCopied] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  const handleCopy = async () => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      setCopied(false);
    }
  };

  if (!value) {
    return (
      <div
        data-testid="bolt11-qr-empty"
        className="flex flex-col items-center justify-center p-6 border border-dashed border-border rounded-xl bg-muted/20 text-muted-foreground"
      >
        <QrCode className="w-10 h-10 mb-2 opacity-50" />
        <span className="text-xs">No active BOLT11 invoice</span>
      </div>
    );
  }

  const isValidFormat = isRecognizedInvoiceFormat(value);

  return (
    <div
      data-testid="bolt11-qr-container"
      className={`flex flex-col items-center p-4 bg-card border border-border/80 rounded-2xl shadow-sm text-foreground transition-all ${className}`}
    >
      {/* Provider Mode & Payload Truthfulness Banner */}
      <div className="w-full flex items-center justify-between pb-2 mb-2 border-b border-border/60 text-xs">
        <span className="font-mono text-muted-foreground flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
          {label || (amountSats ? `${amountSats.toLocaleString()} SATS` : "BOLT11 INVOICE")}
        </span>
        <div className="flex items-center gap-1.5">
          <span
            data-testid="qr-mode-indicator"
            className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase ${
              isMock
                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
            }`}
          >
            {isMock ? "MOCK / SIMULATION" : "LIVE LIGHTNING"}
          </span>
        </div>
      </div>

      {/* Malformed Warning if invoice does not follow BOLT11 conventions */}
      {!isValidFormat && (
        <div
          data-testid="bolt11-malformed-warning"
          className="w-full mb-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center gap-2 text-[11px] text-amber-700 dark:text-amber-300"
        >
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500" />
          <span>Non-standard invoice prefix. Handled as raw synthetic payload.</span>
        </div>
      )}

      {/* Real Standards-Compliant QR Code */}
      <div
        data-testid="bolt11-qr-wrapper"
        className="relative p-3 bg-white rounded-xl shadow-inner border border-slate-200 dark:border-slate-800 flex items-center justify-center group"
      >
        <QRCodeSVG
          value={value}
          size={size}
          level="M"
          includeMargin={false}
          className="rounded shape-rendering-crispEdges"
        />
        {/* Central Lightning Bolt Emblem */}
        <div
          data-testid="qr-center-emblem"
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
        >
          <div className="bg-amber-500 text-slate-950 p-1.5 rounded-full shadow-lg border-2 border-white ring-2 ring-amber-500/20">
            <Zap className="w-4 h-4 fill-current" />
          </div>
        </div>
      </div>

      {/* Payload Type Badge */}
      <div className="mt-2">
        <span
          data-testid="payload-type-badge"
          className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/50"
        >
          {isMock ? "SIMULATED PAYMENT PAYLOAD" : "LIVE BOLT11 INVOICE"}
        </span>
      </div>

      {/* Invoice string snippet & Quick Action Buttons */}
      <div className="w-full mt-3 flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 bg-muted/40 px-2.5 py-1 rounded text-[11px] font-mono text-muted-foreground truncate border border-border/40 select-all">
            {value.slice(0, 14)}...{value.slice(-10)}
          </div>
          <button
            type="button"
            data-testid="bolt11-copy-button"
            onClick={handleCopy}
            title="Copy BOLT11 Invoice"
            className="flex items-center gap-1 px-2.5 py-1 bg-primary text-primary-foreground hover:bg-primary/90 rounded text-xs font-medium transition-colors shadow-sm"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
          <button
            type="button"
            data-testid="bolt11-toggle-raw"
            onClick={() => setShowRaw(!showRaw)}
            title={showRaw ? "Hide full invoice" : "View full invoice"}
            className="p-1 hover:bg-muted text-muted-foreground hover:text-foreground rounded transition-colors"
          >
            {showRaw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Expandable Full Raw Text Fallback (FR-01) */}
        {showRaw && (
          <div
            data-testid="bolt11-text-fallback"
            className="mt-1 p-2 bg-slate-950 text-slate-100 rounded text-[10px] font-mono break-all max-h-24 overflow-y-auto border border-slate-800"
          >
            <div className="text-[9px] text-slate-400 mb-1 font-semibold uppercase tracking-wider">
              Exact {isMock ? "Simulated" : "BOLT11"} Payload
            </div>
            {value}
          </div>
        )}
      </div>
    </div>
  );
}

export default Bolt11QRCode;
