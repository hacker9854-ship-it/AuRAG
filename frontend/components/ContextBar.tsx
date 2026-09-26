"use client";

import { CircleDotIcon, RouteIcon } from "lucide-react";
import type { ChatResponse } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function classify(score: number): "success" | "warning" | "destructive" {
  if (score >= 0.7) return "success";
  if (score >= 0.5) return "warning";
  return "destructive";
}

function ScoreBadge({ label, score }: { label: string; score: number }) {
  return (
    <Badge variant={classify(score)}>
      {label} {score.toFixed(2)}
    </Badge>
  );
}

function ContextMetric({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-sm font-medium">{children}</div>
    </div>
  );
}

export default function ContextBar({ response }: { response: ChatResponse | null }) {
  if (!response) {
    return (
      <Card size="sm">
        <CardHeader>
          <CardTitle>Active investigation</CardTitle>
          <CardDescription>Select an answer to connect its route, sources, graph trail, and quality score.</CardDescription>
          <CardAction>
            <Badge variant="success">
              <CircleDotIcon data-icon="inline-start" />
              Ready for input
            </Badge>
          </CardAction>
        </CardHeader>
        <CardContent className="flex items-center gap-3 text-sm text-muted-foreground">
          <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-muted">
            <RouteIcon className="size-4" />
          </div>
          No question is currently driving the workspace.
        </CardContent>
      </Card>
    );
  }

  const { user_query, routed_agent, intent, routing_confidence, citations, ragas_status, ragas_scores, low_faithfulness } =
    response;

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="line-clamp-1">{user_query}</CardTitle>
        <CardDescription>Active investigation context</CardDescription>
        <CardAction>
          <Badge variant="info">{routed_agent}</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-[repeat(4,minmax(0,1fr))_minmax(240px,auto)] md:items-end">
        <ContextMetric label="Agent">{routed_agent}</ContextMetric>
        <ContextMetric label="Intent">{intent}</ContextMetric>
        <ContextMetric label="Route confidence">{(routing_confidence * 100).toFixed(0)}%</ContextMetric>
        <ContextMetric label="Sources">{citations.length.toString().padStart(2, "0")}</ContextMetric>
        <div className="flex flex-wrap gap-1.5 md:justify-end">
          {ragas_status === "scored" && (
            <>
              {ragas_scores.faithfulness !== undefined && <ScoreBadge label="Faith" score={ragas_scores.faithfulness} />}
              {ragas_scores.context_precision !== undefined && (
                <ScoreBadge label="Context" score={ragas_scores.context_precision} />
              )}
              {ragas_scores.answer_relevancy !== undefined && (
                <ScoreBadge label="Relevance" score={ragas_scores.answer_relevancy} />
              )}
              {low_faithfulness && <Badge variant="destructive">Low faithfulness</Badge>}
            </>
          )}
          {ragas_status === "scoring" && <Badge variant="info">Scoring evidence alignment</Badge>}
          {ragas_status === "scoring_delayed" && <Badge variant="warning">Scoring delayed</Badge>}
          {ragas_status === "skipped_no_context" && <Badge variant="outline">No context to score</Badge>}
          {ragas_status === "skipped_disabled" && <Badge variant="outline">Quality scoring disabled</Badge>}
          {ragas_status === "error" && <Badge variant="destructive">Scoring unavailable</Badge>}
        </div>
      </CardContent>
    </Card>
  );
}
