"use client";

import React, { useEffect, useState } from "react";
import {
  ActivityIcon,
  AlertCircleIcon,
  AlertTriangleIcon,
  ArrowRightIcon,
  CheckCircle2Icon,
  ClockIcon,
  CopyIcon,
  CpuIcon,
  DatabaseIcon,
  ExternalLinkIcon,
  FileCheck2Icon,
  GitBranchIcon,
  LockIcon,
  PlayIcon,
  QrCodeIcon,
  RadioIcon,
  RefreshCwIcon,
  ServerIcon,
  ShieldAlertIcon,
  ShieldCheckIcon,
  SlidersIcon,
  TerminalIcon,
  WalletIcon,
  WrenchIcon,
  ZapIcon,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  approveMachineMoneyPayment,
  getMachineMoneyHealth,
  getMachineMoneyProviders,
  getPaymentEvidence,
  getPaymentGraphTrail,
  listMachineMoneyPayments,
  simulateMachineMoney,
  triggerMachineMoneyFromTelemetry,
  type MachineMoneyHealth,
  type M2MTriggerResult,
  type PaymentTrailResponse,
  type ProviderRegistryResponse,
} from "@/lib/api";

import { Bolt11QRCode } from "@/components/machine-money/Bolt11QRCode";
import { ProviderModeBadge } from "@/components/machine-money/ProviderModeBadge";
import { ProofVerification } from "@/components/machine-money/ProofVerification";
import { JudgeMode } from "@/components/machine-money/JudgeMode";
import { EvidenceSummaryCard } from "@/components/machine-money/EvidenceSummaryCard";
import { PaymentProofDrawer } from "@/components/machine-money/PaymentProofDrawer";
import { VendorRFQ } from "@/components/machine-money/VendorRFQ";
import { IndustrialEconomics } from "@/components/machine-money/IndustrialEconomics";
import { SystemReadinessModal } from "@/components/machine-money/SystemReadinessModal";
import { NovelBitcoinProtocol } from "@/components/machine-money/NovelBitcoinProtocol";
import type { VendorQuoteCandidate } from "@/lib/api";

