import { useState } from "react";
import {
  BadgeCheckIcon,
  ChartNoAxesCombinedIcon,
  CheckCircle2Icon,
  CircleAlertIcon,
  FilePenLineIcon,
  ListChecksIcon,
  MessageSquareTextIcon,
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
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { submitRemediation, type EvaluationRecord, type EvaluationSummary } from "@/lib/api";

function percent(value: number | null) {
  return value === null ? "Not scored" : `${Math.round(value * 100)}%`;
}

function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number | null;
  description: string;
}) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>{label}</CardTitle>
        <CardAction>
          <BadgeCheckIcon />
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="data-mono text-2xl font-semibold">{percent(value)}</div>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function TrendChart({ points }: { points: EvaluationSummary["trend"] }) {
  if (!points.length) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <ChartNoAxesCombinedIcon />
          </EmptyMedia>
          <EmptyTitle>No trend data yet</EmptyTitle>
          <EmptyDescription>Daily quality trends appear after grounded answers are scored.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  const width = 640;
  const height = 180;
  const x = (index: number) =>
    points.length === 1 ? width / 2 : 28 + (index * (width - 56)) / (points.length - 1);
  const y = (value: number | null) => height - 24 - (value ?? 0) * (height - 48);
  const line = (metric: "faithfulness" | "context_precision" | "answer_relevancy") =>
    points.map((point, index) => `${x(index)},${y(point[metric])}`).join(" ");

  return (
    <div className="overflow-x-auto">
      <svg
        className="h-52 min-w-[620px] w-full"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Daily RAGAS metric trend"
      >
        {[0, 0.5, 1].map((value) => (
          <g key={value}>
            <line
              x1="28"
              x2={width - 28}
              y1={y(value)}
              y2={y(value)}
              className="stroke-border"
              strokeDasharray="4 5"
            />
            <text x="0" y={y(value) + 4} className="fill-muted-foreground text-[10px]">
              {Math.round(value * 100)}
            </text>
          </g>
        ))}
        <polyline
          points={line("faithfulness")}
          fill="none"
          className="stroke-emerald-500"
          strokeWidth="3"
        />
        <polyline
          points={line("context_precision")}
          fill="none"
          className="stroke-sky-500"
          strokeWidth="3"
        />
        <polyline
          points={line("answer_relevancy")}
          fill="none"
          className="stroke-violet-500"
          strokeWidth="3"
        />
        {points.map((point, index) => (
          <circle
            key={`${point.day}-${index}`}
            cx={x(index)}
            cy={y(point.faithfulness)}
            r="3"
            className="fill-emerald-500"
          >
            <title>{`${point.day}: ${percent(point.faithfulness)} faithfulness`}</title>
          </circle>
        ))}
      </svg>
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
        <span>{points[0].day}</span>
        <div className="flex flex-wrap gap-3">
          <span className="text-emerald-600">Faithfulness</span>
          <span className="text-sky-600">Context precision</span>
          <span className="text-violet-600">Answer relevancy</span>
        </div>
        <span>{points[points.length - 1].day}</span>
      </div>
    </div>
  );
}

