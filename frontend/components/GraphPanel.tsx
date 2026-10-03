"use client";

import { useEffect, useState } from "react";
import { NetworkIcon, TriangleAlertIcon } from "lucide-react";
import { fetchGraph, GraphResponse } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import GraphCanvas, {
  type CanvasNode,
  type CanvasRelationship,
} from "@/components/GraphCanvas";

const TYPE_COLORS: Record<string, string> = {
  Equipment: "#d79b32",
  FailureEvent: "#e56b63",
  WorkOrder: "#5e91d8",
  Procedure: "#4eb78f",
  RegulatoryClause: "#9575cf",
  Chunk: "#718096",
  Person: "#cc739e",
  Document: "#4aa9b7",
};

function label(node: GraphResponse["nodes"][number]): string {
  const properties = node.properties;
  return (
    (properties.name as string) ??
    (properties.title as string) ??
    (properties.tag_id as string) ??
    (properties.id as string) ??
    node.id.split(":")[1] ??
    node.id
  );
}

type Result = { key: string; graph: GraphResponse } | { key: string; error: string };

function Legend({
  types,
  fallbackActive,
  graphStatus,
}: {
  types: string[];
  fallbackActive?: boolean;
  graphStatus?: string;
}) {
  const isFallback = fallbackActive || graphStatus === "DEGRADED / FALLBACK";
  return (
    <div className="flex flex-wrap items-center gap-2 border-b p-3">
      <span className="mr-1 text-xs font-medium text-muted-foreground">Node classes</span>
      {types.map((type) => (
        <Badge key={type} variant="outline">
          <i className="size-2 rounded-full" style={{ background: TYPE_COLORS[type] ?? "#718096" }} />
          {type}
        </Badge>
      ))}
      <div className="ml-auto flex items-center gap-2">
        <span
          data-testid="graph-status-badge"
          className={`font-mono text-[10px] px-2 py-0.5 rounded border font-semibold flex items-center gap-1 ${
            isFallback
              ? "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20"
              : "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
          }`}
        >
          GRAPH STATUS: {isFallback ? "DEGRADED / FALLBACK" : "LIVE AURA"}
        </span>
        <span className="hidden text-xs text-muted-foreground xl:block">Drag nodes · scroll to zoom</span>
      </div>
    </div>
  );
}

