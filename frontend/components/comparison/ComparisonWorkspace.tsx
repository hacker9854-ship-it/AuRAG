import { DatabaseIcon, NetworkIcon, TimerIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ComparisonAnswer, ComparisonResponse } from "@/lib/api";

function AnswerPane({
  title,
  description,
  icon: Icon,
  answer,
}: {
  title: string;
  description: string;
  icon: typeof NetworkIcon;
  answer: ComparisonAnswer;
}) {
  return (
    <Card className="h-full">
      <CardHeader className="border-b">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
        <CardAction>
          <Icon />
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <p className="text-sm leading-7">{answer.agent_response}</p>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg bg-muted/45 p-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <TimerIcon />
              Response latency
            </div>
            <div className="data-mono mt-1 text-lg font-semibold">{answer.latency_ms} ms</div>
          </div>
          <div className="rounded-lg bg-muted/45 p-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <DatabaseIcon />
              Retrieved sources
            </div>
            <div className="data-mono mt-1 text-lg font-semibold">{answer.source_count}</div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Citations used</div>
          <div className="flex flex-wrap gap-1.5">
            {answer.citations.length ? (
              answer.citations.map((citation) => (
                <Badge key={citation} variant="outline">
                  {citation}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">No citations returned</span>
            )}
          </div>
        </div>

        <details className="rounded-lg border p-3">
          <summary className="cursor-pointer text-sm font-medium">Retrieved context</summary>
          <div className="mt-3 flex flex-col gap-3">
            {answer.retrieved_context.map(([key, text]) => (
              <div key={key} className="rounded-md bg-muted/45 p-3">
                <Badge variant="outline">{key}</Badge>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

export default function ComparisonWorkspace({ data }: { data: ComparisonResponse }) {
  const relationshipCount = data.comparison_metrics.graph_relationship_evidence;

  return (
    <div className="flex flex-col gap-5">
      <section className="grid gap-3 sm:grid-cols-3" aria-label="Comparison summary">
        <Card size="sm">
          <CardHeader>
            <CardTitle>Source overlap</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="data-mono text-2xl font-semibold">{data.comparison_metrics.source_overlap_pct}%</div>
            <p className="mt-1 text-xs text-muted-foreground">Same evidence retrieved by both approaches</p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardTitle>Graph grounding</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="data-mono text-2xl font-semibold">{relationshipCount}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              {relationshipCount} graph-linked evidence {relationshipCount === 1 ? "node" : "nodes"}
            </p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardHeader>
            <CardTitle>Unique evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="data-mono text-2xl font-semibold">
              {data.comparison_metrics.graph_only_sources.length}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Sources found only through GraphRAG</p>
          </CardContent>
        </Card>
      </section>

      <section className="grid items-start gap-5 xl:grid-cols-2" aria-label="Side-by-side answers">
        <AnswerPane
          title="GraphRAG"
          description="Neo4j vector + Qdrant + BM25 + graph traversal, then reranking."
          icon={NetworkIcon}
          answer={data.graph_rag}
        />
        <AnswerPane
          title="Dense-only RAG"
          description="Qdrant semantic vector retrieval only; no graph traversal or keyword channel."
          icon={DatabaseIcon}
          answer={data.plain_rag}
        />
      </section>
    </div>
  );
}

