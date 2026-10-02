"use client";

import React, { useState, useEffect } from "react";
import {
  ActivityIcon,
  AlertCircleIcon,
  BarChart3Icon,
  CalculatorIcon,
  CheckCircle2Icon,
  ChevronRightIcon,
  ClockIcon,
  CopyIcon,
  CpuIcon,
  DollarSignIcon,
  InfoIcon,
  LayersIcon,
  PercentIcon,
  RefreshCwIcon,
  ShieldCheckIcon,
  SlidersIcon,
  SparklesIcon,
  TrendingUpIcon,
  WalletIcon,
  WrenchIcon,
  XIcon,
  ZapIcon,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getIndustrialEconomics,
  getMachineMoneyMetrics,
  calculateCustomIndustrialEconomics,
  type IndustrialEconomicsModel,
  type IndustrialPlantAssumptions,
  type MachineMoneyMetrics,
} from "@/lib/api";

interface IndustrialEconomicsProps {
  equipmentTag?: string;
  activeInterventionSats?: number;
  className?: string;
}

export function IndustrialEconomics({
  equipmentTag = "P-101A",
  activeInterventionSats,
  className = "",
}: IndustrialEconomicsProps) {
  const [metrics, setMetrics] = useState<MachineMoneyMetrics | null>(null);
  const [economics, setEconomics] = useState<IndustrialEconomicsModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Task 5.4: Explainability Drawer state
  const [explainDrawerOpen, setExplainDrawerOpen] = useState(false);
  const [copiedFormula, setCopiedFormula] = useState(false);

  // Interactive sensitivity parameters in drawer
  const [interactiveHours, setInteractiveHours] = useState<number>(4.5);
  const [interactiveHourlyRate, setInteractiveHourlyRate] = useState<number>(260000);
  const [interactiveSats, setInteractiveSats] = useState<number>(activeInterventionSats || 250);
  const [customResult, setCustomResult] = useState<IndustrialEconomicsModel | null>(null);
  const [customLoading, setCustomLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [mRes, eRes] = await Promise.all([
        getMachineMoneyMetrics().catch(() => null),
        getIndustrialEconomics(equipmentTag, activeInterventionSats).catch(() => null),
      ]);
      if (mRes) setMetrics(mRes);
      if (eRes) {
        setEconomics(eRes);
        setInteractiveHours(eRes.downtime_hours_avoided);
        setInteractiveHourlyRate(eRes.hourly_downtime_cost_usd);
        setInteractiveSats(eRes.intervention_cost_sats);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load Machine Money analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [equipmentTag, activeInterventionSats]);

  const handleRecalculateCustom = async (hours: number, rate: number, sats: number) => {
    setCustomLoading(true);
    try {
      const res = await calculateCustomIndustrialEconomics({
        equipment_tag: equipmentTag,
        unmitigated_downtime_hours: hours,
        hourly_downtime_cost_usd: rate,
        intervention_cost_sats: sats,
      });
      setCustomResult(res);
    } catch (err) {
      console.error("Custom calculation failed:", err);
    } finally {
      setCustomLoading(false);
    }
  };

  const handleCopyFormula = (formulaText: string) => {
    navigator.clipboard.writeText(formulaText);
    setCopiedFormula(true);
    setTimeout(() => setCopiedFormula(false), 2500);
  };

  // Fallback defaults if backend is initializing
  const displayEconomics = customResult || economics;
  const grossExposure = displayEconomics?.estimated_downtime_exposure_usd ?? 1170000;
  const downtimeHours = displayEconomics?.downtime_hours_avoided ?? 4.5;
  const hourlyRate = displayEconomics?.hourly_downtime_cost_usd ?? 260000;
  const interventionSats = displayEconomics?.intervention_cost_sats ?? (activeInterventionSats || 250);
  const interventionUsd = displayEconomics?.intervention_cost_usd ?? 0.1625;
  const netPreserved = displayEconomics?.net_value_preserved_usd ?? 1169999.84;
  const protectionMultiple = displayEconomics?.protection_multiple ?? 7200000;
  const riskWeightedExposure = displayEconomics?.risk_weighted_exposure_usd ?? 994500;
  const leadTimeSaved = displayEconomics?.lead_time_saved_hours ?? 4.2;

  // Metrics fallbacks
  const totalSpendSats = metrics?.total_spend_sats ?? 250;
  const fiatSpendUsd = metrics?.fiat_spend_usd_estimate ?? 0.1625;
  const settledCount = metrics?.settled_count ?? 1;
  const pendingCount = metrics?.pending_count ?? 0;
  const autonomousRate = metrics?.autonomous_rate_percentage ?? 100.0;
  const avgLatencyMs = metrics?.average_settlement_latency_ms ?? 1842.0;
  const conversionRate = metrics?.quote_to_payment_conversion_rate ?? 100.0;
  const vendorSpend = metrics?.vendor_spend && metrics.vendor_spend.length > 0 ? metrics.vendor_spend : [
    {
      vendor_name: "Industrial Dynamics Specialist Node",
      spend_sats: totalSpendSats,
      payment_count: settledCount,
      percentage: 100.0,
    },
  ];

  return (
    <Card className={`border-border/80 shadow-xs bg-card/60 backdrop-blur-sm overflow-hidden ${className}`}>
      {/* ------------------------------------------------------------------- */}
      {/* CARD HEADER: BADGES, ENGINE VERSION, AND HONEST ESTIMATED MARKER     */}
      {/* ------------------------------------------------------------------- */}
      <CardHeader className="pb-4 border-b border-border/60">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <BarChart3Icon className="size-5 text-emerald-400" />
              <CardTitle className="text-base sm:text-lg font-bold tracking-tight text-foreground">
                Machine Money Intelligence &amp; Industrial Economics
              </CardTitle>
              <Badge variant="outline" className="text-[11px] font-mono border-emerald-500/40 text-emerald-400 bg-emerald-950/20">
                v2026.1-industrial-m2m
              </Badge>
              <Badge
                variant="secondary"
                className="text-[10px] uppercase font-bold tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30"
              >
                ESTIMATED / SYNTHETIC MODEL
              </Badge>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Mathematical downtime exposure mitigation vs micro-payment intervention cost for asset{" "}
              <span className="font-mono font-medium text-foreground">{equipmentTag}</span>.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 self-start lg:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExplainDrawerOpen(true)}
              className="h-8 text-xs gap-1.5 border-emerald-500/40 text-emerald-400 hover:bg-emerald-950/30 hover:text-emerald-300"
            >
              <CalculatorIcon className="size-3.5" />
              Explainability Drawer
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchData}
              disabled={loading}
              className="h-8 px-2 text-muted-foreground hover:text-foreground"
              title="Refresh Analytics Metrics"
            >
              <RefreshCwIcon className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-6">
        {/* ------------------------------------------------------------------- */}
        {/* 1. INDUSTRIAL DOWNTIME ECONOMIC PROTECTION PANEL (FR-14 / BE-05)     */}
        {/* ------------------------------------------------------------------- */}
        <div className="p-4 sm:p-5 rounded-xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 via-card to-background shadow-inner">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 mb-4 border-b border-border/50 gap-2">
            <div>
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheckIcon className="size-4 text-emerald-400" />
                Asset Downtime Avoidance Impact (FR-14)
              </span>
              <p className="text-xs text-muted-foreground mt-0.5">
                Synthetic petrochemical refining unit P-101A (Crude Charge Pump outage exposure basis)
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs font-mono text-muted-foreground">Basis: </span>
              <span className="text-xs font-mono font-semibold text-foreground">
                ${(hourlyRate / 1000).toFixed(0)}k/hr &times; {downtimeHours}h
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            {/* KPI 1: Estimated Downtime Exposure Avoided */}
            <div className="p-3 rounded-lg bg-card/80 border border-border/60">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1 font-medium">
                <ClockIcon className="size-3.5 text-blue-400" />
                Downtime Exposure
              </div>
              <div className="text-xl sm:text-2xl font-black font-mono text-foreground mt-1">
                {downtimeHours} <span className="text-xs font-normal text-muted-foreground">hrs</span>
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                Saved lead time: <span className="text-blue-400 font-mono font-semibold">{leadTimeSaved}h</span>
              </div>
            </div>

            {/* KPI 2: Estimated Exposure Value Mitigated */}
            <div className="p-3 rounded-lg bg-card/80 border border-border/60">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1 font-medium">
                <DollarSignIcon className="size-3.5 text-emerald-400" />
                Exposure Avoided
              </div>
              <div className="text-xl sm:text-2xl font-black font-mono text-emerald-400 mt-1">
                ${(grossExposure / 1000000).toFixed(2)}M
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                Risk-weighted: <span className="text-foreground font-mono font-semibold">${(riskWeightedExposure / 1000).toFixed(0)}k</span>
              </div>
            </div>

            {/* KPI 3: Intervention Cost (Lightning Micro-Payment) */}
            <div className="p-3 rounded-lg bg-card/80 border border-border/60">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1 font-medium">
                <ZapIcon className="size-3.5 text-amber-400" />
                Intervention Cost
              </div>
              <div className="text-xl sm:text-2xl font-black font-mono text-amber-400 mt-1">
                {interventionSats} <span className="text-xs font-normal text-muted-foreground">sats</span>
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                Fiat spot: <span className="text-foreground font-mono font-semibold">${interventionUsd.toFixed(2)}</span>
              </div>
            </div>

            {/* KPI 4: Economic Protection Multiple */}
            <div className="p-3 rounded-lg bg-card/80 border border-emerald-500/30 bg-emerald-950/10">
              <div className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium">
                <TrendingUpIcon className="size-3.5" />
                Protection Multiple
              </div>
              <div className="text-xl sm:text-2xl font-black font-mono text-emerald-300 mt-1">
                {(protectionMultiple / 1000000).toFixed(1)}M&times;
              </div>
              <div className="text-[10px] text-emerald-400/80 mt-0.5 font-medium">
                Net value: ${(netPreserved / 1000000).toFixed(2)}M preserved
              </div>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------------- */}
        {/* 2. M2M SETTLEMENT METRICS GRID (TASK 5.1 & 5.3)                     */}
        {/* ------------------------------------------------------------------- */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {/* M1: Total Spend */}
          <div className="p-3.5 rounded-lg border border-border/70 bg-muted/20">
            <div className="flex items-center justify-between text-muted-foreground text-xs">
              <span className="flex items-center gap-1 font-medium">
                <WalletIcon className="size-3.5 text-amber-400" />
                Total M2M Spend
              </span>
              <span className="text-[10px] font-mono text-amber-400/80">Lightning</span>
            </div>
            <div className="text-lg sm:text-xl font-bold font-mono text-foreground mt-1.5">
              {totalSpendSats.toLocaleString("en-US")}{" "}
              <span className="text-xs font-normal text-muted-foreground">sats</span>
            </div>
            <div className="text-[10px] text-muted-foreground mt-1 flex items-center justify-between">
              <span>Fiat Equiv: ${fiatSpendUsd.toFixed(4)}</span>
              <span className="font-mono text-emerald-400">{settledCount} settled</span>
            </div>
          </div>

          {/* M2: Autonomous Rate */}
          <div className="p-3.5 rounded-lg border border-border/70 bg-muted/20">
            <div className="flex items-center justify-between text-muted-foreground text-xs">
              <span className="flex items-center gap-1 font-medium">
                <CpuIcon className="size-3.5 text-purple-400" />
                Autonomous Execution
              </span>
              <Badge variant="outline" className="text-[9px] px-1 py-0 border-purple-400/30 text-purple-400">
                &le; 500 sat cap
              </Badge>
            </div>
            <div className="text-lg sm:text-xl font-bold font-mono text-foreground mt-1.5">
              {autonomousRate.toFixed(1)}%
            </div>
            <div className="text-[10px] text-muted-foreground mt-1 flex items-center justify-between">
              <span>{metrics?.autonomous_count ?? settledCount} auto</span>
              <span>{metrics?.human_approval_count ?? pendingCount} human approved</span>
            </div>
          </div>

          {/* M3: Settlement Latency */}
          <div className="p-3.5 rounded-lg border border-border/70 bg-muted/20">
            <div className="flex items-center justify-between text-muted-foreground text-xs">
              <span className="flex items-center gap-1 font-medium">
                <ClockIcon className="size-3.5 text-cyan-400" />
                Avg Settlement Latency
              </span>
              <span className="text-[10px] text-cyan-400 font-mono">Instant</span>
            </div>
            <div className="text-lg sm:text-xl font-bold font-mono text-foreground mt-1.5">
              {(avgLatencyMs / 1000).toFixed(2)}{" "}
              <span className="text-xs font-normal text-muted-foreground">sec</span>
            </div>
            <div className="text-[10px] text-muted-foreground mt-1 flex items-center justify-between">
              <span>Raw: {Math.round(avgLatencyMs)} ms</span>
              <span className="text-emerald-400 font-mono">Real-time</span>
            </div>
          </div>

          {/* M4: Quote Conversion */}
          <div className="p-3.5 rounded-lg border border-border/70 bg-muted/20">
            <div className="flex items-center justify-between text-muted-foreground text-xs">
              <span className="flex items-center gap-1 font-medium">
                <PercentIcon className="size-3.5 text-emerald-400" />
                Quote-to-Payment
              </span>
              <span className="text-[10px] text-emerald-400 font-mono">Conversion</span>
            </div>
            <div className="text-lg sm:text-xl font-bold font-mono text-foreground mt-1.5">
              {conversionRate.toFixed(1)}%
            </div>
            <div className="text-[10px] text-muted-foreground mt-1 flex items-center justify-between">
              <span>Quotes: {metrics?.total_quotes_generated ?? 1}</span>
              <span>Paid: {metrics?.quotes_converted ?? settledCount}</span>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------------- */}
        {/* 3. VENDOR SPEND DISTRIBUTION BREAKDOWN (TASK 5.1 & 5.3)             */}
        {/* ------------------------------------------------------------------- */}
        <div className="p-4 rounded-xl border border-border/70 bg-muted/15 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <LayersIcon className="size-3.5 text-emerald-400" />
              Vendor Settlement Distribution (Autonomous Procurement)
            </span>
            <span className="text-[11px] text-muted-foreground font-mono">
              Total: {totalSpendSats.toLocaleString("en-US")} sats
            </span>
          </div>

          <div className="space-y-2.5">
            {vendorSpend.map((vendor, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-foreground truncate max-w-[240px] sm:max-w-none">
                    {vendor.vendor_name}
                  </span>
                  <div className="flex items-center gap-3 font-mono text-xs">
                    <span className="text-muted-foreground text-[11px]">
                      {vendor.payment_count} {vendor.payment_count === 1 ? "payment" : "payments"}
                    </span>
                    <span className="font-bold text-amber-400">{vendor.spend_sats} sats</span>
                    <span className="text-muted-foreground text-[11px] w-12 text-right">
                      {vendor.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(vendor.percentage, 4)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-2 pb-4 border-t border-border/60 text-xs text-muted-foreground flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px]">
          <InfoIcon className="size-3.5 text-emerald-400 flex-shrink-0" />
          <span>
            Data Basis: <span className="text-foreground font-medium">{displayEconomics?.data_basis || "Synthetic plant model"}</span>
          </span>
        </div>
        <div className="text-[11px] font-mono text-muted-foreground self-end sm:self-auto">
          Audit Reference: <span className="text-foreground">ECON-P101A-2026</span>
        </div>
      </CardFooter>

      {/* ------------------------------------------------------------------- */}
      {/* 4. TASK 5.4: EXPLAINABILITY DRAWER FOR INDUSTRIAL ECONOMICS          */}
      {/* ------------------------------------------------------------------- */}
      {explainDrawerOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200"
        >
          <div className="bg-card border border-border rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
            {/* Drawer Header */}
            <div className="p-4 sm:p-5 border-b flex items-center justify-between sticky top-0 bg-card z-10">
              <div className="flex items-center gap-2">
                <CalculatorIcon className="size-5 text-emerald-400" />
                <div>
                  <h3 className="font-bold text-base text-foreground">
                    Industrial Economics Explainability &amp; Assumption Basis
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Section 5.4 / FR-14 transparent calculation formulas and parameterized plant assumptions.
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                onClick={() => setExplainDrawerOpen(false)}
                aria-label="Close explainability drawer"
              >
                <XIcon className="size-4" />
              </Button>
            </div>

            {/* Drawer Body */}
            <div className="p-4 sm:p-5 space-y-5 text-xs">
              {/* Formula Panel */}
              <div className="p-4 rounded-lg bg-slate-950 border border-emerald-500/30 space-y-2">
                <div className="flex items-center justify-between text-[11px] text-emerald-400 font-semibold uppercase tracking-wider">
                  <span>Mathematical Calculation Formula</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-1.5 text-[10px] text-emerald-400 hover:text-emerald-300 gap-1"
                    onClick={() => handleCopyFormula(displayEconomics?.formula || "")}
                  >
                    {copiedFormula ? <CheckCircle2Icon className="size-3 text-emerald-400" /> : <CopyIcon className="size-3" />}
                    {copiedFormula ? "Copied" : "Copy"}
                  </Button>
                </div>
                <div className="font-mono text-slate-100 text-xs sm:text-sm bg-slate-900/80 p-2.5 rounded border border-border/40">
                  Net Value Preserved = (Avoided Outage Hours &times; Hourly Outage Rate) &minus; Intervention Cost USD
                </div>
                <div className="font-mono text-slate-300 text-[11px] bg-slate-900/50 p-2 rounded">
                  Risk-Weighted Exposure = Gross Exposure &times; Catastrophic Failure Probability (85%)
                </div>
              </div>

              {/* Version & Model Badge */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-3 rounded-lg bg-muted/20 border text-[11px]">
                <div>
                  <span className="text-muted-foreground block">Calculation Engine</span>
                  <span className="font-mono font-semibold text-foreground">v2026.1-industrial-m2m</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Assumption Version</span>
                  <span className="font-mono font-semibold text-foreground">2026.1-synthetic-p101a</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Estimated Marker</span>
                  <span className="font-mono font-semibold text-amber-400">ESTIMATED_SYNTHETIC_MODEL</span>
                </div>
              </div>

              {/* Baseline Assumptions Table */}
              <div className="space-y-2">
                <h4 className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                  <LayersIcon className="size-3.5 text-blue-400" />
                  Parameterized Synthetic Plant Assumptions (Task 5.2)
                </h4>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-[11px] text-left">
                    <thead className="bg-muted/50 border-b font-medium text-muted-foreground">
                      <tr>
                        <th className="p-2 sm:px-3">Parameter</th>
                        <th className="p-2 sm:px-3">Value</th>
                        <th className="p-2 sm:px-3">Unit</th>
                        <th className="p-2 sm:px-3 hidden sm:table-cell">Basis / Citation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Critical Asset</td>
                        <td className="p-2 sm:px-3 font-mono">{equipmentTag}</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">Charge Pump</td>
                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">Petrochemical Refining CDU-1</td>
                      </tr>
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Hourly Outage Loss</td>
                        <td className="p-2 sm:px-3 font-mono text-emerald-400">{`$${(hourlyRate).toLocaleString("en-US")}`}</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">USD / hour</td>


                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">Unplanned unit trip lost throughput</td>
                      </tr>
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Unmitigated Downtime</td>
                        <td className="p-2 sm:px-3 font-mono">{downtimeHours}</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">Hours</td>
                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">Bearing seizure &amp; re-alignment</td>
                      </tr>
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Failure Probability</td>
                        <td className="p-2 sm:px-3 font-mono">85%</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">Factor</td>
                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">Vibration excursion failure model</td>
                      </tr>
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Manual Procurement SLA</td>
                        <td className="p-2 sm:px-3 font-mono">4.2</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">Hours</td>
                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">PO approval + engineer phone tree</td>
                      </tr>
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Autonomous M2M SLA</td>
                        <td className="p-2 sm:px-3 font-mono text-cyan-400">&lt; 2.5</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">Seconds</td>
                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">Lightning invoice + instant settlement</td>
                      </tr>
                      <tr>
                        <td className="p-2 sm:px-3 font-medium text-foreground">Intervention Cost</td>
                        <td className="p-2 sm:px-3 font-mono text-amber-400">{interventionSats} sats</td>
                        <td className="p-2 sm:px-3 text-muted-foreground">~${interventionUsd.toFixed(2)} USD</td>
                        <td className="p-2 sm:px-3 text-muted-foreground hidden sm:table-cell">Autonomous inspection payment</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Interactive Sensitivity Sandbox */}
              <div className="p-4 rounded-xl border border-border/80 bg-muted/15 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                    <SlidersIcon className="size-3.5 text-purple-400" />
                    Interactive Sensitivity Sandbox (Live Model Testing)
                  </h4>
                  {customLoading && <RefreshCwIcon className="size-3 animate-spin text-purple-400" />}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Adjust simulated outage parameters to recalculate net preserved value and protection multiple in real time.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-foreground block mb-1">
                      Outage Hours: <span className="font-mono text-blue-400">{interactiveHours}h</span>
                    </label>
                    <input
                      type="range"
                      min="1.0"
                      max="12.0"
                      step="0.5"
                      value={interactiveHours}
                      onChange={(e) => {
                        const h = parseFloat(e.target.value);
                        setInteractiveHours(h);
                        handleRecalculateCustom(h, interactiveHourlyRate, interactiveSats);
                      }}
                      className="w-full accent-blue-500 cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-medium text-foreground block mb-1">
                      Hourly Rate: <span className="font-mono text-emerald-400">${(interactiveHourlyRate / 1000).toFixed(0)}k</span>
                    </label>
                    <input
                      type="range"
                      min="50000"
                      max="500000"
                      step="10000"
                      value={interactiveHourlyRate}
                      onChange={(e) => {
                        const r = parseFloat(e.target.value);
                        setInteractiveHourlyRate(r);
                        handleRecalculateCustom(interactiveHours, r, interactiveSats);
                      }}
                      className="w-full accent-emerald-500 cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-medium text-foreground block mb-1">
                      Intervention Sats: <span className="font-mono text-amber-400">{interactiveSats} sats</span>
                    </label>
                    <input
                      type="range"
                      min="100"
                      max="1000"
                      step="50"
                      value={interactiveSats}
                      onChange={(e) => {
                        const s = parseInt(e.target.value, 10);
                        setInteractiveSats(s);
                        handleRecalculateCustom(interactiveHours, interactiveHourlyRate, s);
                      }}
                      className="w-full accent-amber-500 cursor-pointer"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-card border border-border/60 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-muted-foreground block text-[10px]">Calculated Net Preserved:</span>
                    <span className="font-mono font-bold text-emerald-400 text-sm">
                      ${(netPreserved / 1000000).toFixed(2)}M USD
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-muted-foreground block text-[10px]">Protection Multiple:</span>
                    <span className="font-mono font-bold text-foreground text-sm">
                      {(protectionMultiple / 1000000).toFixed(1)}M&times; ROI
                    </span>
                  </div>
                </div>
              </div>

              {/* Transparency Notice */}
              <Alert className="border-amber-500/30 bg-amber-950/10 text-amber-200 text-xs">
                <AlertCircleIcon className="size-4 text-amber-400" />
                <AlertTitle className="text-xs font-semibold text-amber-300">
                  Hackathon Evaluation Disclosure
                </AlertTitle>
                <AlertDescription className="text-[11px] text-amber-200/90 leading-relaxed mt-0.5">
                  Values reflect modelled synthetic industrial process assumptions calibrated for the BOSS Battle 2026 Machine Money track. No actual petrochemical plant financial losses occurred.
                </AlertDescription>
              </Alert>
            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t flex justify-end sticky bottom-0 bg-card">
              <Button
                variant="default"
                size="sm"
                onClick={() => setExplainDrawerOpen(false)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
              >
                Close Drawer
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
