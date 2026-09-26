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
    label: "Specialist agents",
    value: "04",
    detail: "Copilot, RCA, Compliance, Lessons Learned",
    icon: BotIcon,
  },
  {
    label: "Retrieval channels",
    value: "03",
    detail: "Graph traversal, dense retrieval, keyword search",
    icon: DatabaseZapIcon,
  },
  {
    label: "Quality dimensions",
    value: "03",
    detail: "Faithfulness, context precision, answer relevancy",
    icon: ShieldCheckIcon,
  },
  {
    label: "Evidence model",
    value: "08",
    detail: "Connected operational entity classes",
    icon: NetworkIcon,
  },
];

const workflow = [
  { step: "01", title: "Ask", detail: "Start with one operational question.", icon: SearchIcon },
  { step: "02", title: "Route", detail: "Supervisor selects the specialist agent.", icon: WorkflowIcon },
  { step: "03", title: "Reason", detail: "Hybrid retrieval grounds domain reasoning.", icon: BrainCircuitIcon },
  { step: "04", title: "Verify", detail: "Citations, graph trail, and RAGAS expose quality.", icon: FileCheck2Icon },
];

const knowledgeTypes = [
  "Equipment",
  "Failure events",
  "Work orders",
  "Procedures",
  "Documents",
  "People",
  "Regulatory clauses",
  "Source chunks",
];

export default function CommandCenterPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
        <section className="overflow-hidden rounded-xl bg-card shadow-xs ring-1 ring-foreground/10">
          <div className="grid lg:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
            <div className="flex flex-col justify-center p-6 sm:p-8 lg:p-10">
              <Badge variant="warning" className="w-fit">
                <SparklesIcon data-icon="inline-start" />
                Unified operations intelligence
              </Badge>
              <h1 className="mt-4 max-w-3xl font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
                Operational knowledge is scattered. AuRAG restores the relationships.
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base sm:leading-7">
                Maintenance records, failures, procedures, people, and regulations usually live in disconnected
                systems. AuRAG connects them in a knowledge graph so teams can investigate faster, verify every answer,
                and act before a known failure repeats.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <Button size="lg" nativeButton={false} render={<Link href="/investigate" />}>
                  Start an investigation
                  <ArrowRightIcon data-icon="inline-end" />
                </Button>
                <Button size="lg" variant="outline" nativeButton={false} render={<Link href="/predictive-watch" />}>
                  Open Predictive Watch
                  <GaugeIcon data-icon="inline-start" />
                </Button>
              </div>
            </div>

            <div className="flex flex-col justify-between gap-6 border-t bg-muted/25 p-6 lg:border-t-0 lg:border-l lg:p-8">
              <div>
                <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Core thesis</div>
                <p className="mt-3 font-heading text-xl font-medium leading-8">
                  This is not another document search box. The missing layer is the connection between operational
                  facts.
                </p>
              </div>
              <div className="grid gap-3">
                <div className="rounded-lg border bg-background/80 p-4">
                  <div className="text-xs text-muted-foreground">North-star interaction</div>
                  <div className="mt-1 font-medium">One question → cited answer → visible graph trail</div>
                </div>
                <div className="rounded-lg border bg-background/80 p-4">
                  <div className="text-xs text-muted-foreground">Proactive interaction</div>
                  <div className="mt-1 font-medium">Sensor drift → failure match → intervention draft</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Platform coverage">
          {coverage.map((item) => {
            const Icon = item.icon;
            return (
              <Card key={item.label} size="sm">
                <CardHeader>
                  <CardTitle className="text-muted-foreground">{item.label}</CardTitle>
                  <CardAction>
                    <div className="grid size-9 place-items-center rounded-lg bg-muted text-muted-foreground">
                      <Icon className="size-4" />
                    </div>
                  </CardAction>
                </CardHeader>
                <CardContent>
                  <div className="data-mono text-2xl font-semibold tracking-tight">{item.value}</div>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p>
                </CardContent>
              </Card>
            );
          })}
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
          <Card>
            <CardHeader>
              <CardTitle>How an answer becomes trustworthy</CardTitle>
              <CardDescription>
                Each stage remains visible instead of hiding the system behind a generic chat response.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {workflow.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.step} className="flex gap-4 rounded-lg border p-4">
                    <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="size-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="data-mono text-xs text-muted-foreground">{item.step}</span>
                        <h3 className="font-medium">{item.title}</h3>
                      </div>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.detail}</p>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Connected knowledge foundation</CardTitle>
              <CardDescription>
                Answers can traverse the operational entities that ordinary file search leaves isolated.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {knowledgeTypes.map((type) => (
                <Badge key={type} variant="outline" className="px-3 py-1.5">
                  {type}
                </Badge>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <Card className="border-primary/20">
            <CardHeader>
              <CardTitle>Investigate with evidence</CardTitle>
              <CardDescription>
                Route questions to RCA, compliance, copilot, or lessons-learned reasoning and inspect the answer trail.
              </CardDescription>
              <CardAction>
                <SearchIcon className="size-5 text-primary" />
              </CardAction>
            </CardHeader>
            <CardContent>
              <Button variant="outline" nativeButton={false} render={<Link href="/investigate" />}>
                Open investigation workspace
                <ArrowRightIcon data-icon="inline-end" />
              </Button>
            </CardContent>
          </Card>

          <Card className="border-warning/20">
            <CardHeader>
              <CardTitle>Act before the next failure</CardTitle>
              <CardDescription>
                Simulate telemetry drift, compare it with known failure signatures, and review a generated intervention.
              </CardDescription>
              <CardAction>
                <GaugeIcon className="size-5 text-warning" />
              </CardAction>
            </CardHeader>
            <CardContent>
              <Button variant="outline" nativeButton={false} render={<Link href="/predictive-watch" />}>
                Open predictive workflow
                <ArrowRightIcon data-icon="inline-end" />
              </Button>
            </CardContent>
          </Card>
        </section>
    </div>
  );
}
