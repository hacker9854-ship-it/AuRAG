"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowRightIcon,
  TriangleAlertIcon,
} from "lucide-react";
import {
  decideWorkOrder,
  draftWorkOrder,
  Equipment,
  getEquipment,
  ReadingMeta,
  scanTelemetry,
  ScanResponse,
  updateWorkOrder,
  WorkOrderRecord,
} from "@/lib/api";
import WorkOrderEditor from "@/components/work-orders/WorkOrderEditor";
import { cn } from "@/lib/utils";
import { Alert, AlertAction, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { Spinner } from "@/components/ui/spinner";

type MetricTone = "success" | "warning" | "destructive";

function MetricCard({
  label,
  value,
  unit,
  nominal,
}: {
  label: string;
  value: number;
  unit: string;
  nominal: number;
}) {
  const deviation = nominal === 0 ? Math.abs(value) : Math.abs(value - nominal) / Math.abs(nominal);
  const level = Math.min(100, Math.round(deviation * 100));
  const tone: MetricTone = deviation < 0.15 ? "success" : deviation < 0.5 ? "warning" : "destructive";
  const barClass =
    tone === "success" ? "bg-success" : tone === "warning" ? "bg-warning" : "bg-destructive";

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-sm">{label}</CardTitle>
        <CardDescription>
          Nominal {nominal} {unit}
        </CardDescription>
        <CardAction>
          <Badge variant={tone}>{level}% dev.</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="data-mono text-2xl font-semibold tracking-tight">
          {value.toFixed(1)}
          <span className="ml-1 text-xs font-normal text-muted-foreground">{unit}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
          <div className={cn("h-full min-w-px rounded-full", barClass)} style={{ width: `${level}%` }} />
        </div>
      </CardContent>
    </Card>
  );
}

