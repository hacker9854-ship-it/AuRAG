import Link from "next/link";
import {
  ArrowRightIcon,
  BotIcon,
  BrainCircuitIcon,
  DatabaseZapIcon,
  FileCheck2Icon,
  GaugeIcon,
  NetworkIcon,
  SearchIcon,
  ShieldCheckIcon,
  SparklesIcon,
  WorkflowIcon,
  ZapIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const coverage = [
  {
    label: "Autonomous Settlement",
    value: "Instant",
    detail: "Lightning BOLT11 & Nostr NIP-47 NWC wallet dispatch",
    icon: ZapIcon,
  },
  {
    label: "Evidence-Backed Spend",
    value: "100%",
    detail: "Deterministic GraphRAG: ISO 10816 + SOPs + Work Orders",
    icon: ShieldCheckIcon,
  },
  {
    label: "Empirical Telemetry",
    value: "20 kHz",
    detail: "Real NASA IMS Run-to-Failure accelerometer dataset",
    icon: GaugeIcon,
  },
  {
    label: "Cryptographic Audit Trail",
    value: "08 Classes",
    detail: "Neo4j graph: (Payment)-[:FUNDS]->(WorkOrder)",
    icon: NetworkIcon,
  },
];

const workflow = [
  {
    step: "01",
    title: "SENSE (Telemetry)",
    detail: "Accelerometers detect bearing degradation (NASA IMS 5.42 mm/s Zone C excursion).",
    icon: GaugeIcon,
  },
  {
    step: "02",
    title: "JUSTIFY (GraphRAG)",
    detail: "Deterministic hybrid retrieval validates SOP-001, warranty, and past work orders.",
    icon: BrainCircuitIcon,
  },
  {
    step: "03",
    title: "FEDERATE (Vendor RFQ)",
    detail: "Machine issues competitive RFQs to diagnostic vendors and selects optimal cost/SLA.",
    icon: WorkflowIcon,
  },
  {
    step: "04",
    title: "SETTLE (Lightning)",
    detail: "Autonomous satoshi settlement via Lightning / Nostr NWC with preimage linked to Neo4j.",
    icon: ZapIcon,
  },
];

const knowledgeTypes = [
  "Equipment",
  "Failure events",
  "Work orders",
  "Procedures",
  "Vendor RFQs",
  "Lightning Preimages",
  "Regulatory clauses",
  "Source chunks",
];

export default function CommandCenterPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
      {/* Flagship Hero Section */}
      <section className="overflow-hidden rounded-2xl bg-card shadow-xs ring-1 ring-foreground/10 border border-amber-500/20">
        <div className="grid lg:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
          <div className="flex flex-col justify-center p-6 sm:p-8 lg:p-10">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="warning" className="w-fit bg-amber-500/10 text-amber-500 border-amber-500/30 flex items-center gap-1.5">
                <ZapIcon className="size-3.5 fill-amber-500 text-amber-500" />
                Autonomous Machine Money Protocol
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-cyan-500/40 text-cyan-400 bg-cyan-950/20">
                Bitcoin Lightning & Nostr NWC
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-border/80">
                by Niss
              </Badge>
            </div>

            <h1 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl text-foreground">
              Industrial machines holding sovereign Lightning wallets.
              <span className="block mt-1 text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-amber-300 to-cyan-400">
                Autonomous economic settlement backed by GraphRAG evidence.
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base sm:leading-7">
              AuRAG equips mission-critical industrial assets with sovereign Bitcoin Lightning wallets (BOLT-11 / Nostr NIP-47 NWC).
              When empirical sensors detect imminent failure, the machine autonomously verifies warranty and SOPs via GraphRAG,
              solicits competitive vendor bids, and settles emergency repairs in satoshis — with zero human latency and 100% cryptographic auditability.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button
                size="lg"
                className="bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700 hover:from-amber-600 hover:to-amber-800 text-slate-950 font-bold shadow-lg shadow-amber-500/25 border-0"
                nativeButton={false}
                render={<Link href="/machine-money" />}
              >
                <ZapIcon data-icon="inline-start" className="size-4 fill-slate-950" />
                Launch Machine Money Console
              </Button>

              <Button
                size="lg"
                variant="outline"
                className="border-cyan-500/40 hover:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-medium"
                nativeButton={false}
                render={<Link href="/predictive-watch" />}
              >
                <GaugeIcon data-icon="inline-start" className="size-4" />
                Predictive Telemetry Triggers
              </Button>

              <Button
                size="lg"
                variant="outline"
                nativeButton={false}
                render={<Link href="/investigate" />}
              >
                Inspect GraphRAG Justification Engine
                <ArrowRightIcon data-icon="inline-end" />
              </Button>
            </div>
          </div>

          <div className="flex flex-col justify-between gap-6 border-t bg-muted/20 p-6 lg:border-t-0 lg:border-l lg:p-8">
            <div>
              <div className="text-xs font-semibold tracking-wider text-amber-500 uppercase flex items-center gap-1.5">
                <SparklesIcon className="size-3.5" />
                The Machine Money Thesis
              </div>
              <p className="mt-3 font-heading text-lg font-medium leading-7 text-foreground">
                Autonomous agents cannot make blind payments. GraphRAG is not a search box — it is the machine&apos;s
                deterministic cryptographic justification engine before releasing satoshis.
              </p>
            </div>

            <div className="grid gap-3 font-mono text-xs">
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-1">
                <div className="text-[11px] text-amber-400 font-bold uppercase tracking-wider">
                  Sovereign Settlement Engine
                </div>
                <div className="text-foreground leading-snug">
                  Nostr NIP-47 Wallet Connect + Multi-Hop HTLC Routing settle vendor invoices in milliseconds with zero counterparty risk.
                </div>
              </div>

              <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-4 space-y-1">
                <div className="text-[11px] text-cyan-400 font-bold uppercase tracking-wider">
                  Cryptographic Evidence Justification
                </div>
                <div className="text-foreground leading-snug">
                  Every satoshi spent is bound to empirical NASA IMS sensor data (20 kHz, Zone C breach) and Neo4j operational proof.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Coverage & Architecture Pillars */}
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Platform coverage">
        {coverage.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.label} size="sm" className="border-border/60 hover:border-primary/40 transition-colors">
              <CardHeader>
                <CardTitle className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
                  {item.label}
                </CardTitle>
                <CardAction>
                  <div className="grid size-9 place-items-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="size-4" />
                  </div>
                </CardAction>
              </CardHeader>
              <CardContent>
                <div className="data-mono text-2xl font-bold tracking-tight text-foreground">{item.value}</div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p>
              </CardContent>
            </Card>
          );
        })}
      </section>

      {/* 4-Step Autonomous Machine Money Execution Flow */}
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
        <Card className="border-border/60">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ZapIcon className="size-4 text-amber-500" />
              <CardTitle>How An Autonomous Machine Safely Spends Bitcoin</CardTitle>
            </div>
            <CardDescription>
              From high-frequency sensor spikes to cryptographic satoshi settlement without human delay or hallucination.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {workflow.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.step} className="flex gap-4 rounded-xl border border-border/60 bg-card/60 p-4 hover:border-amber-500/40 transition-colors">
                  <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-amber-500/10 text-amber-500">
                    <Icon className="size-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="data-mono text-xs font-bold text-amber-500">{item.step}</span>
                      <h3 className="font-semibold text-sm text-foreground">{item.title}</h3>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Connected Knowledge Foundation */}
        <Card className="border-border/60">
          <CardHeader>
            <div className="flex items-center gap-2">
              <NetworkIcon className="size-4 text-cyan-400" />
              <CardTitle>Connected Knowledge Foundation</CardTitle>
            </div>
            <CardDescription>
              The operational entity classes ensuring every autonomous Lightning payment has irrefutable provenance.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {knowledgeTypes.map((type) => (
              <Badge key={type} variant="outline" className="px-3 py-1.5 font-mono text-xs bg-muted/40">
                {type}
              </Badge>
            ))}
          </CardContent>
        </Card>
      </section>

      {/* Deep-Dive Workspaces Grid */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-amber-500/30 bg-amber-500/5 hover:border-amber-500 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="warning" className="text-[10px] font-mono">Flagship</Badge>
              <ZapIcon className="size-5 text-amber-500" />
            </div>
            <CardTitle className="mt-2 text-base">Machine Money Console</CardTitle>
            <CardDescription className="text-xs">
              Execute live autonomous settlements, Nostr NIP-47 NWC payments, and multi-hop Lightning HTLC routing.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" className="w-full bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold" nativeButton={false} render={<Link href="/machine-money" />}>
              Open Console <ArrowRightIcon data-icon="inline-end" />
            </Button>
          </CardContent>
        </Card>

        <Card className="border-cyan-500/30 bg-cyan-500/5 hover:border-cyan-500 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-[10px] font-mono border-cyan-500/40 text-cyan-400">NASA IMS Rig</Badge>
              <GaugeIcon className="size-5 text-cyan-400" />
            </div>
            <CardTitle className="mt-2 text-base">Predictive Telemetry</CardTitle>
            <CardDescription className="text-xs">
              Simulate sensor drift and evaluate the NASA IMS bearing benchmark against ISO 10816 failure thresholds.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" variant="outline" className="w-full border-cyan-500/40 hover:bg-cyan-500/10 text-cyan-400" nativeButton={false} render={<Link href="/predictive-watch" />}>
              Open Telemetry <ArrowRightIcon data-icon="inline-end" />
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border/60 hover:border-primary/60 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-[10px] font-mono">Evidence Engine</Badge>
              <SearchIcon className="size-5 text-primary" />
            </div>
            <CardTitle className="mt-2 text-base">GraphRAG Justification</CardTitle>
            <CardDescription className="text-xs">
              Inspect multi-agent reasoning, compliance verification, and citation graph trails justifying machine spending.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" variant="outline" className="w-full" nativeButton={false} render={<Link href="/investigate" />}>
              Open Investigation <ArrowRightIcon data-icon="inline-end" />
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border/60 hover:border-primary/60 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-[10px] font-mono">Audit Ledger</Badge>
              <FileCheck2Icon className="size-5 text-primary" />
            </div>
            <CardTitle className="mt-2 text-base">Funded Work Orders</CardTitle>
            <CardDescription className="text-xs">
              Review machine-funded work orders, vendor assignments, and cryptographic payment preimages in Neo4j.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" variant="outline" className="w-full" nativeButton={false} render={<Link href="/work-orders" />}>
              Open Work Orders <ArrowRightIcon data-icon="inline-end" />
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
