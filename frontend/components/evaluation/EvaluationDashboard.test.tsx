import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EvaluationDashboard from "./EvaluationDashboard";

describe("EvaluationDashboard", () => {
  it("renders aggregate quality and the low-faithfulness review queue", () => {
    render(
      <EvaluationDashboard
        summary={{
          total: 2,
          status_counts: { scored: 2 },
          agent_counts: { rca: 1, copilot: 1 },
          low_faithfulness_count: 1,
          averages: {
            faithfulness: 0.6,
            context_precision: 0.75,
            answer_relevancy: 0.85,
          },
          trend: [
            {
              day: "2026-07-19",
              total: 1,
              faithfulness: 0.5,
              context_precision: 0.7,
              answer_relevancy: 0.8,
              low_faithfulness_count: 1,
            },
            {
              day: "2026-07-20",
              total: 1,
              faithfulness: 0.7,
              context_precision: 0.8,
              answer_relevancy: 0.9,
              low_faithfulness_count: 0,
            },
          ],
        }}
        items={[
          {
            score_id: "score-1",
            query: "Why did P-101 fail?",
            answer: "Bearing wear followed missed lubrication.",
            routed_agent: "rca",
            citations: ["FE-001"],
            graph_paths: [],
            retrieved_context: [],
            ragas_status: "scored",
            ragas_scores: {
              faithfulness: 0.4,
              context_precision: 0.7,
              answer_relevancy: 0.8,
            },
            low_faithfulness: true,
            created_at: "2026-07-20T10:00:00+00:00",
            completed_at: "2026-07-20T10:00:03+00:00",
            scoring_duration_ms: 3000,
            detail: null,
          },
        ]}
        total={1}
        offset={0}
        hasMore={false}
        lowOnly={false}
        status="all"
        agent="all"
        loading={false}
        onQueueChange={() => undefined}
        onStatusChange={() => undefined}
        onAgentChange={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
      />,
    );

    expect(screen.getByText("60%")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("Why did P-101 fail?")).toBeInTheDocument();
    expect(screen.getByText("Review required")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Daily RAGAS metric trend" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review queue (1)" })).toBeInTheDocument();
    expect(screen.getByText("Showing 1-1 of 1")).toBeInTheDocument();
  });
});
