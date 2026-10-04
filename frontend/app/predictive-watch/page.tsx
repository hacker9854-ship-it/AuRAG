import Link from "next/link";
import { ArrowRightIcon, Database } from "lucide-react";
import TelemetryPanel from "@/components/TelemetryPanel";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function PredictiveWatchPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-4 p-4 sm:p-6">
        <section className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h1 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">Predictive Telemetry Triggers</h1>
            <Badge variant="outline" className="text-xs font-mono border-cyan-500/40 text-cyan-400">
              NASA IMS Benchmark
            </Badge>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Stream empirical sensor telemetry (including NASA IMS bearing test rig) and evaluate ISO 10816 Zone C failure thresholds that trigger autonomous Lightning settlements.
          </p>
        </section>

        {/* Architectural Callout: Why GraphRAG over PLC */}
        <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-400 shrink-0 mt-0.5">
              <Database className="size-4" />
            </div>
            <div>
              <span className="font-bold text-foreground text-xs flex items-center gap-2">
                <span>Why GraphRAG over a simple SCADA threshold?</span>
                <Badge variant="outline" className="text-[10px] font-mono border-purple-500/40 text-purple-400">
                  Symptom vs. Expenditure
                </Badge>
              </span>
              <p className="text-muted-foreground text-[11px] mt-0.5 leading-relaxed">
                A PLC threshold only detects physical symptoms (5.42 mm/s vibration); GraphRAG justifies financial expenditures by verifying active OEM warranty, historical work orders (WO-1002), and plant SOPs before releasing autonomous Lightning satoshis.
              </p>
            </div>
          </div>
          <Link
            href="/machine-money"
            className="inline-flex items-center gap-1.5 text-[11px] font-medium text-purple-400 hover:text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 px-3 py-1.5 rounded-lg border border-purple-500/30 shrink-0 transition-colors"
          >
            <span>View Machine Money Settlement</span>
            <ArrowRightIcon className="size-3" />
          </Link>
        </div>

        <Card className="min-h-[720px] gap-0 py-0">
          <CardHeader className="border-b py-4">
            <CardTitle>Failure signature simulation</CardTitle>
            <CardDescription>
              Live and simulated signals create durable warnings and human-reviewed work orders.
            </CardDescription>
            <CardAction>
              <Badge variant="warning">Simulation</Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 p-0">
            <TelemetryPanel />
          </CardContent>
        </Card>
    </div>
  );
}