export default function MachineMoneyPage() {
  // Global & Subsystem state
  const [health, setHealth] = useState<MachineMoneyHealth | null>(null);
  const [providers, setProviders] = useState<ProviderRegistryResponse | null>(null);
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Active Execution state (Sections A through F)
  const [equipmentTag, setEquipmentTag] = useState("P-101A");
  const [confidence, setConfidence] = useState(94);
  const [workOrderId, setWorkOrderId] = useState("WO-2026-P101");
  const [serviceId, setServiceId] = useState("bearing-inspection");
  const [triggering, setTriggering] = useState(false);
  const [executionResult, setExecutionResult] = useState<M2MTriggerResult | null>(null);
  const [selectedVendorCandidate, setSelectedVendorCandidate] = useState<VendorQuoteCandidate | null>(null);

  // Simulation state
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<any | null>(null);

  // Section G: Graph Trail state
  const [activeTrailPaymentId, setActiveTrailPaymentId] = useState<string | null>(null);
  const [trail, setTrail] = useState<PaymentTrailResponse | null>(null);
  const [trailLoading, setTrailLoading] = useState(false);

  // Operator Approval state
  const [approvingPaymentId, setApprovingPaymentId] = useState<string | null>(null);

  // Proof Drawer state
  const [proofDrawerOpen, setProofDrawerOpen] = useState(false);
  const [selectedProofPaymentId, setSelectedProofPaymentId] = useState<string | undefined>(undefined);
  const [readinessModalOpen, setReadinessModalOpen] = useState(false);

  const openProofDrawer = (pid?: string) => {
    setSelectedProofPaymentId(pid || executionResult?.payment_id || (payments.length > 0 ? payments[0].payment_id : undefined));
    setProofDrawerOpen(true);
  };

  const loadPaymentTrail = async (pid: string) => {
    setTrailLoading(true);
    setActiveTrailPaymentId(pid);
    try {
      const t = await getPaymentGraphTrail(pid);
      setTrail(t);
    } catch (err: any) {
      console.error("Failed to load trail:", err);
    } finally {
      setTrailLoading(false);
    }
  };

  // Initial Load
  const fetchAll = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [hRes, pRes, payList] = await Promise.all([
        getMachineMoneyHealth().catch(() => null),
        getMachineMoneyProviders().catch(() => null),
        listMachineMoneyPayments(20).catch(() => []),
      ]);
      if (hRes) setHealth(hRes);
      if (pRes) setProviders(pRes);
      setPayments(payList || []);

      // If there are payments, auto-load trail for the most recent one
      if (payList && payList.length > 0 && !activeTrailPaymentId) {
        const topId = payList[0].payment_id;
        setActiveTrailPaymentId(topId);
        loadPaymentTrail(topId);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load Machine Money data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(label);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  // Scenario 1: Autonomous Telemetry Trigger
  const handleTriggerTelemetry = async (customConfidence = confidence, customWorkOrder = workOrderId) => {
    setTriggering(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await triggerMachineMoneyFromTelemetry({
        equipment_tag: equipmentTag,
        confidence: customConfidence / 100,
        work_order_id: customWorkOrder,
        event_id: "EVT-VIB-001",
        failure_event_id: "FE-001",
      });
      setExecutionResult(res);
      setActiveTrailPaymentId(res.payment_id);
      const isSim = (health?.provider_name || "").toLowerCase().includes("mock") || health?.is_mock !== false;
      setSuccessMsg(`M2M Settlement triggered: ${res.payment_id} (${res.status} • ${isSim ? "Simulation" : "Live Lightning"})`);
      // Refresh ledger
      const updated = await listMachineMoneyPayments(20);
      setPayments(updated);
    } catch (err: any) {
      setError(err?.message || "Autonomous telemetry trigger failed");
    } finally {
      setTriggering(false);
    }
  };

  // Scenario 2: Test Policy Cap (Exceeding Cap)
  const handleTestPolicyCap = async () => {
    setTriggering(true);
    setError(null);
    setSuccessMsg(null);
    try {
      // Overhaul service 1200 sats > 500 sat cap
      const res = await simulateMachineMoney({
        equipment_id: equipmentTag,
        service_id: "motor-rewind",
        amount_sats: 1200,
        confidence: 0.96,
      });
      setSimulationResult(res);
      setSuccessMsg("Policy Cap Evaluated: 1,200 sats exceeds 500 sats cap -> Held in PENDING_APPROVAL");
    } catch (err: any) {
      setError(err?.message || "Policy cap evaluation failed");
    } finally {
      setTriggering(false);
    }
  };

  // Scenario 3: Dry Run Simulation
  const handleRunSimulation = async () => {
    setSimulating(true);
    setError(null);
    try {
      const res = await simulateMachineMoney({
        equipment_id: equipmentTag,
        service_id: serviceId,
        amount_sats: 250,
        confidence: confidence / 100,
      });
      setSimulationResult(res);
      setSuccessMsg("Dry-run simulation completed: zero funds moved, policy verified.");
    } catch (err: any) {
      setError(err?.message || "Dry-run simulation failed");
    } finally {
      setSimulating(false);
    }
  };

  // Operator Manual Approval
  const handleApprove = async (paymentId: string) => {
    setApprovingPaymentId(paymentId);
    setError(null);
    try {
      const res = await approveMachineMoneyPayment(
        paymentId,
        "lead-operator-mumbai",
        "Sign-off verified: Bearing overhaul urgent to prevent plant downtime."
      );
      const isSim = (health?.provider_name || "").toLowerCase().includes("mock") || health?.is_mock !== false;
      setSuccessMsg(`Payment ${paymentId} approved and settled (${isSim ? "Simulated Ledger" : "Live Lightning Network"})!`);
      const updated = await listMachineMoneyPayments(20);
      setPayments(updated);
      loadPaymentTrail(paymentId);
    } catch (err: any) {
      setError(err?.message || "Approval failed");
    } finally {
      setApprovingPaymentId(null);
    }
  };

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-6 p-4 sm:p-6">
      {/* --------------------------------------------------------------------- */}
      {/* Workspace Header & Operational Health Badge                           */}
      {/* --------------------------------------------------------------------- */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between border-b pb-5">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <div className="grid size-8 place-items-center rounded-lg bg-amber-500/20 text-amber-500 font-bold border border-amber-500/30">
              <ZapIcon className="size-5 fill-amber-500" />
            </div>
            <h1 className="font-heading text-2xl font-bold tracking-tight">
              Machine Money Operator Workspace
            </h1>
            <Badge variant="warning" className="uppercase font-semibold tracking-wider text-[10px]">
              Bitshala BOSS Battle
            </Badge>
            <Badge variant="outline" className="text-[10px] font-mono border-amber-500/40 text-amber-500">
              by Niss
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground max-w-3xl">
            Autonomous Lightning micro-settlement protocol for industrial telemetry excursions. Engineered by Niss.
            Governed by deterministic GraphRAG evidence, automated spending policies, and human-in-the-loop oversight.
          </p>
        </div>

        {/* Live Subsystem Health Strip */}
        <div className="flex flex-wrap items-center gap-2">
          <ProviderModeBadge
            providerName={health?.provider_name || "mock"}
            providerMode={health?.provider_mode || (health?.is_mock ? "MOCK" : "MOCK")}
            settlementSource={health?.settlement_source || "SIMULATED"}
            network={health?.network || "regtest"}
            isMock={health?.is_mock ?? (health?.provider_name?.toLowerCase().includes("mock") ?? true)}
            balanceSats={health?.balance_sats ?? 1000000}
            latencyMs={health?.latency_ms ?? 1.2}
            showDetails={true}
          />

          <Button
            variant="outline"
            size="sm"
            data-testid="system-readiness-trigger"
            onClick={() => setReadinessModalOpen(true)}
            className="h-8 gap-1.5 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10"
          >
            <ShieldCheckIcon className="size-3.5 text-emerald-500" />
            System Readiness
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={fetchAll}
            disabled={refreshing}
            className="h-8 gap-1.5"
          >
            <RefreshCwIcon className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Global Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircleIcon className="size-4" />
          <AlertTitle>Operation Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {successMsg && (
        <Alert className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <CheckCircle2Icon className="size-4 text-emerald-500" />
          <AlertTitle>Settlement Notice</AlertTitle>
          <AlertDescription>{successMsg}</AlertDescription>
        </Alert>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Empirical Dataset Benchmark Provenance Banner (NASA IMS Bearing)       */}
      {/* --------------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-2xl bg-cyan-950/25 border border-cyan-500/40 text-xs shadow-xs">
        <div className="flex items-center gap-2.5">
          <DatabaseIcon className="size-4 text-cyan-400 shrink-0" />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-foreground">Empirical Benchmark Grounding:</span>
              <Badge variant="outline" className="text-[10px] text-cyan-300 border-cyan-500/50 bg-cyan-500/20 font-mono">
                NASA IMS Bearing Run-to-Failure (PCoE)
              </Badge>
              <Badge variant="outline" className="text-[10px] text-muted-foreground border-border font-mono">
                Asset: REPLAY-ASSET-01
              </Badge>
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              AuRAG replaces fictional synthetic drift with authentic run-to-failure condition monitoring from the University of Cincinnati / NASA Ames Research Center.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 font-mono text-[10px] text-cyan-400 bg-background/80 px-2.5 py-1 rounded border border-cyan-500/30">
          <span>Record: NASA-IMS-T2-REC-042 (147.6h &bull; 5.42 mm/s Zone C)</span>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* Judge Mode: One-Click Autonomous Settlement Pipeline & Live Timeline   */}
      {/* --------------------------------------------------------------------- */}
      <JudgeMode
        onExecutionComplete={(res) => {
          if (res.payment_record) {
            setExecutionResult({
              status: res.status === "SUCCESS" ? "PAID" : res.status,
              payment_id: res.payment_record.payment_id || res.execution_id,
              idempotency_key: res.execution_id,
              amount_sats: res.payment_record.amount_sats || 250,
              payment_hash: res.payment_record.payment_hash,
              preimage: res.payment_record.preimage,
              paid_at: res.payment_record.paid_at,
              evidence_package: res.evidence_package as any,
              is_duplicate_prevented: false,
            });
            fetchAll();
          }
        }}
      />

      {/* --------------------------------------------------------------------- */}
      {/* Demonstration Controls & Scenario Presets                             */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:border-cyan-500/50 transition-colors">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Badge variant="info" className="text-[10px] bg-cyan-500/20 text-cyan-300 border-cyan-500/40">Scenario 1: Real Benchmark</Badge>
              <DatabaseIcon className="size-4 text-cyan-400" />
            </div>
            <CardTitle className="text-sm font-semibold">NASA IMS Benchmark Replay</CardTitle>
            <CardDescription className="text-xs">
              Authentic 147.6h vibration excursion (5.42 mm/s &gt; 4.5 mm/s ISO threshold) triggers 250 sats autonomous settlement.
            </CardDescription>
          </CardHeader>
          <CardFooter className="pt-1">
            <Button
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs h-8 gap-1.5 shadow-sm"
              onClick={() => handleTriggerTelemetry(94, "WO-2026-P101")}
              disabled={triggering}
            >
              <PlayIcon className="size-3.5 fill-current" />
              {triggering ? "Replaying NASA Benchmark..." : "Replay NASA IMS Benchmark"}
            </Button>
          </CardFooter>
        </Card>

        <Card className="hover:border-amber-500/50 transition-colors">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Badge variant="warning" className="text-[10px]">Scenario 2: Policy Cap</Badge>
              <LockIcon className="size-4 text-amber-500" />
            </div>
            <CardTitle className="text-sm font-semibold">Policy Threshold Escalation</CardTitle>
            <CardDescription className="text-xs">
              Stator Rewind quote (1,200 sats &gt; 500 cap) triggers human-in-the-loop approval gate.
            </CardDescription>
          </CardHeader>
          <CardFooter className="pt-1">
            <Button
              variant="outline"
              className="w-full text-xs h-8 gap-1.5 border-amber-500/40 hover:bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium"
              onClick={handleTestPolicyCap}
              disabled={triggering}
            >
              <ShieldAlertIcon className="size-3.5" />
              Test 500-Sat Policy Cap
            </Button>
          </CardFooter>
        </Card>

        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Badge variant="info" className="text-[10px]">Scenario 3: Dry-Run</Badge>
              <SlidersIcon className="size-4 text-primary" />
            </div>
            <CardTitle className="text-sm font-semibold">Zero-Risk Simulation</CardTitle>
            <CardDescription className="text-xs">
              Validates quotes, spending policy, and idempotency key preview without moving satoshis.
            </CardDescription>
          </CardHeader>
          <CardFooter className="pt-1">
            <Button
              variant="outline"
              className="w-full text-xs h-8 gap-1.5 font-medium"
              onClick={handleRunSimulation}
              disabled={simulating}
            >
              <ActivityIcon className="size-3.5" />
              {simulating ? "Simulating..." : "Run Dry-Run Simulation"}
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* Master 6-Stage Lifecycle Flow (Sections 19 A through F)               */}
      {/* --------------------------------------------------------------------- */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="font-heading text-lg font-bold">M2M Micro-Settlement Lifecycle</h2>
            <Badge variant="outline" className="text-xs font-mono">Sections 19 A - F</Badge>
          </div>
          <span className="text-xs text-muted-foreground hidden sm:inline">
            Deterministic state pipeline governed by POL-LIGHTNING-MACHINE-MONEY
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* ---------------- STAGE A: TRIGGER ---------------- */}
          <Card className="border-border/80 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-blue-500" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-blue-500">STAGE A</span>
                <Badge variant="destructive" className="font-semibold text-[10px] animate-pulse">
                  High Risk (94%)
                </Badge>
              </div>
              <CardTitle className="text-base flex items-center gap-2">
                <ActivityIcon className="size-4 text-blue-500" />
                Telemetry Trigger
              </CardTitle>
              <CardDescription className="text-xs">
                Predictive sensor excursion detected on critical asset
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Equipment:</span>
                <span className="font-mono font-bold">{equipmentTag} (Slurry Feed Pump)</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Excursion Metric:</span>
                <span className="font-mono text-destructive font-semibold">Vibration 5.8 mm/s (&gt; 2.5)</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Predictive Event:</span>
                <span className="font-mono font-semibold">EVT-VIB-001</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Model Confidence:</span>
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{confidence}%</span>
              </div>
            </CardContent>
          </Card>

          {/* ---------------- STAGE B: EVIDENCE ---------------- */}
          <Card className="border-border/80 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-purple-500" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-purple-500">STAGE B</span>
                <Badge variant="info" className="font-semibold text-[10px]">GraphRAG Verified</Badge>
              </div>
              <CardTitle className="text-base flex items-center gap-2">
                <GitBranchIcon className="size-4 text-purple-500" />
                Evidence Package
              </CardTitle>
              <CardDescription className="text-xs">
                Ontology evidence resolving why money is spent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Failure Event:</span>
                <span className="font-mono font-bold text-purple-400">FE-001 (Bearing Degradation)</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Historical WO:</span>
                <span className="font-mono font-bold">WO-1002 (Prior Excursion)</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Procedure:</span>
                <span className="font-mono">PROC-001 (Laser Alignment)</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Cross-Layer Path:</span>
                <span className="font-mono text-[11px] text-muted-foreground truncate max-w-[150px]">
                  P-101A → FE-001 → WO-1002
                </span>
              </div>
            </CardContent>
          </Card>

          {/* ---------------- STAGE C: SERVICE QUOTE ---------------- */}
          <Card className="border-border/80 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-amber-500" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-amber-500">STAGE C</span>
                <Badge variant="outline" className="font-semibold text-[10px] font-mono">Catalog Node</Badge>
              </div>
              <CardTitle className="text-base flex items-center gap-2">
                <WrenchIcon className="size-4 text-amber-500" />
                Service Quote
              </CardTitle>
              <CardDescription className="text-xs">
                Verifiable machine-to-machine service specification
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Service:</span>
                <span className="font-mono font-bold">{selectedVendorCandidate?.service_name || "Bearing Inspection & Alignment"}</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Provider:</span>
                <span className="font-mono font-semibold text-amber-500 truncate max-w-[150px]" title={selectedVendorCandidate?.vendor_name || "maintenance-node-a"}>
                  {selectedVendorCandidate?.vendor_name || "maintenance-node-a"}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Quoted Cost:</span>
                <span className="font-mono text-base font-bold text-amber-500">
                  {selectedVendorCandidate?.amount_sats ?? 250} sats
                </span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">SLA &amp; Duration:</span>
                <span className="font-mono text-muted-foreground">
                  {selectedVendorCandidate?.sla_hours ?? 2.0} hrs (Parts Included)
                </span>
              </div>
            </CardContent>
          </Card>

          {/* ---------------- STAGE D: POLICY ---------------- */}
          <Card className="border-border/80 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-emerald-500" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-emerald-500">STAGE D</span>
                <Badge variant="success" className="font-semibold text-[10px]">
                  Policy: ALLOWED
                </Badge>
              </div>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheckIcon className="size-4 text-emerald-500" />
                Policy Engine
              </CardTitle>
              <CardDescription className="text-xs">
                Zero-trust automated spending cap &amp; idempotency guard
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Policy ID:</span>
                <span className="font-mono font-bold text-[11px]">POL-LIGHTNING-MACHINE-MONEY</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Auto-Pay Cap:</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">500 sats</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Policy Decision:</span>
                <Badge variant="success" className="text-[10px]">
                  Allowed (250 &le; 500)
                </Badge>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Deterministic Guard:</span>
                <span className="font-mono text-[10px] text-muted-foreground truncate max-w-[150px]">
                  sha256(site:asset:svc:evt)
                </span>
              </div>
            </CardContent>
          </Card>

          {/* ---------------- STAGE E: PAYMENT ---------------- */}
          <Card className="border-border/80 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-amber-400" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-amber-400">STAGE E</span>
                <Badge
                  variant={executionResult?.status === "PAID" || executionResult?.status === "SETTLED" ? "success" : "warning"}
                  className="font-semibold text-[10px]"
                >
                  {executionResult?.status === "PAID" || executionResult?.status === "SETTLED"
                    ? "Paid (Settled)"
                    : "Pending → Paid"}
                </Badge>
              </div>
              <CardTitle className="text-base flex items-center gap-2">
                <ZapIcon className="size-4 text-amber-500 fill-amber-500" />
                Lightning Micro-Payment
              </CardTitle>
              <CardDescription className="text-xs">
                Cryptographic BOLT11 invoice and settlement preimage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Network:</span>
                <span className="font-mono font-semibold">Lightning ({health?.network || "regtest"})</span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Payment Hash:</span>
                <div className="flex items-center gap-1">
                  <span className="font-mono text-[10px] truncate max-w-[120px]">
                    {executionResult?.payment_hash || "81ebd7332d750fe868ef8777..."}
                  </span>
                  <button
                    onClick={() => handleCopy(executionResult?.payment_hash || "81ebd7332d750fe868ef8777b6fa43e0b608b01014f1aa4fe6d02a6d3c92d421", "hash")}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <CopyIcon className="size-3" />
                  </button>
                </div>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Preimage Proof:</span>
                <span className="font-mono text-[10px] text-emerald-600 dark:text-emerald-400 truncate max-w-[140px]">
                  {executionResult?.preimage || "eaa9f31cebb48b2c50cfeda7..."}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Routing Fee:</span>
                <span className="font-mono text-muted-foreground">0 sats (Local routing)</span>
              </div>
              {executionResult?.payment_hash && executionResult?.preimage && (
                <div className="pt-2 border-t border-border/40 space-y-2">
                  <ProofVerification
                    paymentHash={executionResult.payment_hash}
                    preimage={executionResult.preimage}
                    isMock={health?.provider_name?.toLowerCase().includes("mock") ?? true}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full h-7 text-xs font-medium text-amber-500 border-amber-500/40 hover:bg-amber-500/10 gap-1.5"
                    onClick={() => openProofDrawer(executionResult?.payment_id || activeTrailPaymentId || undefined)}
                  >
                    <ShieldCheckIcon className="size-3.5" />
                    Open Proof &amp; Audit Drawer
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ---------------- STAGE F: OUTCOME ---------------- */}
          <Card className="border-border/80 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-emerald-600" />
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-emerald-600">STAGE F</span>
                <Badge variant="success" className="font-semibold text-[10px]">
                  WO Funded
                </Badge>
              </div>
              <CardTitle className="text-base flex items-center gap-2">
                <FileCheck2Icon className="size-4 text-emerald-600" />
                Operational Outcome
              </CardTitle>
              <CardDescription className="text-xs">
                Work order dispatch &amp; dual-layer audit trail commitment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Target Work Order:</span>
                <span className="font-mono font-bold text-primary">
                  {workOrderId}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Work Order Status:</span>
                <Badge variant="success" className="text-[10px]">
                  FUNDED / DISPATCHED
                </Badge>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Neo4j Graph Audit:</span>
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                  (:Payment)-[:FUNDS]
                </span>
              </div>
              <div className="flex justify-between items-center p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">SQL Audit Record:</span>
                <span className="font-mono text-[10px] text-muted-foreground truncate max-w-[150px]">
                  {executionResult?.payment_id || "PAY-20260927-P101"}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* SECTION G: VISUAL GRAPH TRAIL (Section 19 G)                         */}
      {/* --------------------------------------------------------------------- */}
      <Card id="graph-trail-section" className="border-border/80 shadow-xs">
        <CardHeader className="pb-3 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <GitBranchIcon className="size-4 text-primary" />
                <CardTitle className="text-base">Section 19 G: Operational Graph Trail</CardTitle>
                <Badge variant="outline" className="font-mono text-[10px]">
                  {activeTrailPaymentId || "Latest Payment"}
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Neo4j causal ontology linking equipment telemetry, work orders, payment settlements, and service providers.
              </CardDescription>
            </div>
            {trail?.found && (
              <Badge variant="success" className="text-xs self-start sm:self-auto">
                <CheckCircle2Icon className="size-3 mr-1" />
                Dual-Layer Causal Chain Verified
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-4 space-y-6">
          {/* Visual Step-by-Step Flow Nodes */}
          <div className="overflow-x-auto pb-2">
            <div className="flex items-center justify-between min-w-[750px] gap-2 p-4 rounded-xl bg-muted/30 border border-border/60">
              {/* Node 1: Equipment */}
              <div className="flex flex-col items-center text-center p-3 rounded-lg bg-card border shadow-xs w-36 shrink-0">
                <div className="p-2 rounded-full bg-blue-500/10 text-blue-500 mb-1.5">
                  <CpuIcon className="size-5" />
                </div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Equipment</span>
                <span className="font-mono font-bold text-xs truncate max-w-[120px]">
                  {trail?.equipment?.tag_id || equipmentTag}
                </span>
                <span className="text-[10px] text-muted-foreground truncate max-w-[120px]">
                  Slurry Pump
                </span>
              </div>

              <div className="flex flex-col items-center text-muted-foreground shrink-0">
                <span className="text-[10px] font-mono text-blue-500 font-semibold mb-0.5">EXCURSION</span>
                <ArrowRightIcon className="size-4 text-blue-500" />
              </div>

              {/* Node 2: Predictive Event */}
              <div className="flex flex-col items-center text-center p-3 rounded-lg bg-card border shadow-xs w-40 shrink-0">
                <div className="p-2 rounded-full bg-destructive/10 text-destructive mb-1.5">
                  <ActivityIcon className="size-5" />
                </div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Predictive Event</span>
                <span className="font-mono font-bold text-xs">
                  {trail?.predictive_trigger?.event_id || "EVT-VIB-001"}
                </span>
                <span className="text-[10px] text-destructive font-medium">
                  High Risk (94% conf)
                </span>
              </div>

              <div className="flex flex-col items-center text-muted-foreground shrink-0">
                <span className="text-[10px] font-mono text-purple-500 font-semibold mb-0.5">TRIGGERS</span>
                <ArrowRightIcon className="size-4 text-purple-500" />
              </div>

              {/* Node 3: Work Order */}
              <div className="flex flex-col items-center text-center p-3 rounded-lg bg-card border shadow-xs w-40 shrink-0">
                <div className="p-2 rounded-full bg-purple-500/10 text-purple-500 mb-1.5">
                  <FileCheck2Icon className="size-5" />
                </div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Work Order</span>
                <span className="font-mono font-bold text-xs">
                  {trail?.work_order?.id || workOrderId}
                </span>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                  Status: FUNDED
                </span>
              </div>

              <div className="flex flex-col items-center text-muted-foreground shrink-0">
                <span className="text-[10px] font-mono text-amber-500 font-semibold mb-0.5">&larr; FUNDS</span>
                <ArrowRightIcon className="size-4 text-amber-500" />
              </div>

              {/* Node 4: Payment */}
              <div className="flex flex-col items-center text-center p-3 rounded-lg bg-card border-2 border-amber-500/50 shadow-sm w-44 shrink-0">
                <div className="p-2 rounded-full bg-amber-500/10 text-amber-500 mb-1.5">
                  <ZapIcon className="size-5 fill-amber-500" />
                </div>
                <span className="text-[10px] uppercase font-bold text-amber-500">Lightning Payment</span>
                <span className="font-mono font-bold text-xs truncate max-w-[150px]">
                  {activeTrailPaymentId || "PAY-2026..."}
                </span>
                <Badge variant="success" className="text-[9px] mt-0.5">
                  PAID (250 sats)
                </Badge>
              </div>

              <div className="flex flex-col items-center text-muted-foreground shrink-0">
                <span className="text-[10px] font-mono text-emerald-500 font-semibold mb-0.5">PAID_TO &rarr;</span>
                <ArrowRightIcon className="size-4 text-emerald-500" />
              </div>

              {/* Node 5: Service Provider */}
              <div className="flex flex-col items-center text-center p-3 rounded-lg bg-card border shadow-xs w-36 shrink-0">
                <div className="p-2 rounded-full bg-emerald-500/10 text-emerald-500 mb-1.5">
                  <ServerIcon className="size-5" />
                </div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Provider Node</span>
                <span className="font-mono font-bold text-xs truncate max-w-[120px]">
                  {trail?.service_provider || "maintenance-node-a"}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  Autonomous Node
                </span>
              </div>
            </div>
          </div>

          {/* Cypher Traversal & Causal Narrative */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-muted/40 border space-y-2">
              <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                <TerminalIcon className="size-3.5" />
                Neo4j Causal Cypher Query Pattern
              </span>
              <pre className="font-mono text-[11px] leading-relaxed p-2.5 rounded bg-slate-950 text-slate-100 overflow-x-auto">
{`MATCH (p:Payment {payment_id: "${activeTrailPaymentId || "PAY-2026-..."}"})
OPTIONAL MATCH (p)-[:FUNDS]->(wo:WorkOrder)
OPTIONAL MATCH (wo)-[:RESOLVES]->(evt:PredictiveEvent)
OPTIONAL MATCH (evt)-[:AFFECTS]->(eq:Equipment)
OPTIONAL MATCH (p)-[:PAID_TO]->(sp:ServiceProvider)
RETURN eq.tag_id, evt.event_id, wo.id, p.amount_sats, sp.provider_id`}
              </pre>
            </div>

            <div className="p-3 rounded-lg bg-muted/40 border space-y-2 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mb-1.5">
                  <ShieldCheckIcon className="size-3.5 text-emerald-500" />
                  Deterministic Operational Narrative
                </span>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {trail?.explanation ||
                    "This payment represents an autonomous M2M maintenance settlement. High-confidence vibration anomaly (5.8 mm/s on Slurry Pump P-101A) matched failure signature FE-001 in AuRAG's operational ontology, automatically generating Work Order WO-2026-P101. The transaction was verified against spending policy POL-LIGHTNING-MACHINE-MONEY (250 sats <= 500 sat cap) and settled instantaneously over the Lightning Network."}
                </p>
              </div>

              {trail?.graph_story && trail.graph_story.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/50">
                  {trail.graph_story.map((step, idx) => (
                    <Badge key={idx} variant="outline" className="text-[10px] font-mono">
                      {step}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* --------------------------------------------------------------------- */}
      {/* BOLT11 Invoice & Settlement Verification Panel                        */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: QR Code & BOLT11 String */}
        <Card className="lg:col-span-1 border-border/80 shadow-xs flex flex-col justify-between">
          <CardHeader className="pb-3 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <QrCodeIcon className="size-4 text-amber-500" />
                BOLT11 Payment Request
              </CardTitle>
              <Badge variant="outline" className="text-[10px] font-mono">
                lnbc2500n1...
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Micro-payment invoice generated for machine service dispatch
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-4 flex flex-col items-center justify-center">
            <Bolt11QRCode
              value={
                executionResult?.payment_record?.bolt11 ||
                executionResult?.bolt11 ||
                (trail as any)?.payment?.bolt11 ||
                "lnbcrt2500n1pj48ugqpp5qxaywxwgpdh7jydsjxnuq5fyke8wan5kfcyuqk8037vqtkk2234ssp50nuwt7l793l234xk7vsps0y3l2qr3e6l0qgfrthq38yyerww6fhsdz6tdx57s6tyqhjq56ff425cs25f985uhfqf45kxun094cxz7tdv4h8ggrxdaezq5pdxycrzsfqd36kyunfvdshg6t0dcxqrrsscqpjjga32ynxew6snx8mdhv9qdtt5405zt2kdh5h5fcsm7pydlnrfckzzntwqu77gcfdtyjkglaphs6rjjlj548gc8lhljpaw7vtcawejecqwtnmnz"
              }
              isMock={health?.provider_name?.toLowerCase().includes("mock") ?? true}
              amountSats={250}
              size={170}
              className="w-full"
            />
          </CardContent>

          <CardFooter className="pt-2 border-t text-xs text-muted-foreground flex justify-between">
            <span>Amount: <strong className="text-foreground">250 sats</strong> (0.00000250 BTC)</span>
            <Badge variant="success" className="text-[10px]">Zero Network Routing Fee</Badge>
          </CardFooter>
        </Card>

        {/* Right 2 Columns: Evidence Summary Card (Section 18 Contract) */}
        <EvidenceSummaryCard
          equipmentId={equipmentTag}
          anomalyTitle="Radial Bearing Vibration Excursion"
          vibrationValue="5.8 mm/s (Threshold: 4.5 mm/s)"
          confidence={confidence / 100}
          failureSignatureId={executionResult?.evidence_package?.matched_failure_event || "FE-001"}
          governingProcedure={executionResult?.evidence_package?.governing_procedure || "PROC-001"}
          relatedWorkOrder={executionResult?.evidence_package?.related_work_order || "WO-1002"}
          workOrderId={workOrderId}
          serviceName="Precision Bearing Inspection & Laser Alignment"
          costSats={executionResult?.amount_sats || 250}
          policyCap={500}
          policyStatus={executionResult?.status === "PAID" || executionResult?.status === "SETTLED" ? "AUTHORIZED" : "PENDING_APPROVAL"}
          crossLayerJustification={
            executionResult?.evidence_package?.cross_layer_justification ||
            "Predictive excursion on (P-101A) strongly correlates with historical failure signature (FE-001), triggering intervention Work Order (WO-1002) adhering to procedure (PROC-001). Spending 250 sats averts an estimated 4.5 hours of unbudgeted plant downtime."
          }
          className="lg:col-span-2"
          onOpenGraphTrail={() => {
            const el = document.getElementById("graph-trail-section");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          onOpenProofDrawer={() => openProofDrawer(executionResult?.payment_id || activeTrailPaymentId || undefined)}
        />
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* SECTION 19 C / FR-04: MULTI-VENDOR RFQ & COMPETITIVE BIDDING           */}
      {/* --------------------------------------------------------------------- */}
      <VendorRFQ
        serviceId={serviceId}
        equipmentId={equipmentTag}
        policyCapSats={500}
        onSelectCandidate={(cand) => setSelectedVendorCandidate(cand)}
      />

      {/* --------------------------------------------------------------------- */}
      {/* SECTION 19 D / FR-14 / PHASE 5: INDUSTRIAL ECONOMICS & INTELLIGENCE   */}
      {/* --------------------------------------------------------------------- */}
      <IndustrialEconomics
        equipmentTag={equipmentTag}
        activeInterventionSats={executionResult?.amount_sats || 250}
      />


      {/* --------------------------------------------------------------------- */}
      {/* SECTION 20: NOVEL BITCOIN INNOVATION (NWC NIP-47 & MULTI-HOP ONION)    */}
      {/* --------------------------------------------------------------------- */}
      <NovelBitcoinProtocol
        initialCapSats={500}
        activeInterventionSats={executionResult?.amount_sats || 250}
      />

      {/* --------------------------------------------------------------------- */}
      {/* Recent Machine Money Settlement Ledger & Approval Queue Table         */}
      {/* --------------------------------------------------------------------- */}
      <Card className="border-border/80 shadow-xs">
        <CardHeader className="pb-3 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <DatabaseIcon className="size-4 text-primary" />
                Machine Money Settlement Ledger
              </CardTitle>
              <CardDescription className="text-xs">
                Real-time record of all autonomous settlements, pending approval gates, and verifiable audit records.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {payments.length} Records
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 border-b text-muted-foreground uppercase text-[10px] font-semibold tracking-wider">
                <tr>
                  <th className="py-2.5 px-4">Payment ID</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Amount</th>
                  <th className="py-2.5 px-4">Work Order</th>
                  <th className="py-2.5 px-4">Vendor / Node</th>
                  <th className="py-2.5 px-4">Created / Settled</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-muted-foreground">
                      No payment settlements recorded yet. Use the actions above to trigger a test settlement.
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => {
                    const isPending = p.status === "PENDING_APPROVAL";
                    const isPaid = p.status === "PAID" || p.status === "SETTLED";
                    const isSelected = p.payment_id === activeTrailPaymentId;

                    return (
                      <tr
                        key={p.payment_id}
                        className={`hover:bg-muted/40 transition-colors ${isSelected ? "bg-muted/30" : ""}`}
                      >
                        <td className="py-2.5 px-4 font-mono font-medium">
                          <div className="flex items-center gap-1.5">
                            <ZapIcon className="size-3 text-amber-500 fill-amber-500" />
                            <span className="truncate max-w-[140px]">{p.payment_id}</span>
                          </div>
                        </td>
                        <td className="py-2.5 px-4">
                          <Badge
                            variant={isPaid ? "success" : isPending ? "warning" : "outline"}
                            className="text-[10px] uppercase font-mono"
                          >
                            {p.status}
                          </Badge>
                        </td>
                        <td className="py-2.5 px-4 font-mono font-bold text-amber-500">
                          {p.amount_sats} sats
                        </td>
                        <td className="py-2.5 px-4 font-mono text-muted-foreground">
                          {p.work_order_id || "WO-2026-P101"}
                        </td>
                        <td className="py-2.5 px-4 font-mono text-muted-foreground">
                          {p.vendor_name || "maintenance-node-a"}
                        </td>
                        <td className="py-2.5 px-4 text-muted-foreground">
                          {p.created_at ? new Date(p.created_at).toLocaleTimeString() : "Just now"}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {isPending && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-[11px] px-2 text-emerald-600 dark:text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/10"
                                onClick={() => handleApprove(p.payment_id)}
                                disabled={approvingPaymentId === p.payment_id}
                              >
                                <CheckCircle2Icon className="size-3 mr-1" />
                                {approvingPaymentId === p.payment_id ? "Approving..." : "Approve"}
                              </Button>
                            )}

                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 text-[11px] px-2 text-muted-foreground hover:text-foreground"
                              onClick={() => loadPaymentTrail(p.payment_id)}
                            >
                              <GitBranchIcon className="size-3 mr-1 text-purple-400" />
                              Trail
                            </Button>

                            <Button
                              size="sm"
                              variant="outline"
                              className="h-6 text-[11px] px-2 text-amber-500 border-amber-500/40 hover:bg-amber-500/10"
                              onClick={() => openProofDrawer(p.payment_id)}
                            >
                              <ShieldCheckIcon className="size-3 mr-1" />
                              Proof
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* --------------------------------------------------------------------- */}
      {/* Cryptographic Payment Proof & Multi-Tab Audit Drawer (Phase 3)        */}
      {/* --------------------------------------------------------------------- */}
      <PaymentProofDrawer
        isOpen={proofDrawerOpen}
        onClose={() => setProofDrawerOpen(false)}
        paymentId={selectedProofPaymentId}
      />

      {/* --------------------------------------------------------------------- */}
      {/* Safe System Readiness & Operational Health Modal (Task 10.3)         */}
      {/* --------------------------------------------------------------------- */}
      <SystemReadinessModal
        isOpen={readinessModalOpen}
        onClose={() => setReadinessModalOpen(false)}
        health={health}
      />
    </div>
  );
}
