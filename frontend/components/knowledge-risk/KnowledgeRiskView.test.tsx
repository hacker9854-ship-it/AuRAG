import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import KnowledgeRiskView from "./KnowledgeRiskView";

const result = {
  retirement_horizon: 5,
  summary: {
    people_at_risk: 1,
    critical: 1,
    elevated: 0,
    uncovered_assets: 1,
  },
  people: [
    {
      person_id: "PER-001",
      name: "Vikram Singh",
      role: "Maintenance Supervisor",
      department: "Mechanical",
      years_to_retirement: 1,
      risk_score: 88,
      severity: "critical" as const,
      work_orders: ["WO-1003", "WO-1009"],
      equipment: ["C-201", "T-501"],
      critical_equipment: ["C-201"],
      failure_events: ["FE-002"],
      documents: ["DOC-MAINT"],
      uncovered_equipment: ["C-201"],
      knowledge_coverage: {
        covered_assets: 1,
        uncovered_assets: 1,
        coverage_pct: 50,
      },
      recommended_actions: [
        {
          type: "capture_knowledge",
          priority: "critical",
          description: "Capture operating knowledge before retirement.",
        },
      ],
    },
  ],
};

describe("KnowledgeRiskView", () => {
  it("renders ranked risk, coverage, evidence, and recommended action", () => {
    render(<KnowledgeRiskView data={result} />);

    expect(screen.getByText("Vikram Singh")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText("50% covered")).toBeInTheDocument();
    expect(screen.getByText("C-201")).toBeInTheDocument();
    expect(screen.getByText("Capture operating knowledge before retirement.")).toBeInTheDocument();
  });

  it("renders an actionable empty state", () => {
    render(
      <KnowledgeRiskView
        data={{
          retirement_horizon: 5,
          summary: { people_at_risk: 0, critical: 0, elevated: 0, uncovered_assets: 0 },
          people: [],
        }}
      />,
    );

    expect(screen.getByText("No retirement risk in this horizon")).toBeInTheDocument();
  });
});

