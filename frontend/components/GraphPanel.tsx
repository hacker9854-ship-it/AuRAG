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

function Legend({ types }: { types: string[] }) {
  return (
    <div className="flex flex-wrap items-center gap-2 border-b p-3">
      <span className="mr-1 text-xs font-medium text-muted-foreground">Node classes</span>
      {types.map((type) => (
        <Badge key={type} variant="outline">
          <i className="size-2 rounded-full" style={{ background: TYPE_COLORS[type] ?? "#718096" }} />
          {type}
        </Badge>
      ))}
      <span className="ml-auto hidden text-xs text-muted-foreground xl:block">Drag nodes · scroll to zoom</span>
    </div>
  );
}

function EvidenceDetails({ graph, query }: { graph: GraphResponse; query: string | null }) {
  const grouped: Record<string, string[]> = {};
  for (const node of graph.nodes) {
    (grouped[node.type] ??= []).push(label(node));
  }

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
      .then((graph) => {
        if (!ignore) setResult({ key, graph });
      })
      .catch(() => {
        if (!ignore) setResult({ key, error: "The evidence graph could not be loaded for this answer." });
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

  if ("error" in result) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <TriangleAlertIcon />
          <AlertTitle>Evidence service unavailable</AlertTitle>
          <AlertDescription>{result.error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const nodes: CanvasNode[] = result.graph.nodes.map((node) => ({
    id: node.id,
    caption: `${node.type}: ${label(node)}`,
    color: TYPE_COLORS[node.type] ?? "#718096",
    size: node.type === "Equipment" ? 32 : 24,
  }));
  const relationships: CanvasRelationship[] = result.graph.relationships.map((relationship) => ({
    id: `${relationship.source}-${relationship.type}-${relationship.target}`,
    from: relationship.source,
    to: relationship.target,
    caption: relationship.type,
    color: "#667085",
  }));
  const presentTypes = [...new Set(result.graph.nodes.map((node) => node.type))];

  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_minmax(280px,1fr)_170px]">
      <Legend types={presentTypes} />
      <div className="min-h-0 bg-muted/20">
        <GraphCanvas key={key} nodes={nodes} rels={relationships} />
      </div>
      <EvidenceDetails graph={result.graph} query={query ?? null} />
    </div>
  );
}