export default function EvaluationDashboard({
  summary,
  items,
  total,
  offset,
  hasMore,
  lowOnly,
  status,
  agent,
  loading,
  onQueueChange,
  onStatusChange,
  onAgentChange,
  onPrevious,
  onNext,
}: {
  summary: EvaluationSummary;
  items: EvaluationRecord[];
  total: number;
  offset: number;
  hasMore: boolean;
  lowOnly: boolean;
  status: string;
  agent: string;
  loading: boolean;
  onQueueChange: (value: boolean) => void;
  onStatusChange: (value: string) => void;
  onAgentChange: (value: string) => void;
  onPrevious: () => void;
  onNext: () => void;
}) {
  const [remediatingScoreId, setRemediatingScoreId] = useState<string | null>(null);
  const [remediationReason, setRemediationReason] = useState("");
  const [remediationNotes, setRemediationNotes] = useState("");
  const [remediationSuccess, setRemediationSuccess] = useState<string | null>(null);
  const [remediationSubmitting, setRemediationSubmitting] = useState(false);

  const handleRemediationSubmit = async (scoreId: string) => {
    if (!remediationNotes.trim()) return;
    setRemediationSubmitting(true);
    try {
      await submitRemediation({
        score_id: scoreId,
        reason: remediationReason || "Low Faithfulness / Inaccurate Evidence",
        correction_notes: remediationNotes,
      });
      setRemediationSuccess(scoreId);
      setTimeout(() => {
        setRemediatingScoreId(null);
        setRemediationSuccess(null);
      }, 3000);
    } catch {
      // handled
    } finally {
      setRemediationSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-5" aria-busy={loading}>
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Evaluation summary">
        <MetricCard
          label="Faithfulness"
          value={summary.averages.faithfulness}
          description="Claims supported by retrieved evidence"
        />
        <MetricCard
          label="Context precision"
          value={summary.averages.context_precision}
          description="Retrieved context that was actually relevant"
        />
        <MetricCard
          label="Answer relevancy"
          value={summary.averages.answer_relevancy}
          description="How directly answers address the question"
        />
        <Card size="sm">
          <CardHeader>
            <CardTitle>Review queue</CardTitle>
            <CardAction>
              <CircleAlertIcon />
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="data-mono text-2xl font-semibold">{summary.low_faithfulness_count}</div>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Low-faithfulness answers requiring review
            </p>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader className="border-b">
          <CardTitle>Quality trend</CardTitle>
          <CardDescription>Daily metric averages from the latest 30 recorded scoring days.</CardDescription>
          <CardAction>
            <ChartNoAxesCombinedIcon />
          </CardAction>
        </CardHeader>
        <CardContent className="pt-5">
          <TrendChart points={summary.trend} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b">
          <div className="flex flex-col gap-4">
            <div>
              <CardTitle>{lowOnly ? "Low-faithfulness review queue" : "Answer evaluations"}</CardTitle>
              <CardDescription>
                Durable history across backend restarts, ordered by most recent answer.
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant={lowOnly ? "outline" : "default"}
                onClick={() => onQueueChange(false)}
                disabled={loading}
              >
                All answers
              </Button>
              <Button
                size="sm"
                variant={lowOnly ? "destructive" : "outline"}
                onClick={() => onQueueChange(true)}
                disabled={loading}
              >
                Review queue ({summary.low_faithfulness_count})
              </Button>
              <Select value={status} onValueChange={(value) => value && onStatusChange(value)}>
                <SelectTrigger size="sm" aria-label="Evaluation status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="all">All statuses</SelectItem>
                    {Object.keys(summary.status_counts).map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
              <Select value={agent} onValueChange={(value) => value && onAgentChange(value)}>
                <SelectTrigger size="sm" aria-label="Routed agent">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="all">All agents</SelectItem>
                    {Object.keys(summary.agent_counts).map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>
          </div>
          <CardAction>
            <Badge variant="outline">{total} matching</Badge>
          </CardAction>
        </CardHeader>
        <CardContent>
          {items.length ? (
            <div className="flex flex-col gap-3">
              {items.map((item) => (
                <article key={item.score_id} className="rounded-lg border p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="info">{item.routed_agent}</Badge>
                        <Badge
                          variant={
                            item.ragas_status === "scored"
                              ? "success"
                              : item.ragas_status === "error"
                                ? "destructive"
                                : "warning"
                          }
                        >
                          {item.ragas_status}
                        </Badge>
                        {item.low_faithfulness ? (
                          <Badge variant="destructive">Review required</Badge>
                        ) : null}
                      </div>
                      <h3 className="mt-3 font-medium">{item.query}</h3>
                      <p className="mt-1 line-clamp-2 text-sm leading-6 text-muted-foreground">
                        {item.answer}
                      </p>
                    </div>
                    <div className="grid shrink-0 grid-cols-3 gap-3 text-center">
                      {[
                        ["Faith", item.ragas_scores.faithfulness],
                        ["Precision", item.ragas_scores.context_precision],
                        ["Relevance", item.ragas_scores.answer_relevancy],
                      ].map(([label, value]) => (
                        <div key={String(label)}>
                          <div className="data-mono text-sm font-semibold">
                            {percent(typeof value === "number" ? value : null)}
                          </div>
                          <div className="text-[11px] text-muted-foreground">{label}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between border-t pt-2 text-xs">
                    <span className="font-mono text-muted-foreground">{item.score_id}</span>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs gap-1.5"
                      onClick={() => {
                        setRemediatingScoreId(remediatingScoreId === item.score_id ? null : item.score_id);
                        setRemediationReason(item.low_faithfulness ? "Low Faithfulness / Hallucinated Evidence" : "Factually Inaccurate");
                        setRemediationNotes("");
                      }}
                    >
                      <FilePenLineIcon className="size-3.5" />
                      {remediatingScoreId === item.score_id ? "Cancel Correction" : "Remediate Answer"}
                    </Button>
                  </div>

                  {remediatingScoreId === item.score_id && (
                    <div className="mt-3 rounded-lg border border-amber-300/60 bg-amber-50/50 p-4 text-xs dark:border-amber-900/50 dark:bg-amber-950/20">
                      {remediationSuccess === item.score_id ? (
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                          <CheckCircle2Icon className="size-4" />
                          <span>Correction submitted! Document queued for re-indexing in Operations Hub.</span>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="font-semibold text-amber-900 dark:text-amber-200">
                            Operational Remediation & Document Re-indexing
                          </div>
                          <div>
                            <label className="block text-slate-600 dark:text-slate-400 mb-1">Reason:</label>
                            <input
                              type="text"
                              className="w-full rounded border bg-background px-2.5 py-1 text-xs"
                              value={remediationReason}
                              onChange={(e) => setRemediationReason(e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="block text-slate-600 dark:text-slate-400 mb-1">
                              Ground-Truth Engineering Correction:
                            </label>
                            <textarea
                              rows={2}
                              className="w-full rounded border bg-background px-2.5 py-1 text-xs"
                              placeholder="State the verified operating procedure, tag, or drawing revision..."
                              value={remediationNotes}
                              onChange={(e) => setRemediationNotes(e.target.value)}
                            />
                          </div>
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                              onClick={() => setRemediatingScoreId(null)}
                            >
                              Cancel
                            </Button>
                            <Button
                              size="sm"
                              className="h-7 text-xs bg-amber-600 hover:bg-amber-700 text-white"
                              disabled={remediationSubmitting || !remediationNotes.trim()}
                              onClick={() => handleRemediationSubmit(item.score_id)}
                            >
                              {remediationSubmitting ? "Submitting..." : "Submit Correction & Queue Re-indexing"}
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <Empty>
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <MessageSquareTextIcon />
                </EmptyMedia>
                <EmptyTitle>No evaluations match</EmptyTitle>
                <EmptyDescription>
                  {lowOnly
                    ? "No low-faithfulness answers match the current filters."
                    : "Ask a grounded question in Investigate; scoring will appear here when complete."}
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
          <div className="mt-5 flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-muted-foreground">
              {total
                ? `Showing ${offset + 1}-${Math.min(offset + items.length, total)} of ${total}`
                : "No matching evaluations"}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={onPrevious} disabled={loading || offset === 0}>
                Previous
              </Button>
              <Button variant="outline" size="sm" onClick={onNext} disabled={loading || !hasMore}>
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card size="sm">
        <CardHeader>
          <CardTitle>Scoring operations</CardTitle>
          <CardAction>
            <ListChecksIcon />
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {Object.entries(summary.status_counts).map(([itemStatus, count]) => (
            <Badge key={itemStatus} variant="outline">
              {itemStatus}: {count}
            </Badge>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