function EvidenceDetails({ graph, query }: { graph: GraphResponse; query: string | null }) {
  const grouped: Record<string, string[]> = {};
  for (const node of graph.nodes) {
    (grouped[node.type] ??= []).push(label(node));
  }
  const isFallback = graph.fallback_active || graph.graph_status === "DEGRADED / FALLBACK";

  return (
    <div className="grid h-full min-h-0 grid-cols-[auto_1fr] border-t">
      <div className="grid content-center gap-4 border-r p-4">
        <div>
          <div className="text-xs text-muted-foreground">Nodes</div>
          <div className="data-mono mt-1 text-lg font-semibold">{graph.nodes.length.toString().padStart(2, "0")}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Relations</div>
          <div className="data-mono mt-1 text-lg font-semibold">
            {graph.relationships.length.toString().padStart(2, "0")}
          </div>
        </div>
      </div>
      <ScrollArea className="min-h-0">
        <div className="flex flex-col gap-3 p-4">
          {isFallback && (
            <div
              data-testid="graph-fallback-banner"
              className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-700 dark:text-amber-300 flex items-center justify-between"
            >
              <span>Resilient Fallback Graph: Remote Aura disconnected or paused. Operating in deterministic offline mode.</span>
              <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-amber-500/20 font-bold">Fallback</span>
            </div>
          )}
          {query && <p className="line-clamp-2 text-xs text-muted-foreground">“{query}”</p>}
          {Object.entries(grouped).map(([type, names]) => (
            <div key={type} className="grid gap-1 sm:grid-cols-[120px_1fr]">
              <span className="flex items-center gap-2 text-xs font-medium">
                <i className="size-2 rounded-full" style={{ background: TYPE_COLORS[type] ?? "#718096" }} />
                {type}
              </span>
              <p className="text-xs leading-5 text-muted-foreground">{names.join(", ")}</p>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

function LoadingGraph() {
  return (
    <div className="flex h-full flex-col gap-3 p-4" aria-live="polite">
      <div className="flex gap-2">
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-5 w-16" />
      </div>
      <Skeleton className="min-h-0 flex-1" />
      <div className="grid grid-cols-3 gap-3">
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
      </div>
    </div>
  );
}

export default function GraphPanel({
  graphPaths,
  query,
}: {
  graphPaths: { type: string; id: string }[] | null;
  query?: string | null;
}) {
  const [result, setResult] = useState<Result | null>(null);
  const key = graphPaths && graphPaths.length > 0 ? JSON.stringify(graphPaths) : null;

  useEffect(() => {
    if (!key || !graphPaths) return;
    let ignore = false;
    fetchGraph(graphPaths)
      .then((data: any) => {
        if (!ignore) {
          if (data && (data.error || !Array.isArray(data.nodes))) {
            setResult({ key, error: data.detail || data.error || "The evidence graph could not be loaded for this answer." });
          } else {
            setResult({ key, graph: data });
          }
        }
      })
      .catch((err) => {
        if (!ignore) setResult({ key, error: err?.message || "The evidence graph could not be loaded for this answer." });
      });
    return () => {
      ignore = true;
    };
  }, [key, graphPaths]);

  if (!graphPaths) {
    return (
      <Empty className="h-full min-h-[430px] border-0">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <NetworkIcon />
          </EmptyMedia>
          <EmptyTitle>Every answer should show its work</EmptyTitle>
          <EmptyDescription>
            Select an agent response to reveal the connected equipment, event, procedure, document, and clause trail.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  if (graphPaths.length === 0) {
    return (
      <Empty className="h-full min-h-[430px] border-0">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <NetworkIcon />
          </EmptyMedia>
          <EmptyTitle>No graph path returned</EmptyTitle>
          <EmptyDescription>
            This answer may rely on direct context rather than a traversable knowledge-graph path.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  if (!result || result.key !== key) {
    return <LoadingGraph />;
  }

  if ("error" in result || !result.graph?.nodes || !Array.isArray(result.graph.nodes)) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <TriangleAlertIcon />
          <AlertTitle>Evidence service unavailable</AlertTitle>
          <AlertDescription>{"error" in result ? result.error : "The evidence graph could not be rendered."}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Deduplicate nodes defensively in frontend to eliminate any potential React key warnings
  const uniqueNodesMap = new Map<string, (typeof result.graph.nodes)[0]>();
  for (const node of result.graph.nodes || []) {
    if (!uniqueNodesMap.has(node.id)) {
      uniqueNodesMap.set(node.id, node);
    }
  }
  const uniqueNodesList = Array.from(uniqueNodesMap.values());

  const nodes: CanvasNode[] = uniqueNodesList.map((node) => ({
    id: node.id,
    caption: `${node.type}: ${label(node)}`,
    color: TYPE_COLORS[node.type] ?? "#718096",
    size: node.type === "Equipment" ? 32 : 24,
  }));
  const relationships: CanvasRelationship[] = (result.graph.relationships || []).map((relationship, idx) => ({
    id: `${relationship.source}-${relationship.type}-${relationship.target}-${idx}`,
    from: relationship.source,
    to: relationship.target,
    caption: relationship.type,
    color: "#667085",
  }));
  const presentTypes = [...new Set(uniqueNodesList.map((node) => node.type))];

  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_minmax(280px,1fr)_170px]">
      <Legend
        types={presentTypes}
        fallbackActive={result.graph.fallback_active}
        graphStatus={result.graph.graph_status}
      />
      <div className="min-h-0 bg-muted/20">
        <GraphCanvas key={key} nodes={nodes} rels={relationships} />
      </div>
      <EvidenceDetails graph={result.graph} query={query ?? null} />
    </div>
  );
}