function MetricGrid({
  reading,
  meta,
}: {
  reading: ScanResponse["reading"];
  meta: Record<string, ReadingMeta>;
}) {
  const dimensions = Object.keys(reading).filter(
    (key) => key !== "equipment" && meta[key] && typeof reading[key] === "number"
  );

  if (dimensions.length === 0) {
    return (
      <Empty className="min-h-40 border">
        <EmptyHeader>
          <EmptyTitle>No sensor dimensions configured</EmptyTitle>
          <EmptyDescription>This equipment has no telemetry metadata available.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {dimensions.map((key) => (
        <MetricCard
          key={key}
          label={meta[key].label}
          value={reading[key] as number}
          unit={meta[key].unit}
          nominal={meta[key].nominal}
        />
      ))}
    </div>
  );
}

function SignalGauge({ driftPct, scanning }: { driftPct: number; scanning: boolean }) {
  return (
    <div className="relative size-36 shrink-0" aria-hidden="true">
      <svg viewBox="0 0 140 140" className="-rotate-90">
        <circle cx="70" cy="70" r="55" pathLength="100" className="fill-none stroke-muted" strokeWidth="8" />
        <circle
          cx="70"
          cy="70"
          r="55"
          pathLength="100"
          strokeDasharray={`${driftPct} 100`}
          className={cn(
            "fill-none stroke-primary transition-[stroke-dasharray,opacity] duration-300",
            scanning && "opacity-55"
          )}
          strokeWidth="8"
          strokeLinecap="round"
        />
        <circle cx="70" cy="70" r="40" className="fill-none stroke-border" strokeWidth="1" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <strong className="data-mono text-3xl font-semibold">{driftPct}</strong>
        <span className="text-xs text-muted-foreground">% drift</span>
      </div>
    </div>
  );
}

export default function TelemetryPanel() {
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [driftPct, setDriftPct] = useState(0);
  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [scanning, setScanning] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [workOrder, setWorkOrder] = useState<WorkOrderRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scanVersion = useRef(0);

  useEffect(() => {
    getEquipment()
      .then((list) => {
        setEquipment(list);
        if (list.length > 0) setSelected(list[0].tag_id);
      })
      .catch(() => setError("Could not connect to the equipment registry."));
  }, []);

  useEffect(() => {
    if (!selected) return;
    const version = ++scanVersion.current;
    const timer = setTimeout(() => {
      setScanning(true);
      setError(null);
      scanTelemetry(selected, null, driftPct / 100)
        .then((result) => {
          if (version !== scanVersion.current) return;
          setScan(result);
          setScanning(false);
        })
        .catch(() => {
          if (version !== scanVersion.current) return;
          setError("The telemetry scan service is currently unavailable.");
          setScanning(false);
        });
    }, 150);
    return () => clearTimeout(timer);
  }, [selected, driftPct]);

  function handleSelectEquipment(tag: string) {
    scanVersion.current += 1;
    setSelected(tag);
    setScan(null);
    setWorkOrder(null);
    setError(null);
  }

  async function handleDraft() {
    if (!scan?.matches[0] || drafting) return;
    setDrafting(true);
    setError(null);
    try {
      const draft = await draftWorkOrder(
        selected,
        scan.matches[0],
        scan.warning?.event_id ?? scan.predictive_event?.id,
      );
      setWorkOrder(draft);
    } catch {
      setError("The work-order draft service is currently unavailable.");
    } finally {
      setDrafting(false);
    }
  }

  const driftState =
    driftPct < 35
      ? { label: "Baseline", detail: "Nominal operating envelope", variant: "success" as const }
      : driftPct < 70
        ? { label: "Diverging", detail: "Moving toward a known signature", variant: "warning" as const }
        : { label: "High similarity", detail: "Failure pattern convergence", variant: "destructive" as const };
  const selectedEquipment = equipment.find((item) => item.tag_id === selected);
  const equipmentItems = equipment.map((item) => ({
    label: `${item.tag_id} / ${item.name}`,
    value: item.tag_id,
  }));

  return (
    <div className="grid h-full min-h-0 lg:grid-cols-[minmax(0,1.08fr)_minmax(340px,0.92fr)]">
      <div className="flex min-h-0 flex-col gap-5 border-b p-5 lg:border-r lg:border-b-0">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Controlled simulation</div>
            <h3 className="mt-1 font-heading text-base font-medium">
              Move a live reading toward a known failure signature.
            </h3>
          </div>
          <Badge variant="info">Durable event + review workflow</Badge>
        </div>

        <FieldGroup className="grid gap-4 md:grid-cols-[minmax(220px,0.8fr)_minmax(300px,1.2fr)]">
          <Field data-disabled={equipment.length === 0}>
            <FieldLabel htmlFor="equipment-asset">Equipment asset</FieldLabel>
            <Select<string>
              items={equipmentItems}
              value={selected || null}
              onValueChange={(value) => {
                if (value) handleSelectEquipment(value);
              }}
              disabled={equipment.length === 0}
            >
              <SelectTrigger id="equipment-asset" className="w-full">
                <SelectValue placeholder="Equipment unavailable" />
              </SelectTrigger>
              <SelectContent alignItemWithTrigger={false}>
                <SelectGroup>
                  {equipmentItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
            <FieldDescription>Select the asset whose known failure signatures should be compared.</FieldDescription>
          </Field>

          <Field data-disabled={!selected}>
            <div className="flex items-center justify-between gap-3">
              <FieldLabel htmlFor="signature-drift">Signature drift</FieldLabel>
              <div className="flex items-center gap-2">
                <Badge variant={driftState.variant}>{driftState.label}</Badge>
                <span className="data-mono text-sm font-semibold">{driftPct.toString().padStart(3, "0")}%</span>
              </div>
            </div>
            <Slider
              id="signature-drift"
              min={0}
              max={100}
              value={driftPct}
              onValueChange={(value) => setDriftPct(typeof value === "number" ? value : (value[0] ?? 0))}
              disabled={!selected}
              aria-label="Drift toward failure signature"
            />
            <div className="flex justify-between text-xs text-muted-foreground" aria-hidden="true">
              <span>Nominal</span>
              <span>Watch</span>
              <span>Failure match</span>
            </div>
          </Field>
        </FieldGroup>

        {error && (
          <Alert variant="destructive">
            <TriangleAlertIcon />
            <AlertTitle>Service connection interrupted</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <section className="flex min-h-0 flex-col gap-3">
          <div className="flex items-end justify-between gap-3">
            <div>
              <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Sensor frame</div>
              <div className="mt-1 text-sm font-medium">
                {selectedEquipment
                  ? `${selectedEquipment.tag_id} / ${selectedEquipment.type}`
                  : "Awaiting equipment"}
              </div>
            </div>
            <Badge variant={scanning ? "info" : scan ? "success" : "outline"}>
              {scanning && <Spinner data-icon="inline-start" />}
              {scanning ? "Scanning" : scan ? "Frame resolved" : "No frame"}
            </Badge>
          </div>

          {scan ? (
            <MetricGrid reading={scan.reading} meta={scan.reading_meta} />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          )}
        </section>
      </div>

      <div className="flex min-h-[340px] min-w-0 flex-col justify-center gap-4 bg-muted/20 p-5">
        {!scan?.warning ? (
          <Empty className="border-0 p-4">
            <EmptyMedia>
              <SignalGauge driftPct={driftPct} scanning={scanning} />
            </EmptyMedia>
            <EmptyHeader>
              <EmptyTitle>{error ? "Monitoring is paused" : "No proactive warning at this drift level"}</EmptyTitle>
              <EmptyDescription>
                {error ? "Restore the backend connection to resume scanning." : driftState.detail}
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Badge variant={scanning ? "info" : "success"}>
                {scanning && <Spinner data-icon="inline-start" />}
                {scanning ? "Resolving pattern" : "Below alert threshold"}
              </Badge>
            </EmptyContent>
          </Empty>
        ) : (
          <Alert variant="destructive">
            <TriangleAlertIcon />
            <AlertTitle>Known failure pattern detected</AlertTitle>
            <AlertDescription>{scan.warning.symptom}</AlertDescription>
            {!workOrder && (
              <AlertAction>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={handleDraft}
                  disabled={drafting}
                >
                  {drafting ? <Spinner data-icon="inline-start" /> : null}
                  Draft intervention
                  <ArrowRightIcon data-icon="inline-end" />
                </Button>
              </AlertAction>
            )}
            <div className="col-start-2 mt-3 grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs text-muted-foreground">Similarity</div>
                <div className="data-mono mt-1 text-xl font-semibold">
                  {(scan.warning.similarity * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Matched event</div>
                <div className="mt-1 text-sm font-medium">{scan.warning.matched_failure_event}</div>
              </div>
            </div>
          </Alert>
        )}

        {workOrder ? (
          <WorkOrderEditor
            key={`${workOrder.id}-${workOrder.version}`}
            workOrder={workOrder}
            onSave={async (payload) => {
              const updated = await updateWorkOrder(workOrder.id, payload);
              setWorkOrder(updated);
              return updated;
            }}
            onDecision={async (payload) => {
              const updated = await decideWorkOrder(workOrder.id, payload);
              setWorkOrder(updated);
              return updated;
            }}
          />
        ) : null}
      </div>
    </div>
  );
}
