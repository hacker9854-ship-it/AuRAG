import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ComparisonWorkspace from "./ComparisonWorkspace";

const comparison = {
  query: "Why did P-101 fail?",
  graph_rag: {
    user_query: "Why did P-101 fail?",
    agent_response: "The bearing failed after an overdue lubrication service.",
    citations: ["FE-001", "WO-1002"],
    retrieved_context: [
      ["FE-001", "Failure evidence"],
      ["WO-1002", "Work-order evidence"],
    ] as [string, string][],
    graph_paths: [{ type: "FailureEvent", id: "FE-001" }],
    latency_ms: 240,
    source_count: 2,
  },
  plain_rag: {
    user_query: "Why did P-101 fail?",
    agent_response: "A similar pump showed bearing wear.",
    citations: ["CHUNK-9"],
    retrieved_context: [["CHUNK-9", "Similar pump text"]] as [string, string][],
    graph_paths: [],
    latency_ms: 180,
    source_count: 1,
  },
  comparison_metrics: {
    shared_sources: [],
    graph_only_sources: ["FE-001", "WO-1002"],
    plain_only_sources: ["CHUNK-9"],
    source_overlap_pct: 0,
    graph_relationship_evidence: 1,
  },
};

describe("ComparisonWorkspace", () => {
  it("renders independent answers and the graph grounding delta", () => {
    render(<ComparisonWorkspace data={comparison} />);

    expect(screen.getByText("GraphRAG")).toBeInTheDocument();
    expect(screen.getByText("Dense-only RAG")).toBeInTheDocument();
    expect(screen.getByText("The bearing failed after an overdue lubrication service.")).toBeInTheDocument();
    expect(screen.getByText("A similar pump showed bearing wear.")).toBeInTheDocument();
    expect(screen.getByText("1 graph-linked evidence node")).toBeInTheDocument();
    expect(screen.getAllByText("FE-001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("CHUNK-9").length).toBeGreaterThan(0);
  });
});
