import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { JudgeMode } from "./JudgeMode";
import { ExecutionTimeline } from "./ExecutionTimeline";
import * as api from "@/lib/api";

describe("Machine Money Phase 2: Judge Mode & Timeline Components", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("ExecutionTimeline", () => {
    it("renders empty state when no events exist", () => {
      render(<ExecutionTimeline events={[]} />);
      expect(screen.getByTestId("execution-timeline-empty")).toBeInTheDocument();
      expect(screen.getByText("Awaiting Judge Scenario Execution")).toBeInTheDocument();
    });

    it("renders timeline stages with elapsed times and citation references", () => {
      const mockEvents: api.ExecutionStageEvent[] = [
        {
          stage: "ANOMALY_DETECTED",
          status: "SUCCESS",
          elapsed_ms: 12,
          message: "Sensor anomaly detected on P-101A",
          evidence_refs: ["P-101A", "EVT-001"],
          data: {},
          timestamp: new Date().toISOString(),
        },
        {
          stage: "EVIDENCE_MATCHED",
          status: "SUCCESS",
          elapsed_ms: 310,
          message: "GraphRAG matched failure signature FE-001",
          evidence_refs: ["FE-001", "PROC-001"],
          data: {},
          timestamp: new Date().toISOString(),
        },
        {
          stage: "POLICY_EVALUATED",
          status: "SUCCESS",
          elapsed_ms: 540,
          message: "250 sats is within autonomous cap (500 sats)",
          evidence_refs: ["POL-001"],
          data: {},
          timestamp: new Date().toISOString(),
        },
      ];

      render(<ExecutionTimeline events={mockEvents} />);

      expect(screen.getByTestId("execution-timeline")).toBeInTheDocument();
      expect(screen.getByTestId("timeline-stage-anomaly_detected")).toBeInTheDocument();
      expect(screen.getByTestId("timeline-stage-evidence_matched")).toBeInTheDocument();
      expect(screen.getByTestId("timeline-stage-policy_evaluated")).toBeInTheDocument();

      // Check citations
      expect(screen.getByText("FE-001")).toBeInTheDocument();
      expect(screen.getByText("PROC-001")).toBeInTheDocument();
    });
  });

  describe("JudgeMode Component", () => {
    it("renders primary CTA button and secondary actions", () => {
      render(<JudgeMode />);

      expect(screen.getByTestId("run-emergency-button")).toBeInTheDocument();
      expect(screen.getByTestId("run-escalation-button")).toBeInTheDocument();
      expect(screen.getByTestId("reset-scenario-button")).toBeInTheDocument();
      expect(screen.getByText("RUN INDUSTRIAL EMERGENCY")).toBeInTheDocument();
    });

    it("executes industrial emergency scenario and updates timeline", async () => {
      const mockResponse: api.JudgeExecutionResponse = {
        execution_id: "EXEC-JM-TEST1234",
        scenario: "INDUSTRIAL_EMERGENCY",
        status: "SUCCESS",
        total_elapsed_ms: 185,
        provider_mode: "MOCK / SIMULATION",
        summary: "Autonomous Settlement Complete: 250 sats paid.",
        events: [
          {
            stage: "ANOMALY_DETECTED",
            status: "SUCCESS",
            elapsed_ms: 10,
            message: "Sensor anomaly detected on P-101A",
            evidence_refs: ["P-101A"],
            data: {},
            timestamp: new Date().toISOString(),
          },
          {
            stage: "SETTLEMENT_CONFIRMED",
            status: "SUCCESS",
            elapsed_ms: 180,
            message: "Lightning payment settled",
            evidence_refs: ["REC-001"],
            data: {},
            timestamp: new Date().toISOString(),
          },
        ],
      };

      vi.spyOn(api, "executeJudgeMode").mockResolvedValueOnce(mockResponse);

      render(<JudgeMode />);

      const runButton = screen.getByTestId("run-emergency-button");
      fireEvent.click(runButton);

      await waitFor(() => {
        expect(api.executeJudgeMode).toHaveBeenCalledWith({
          scenario: "INDUSTRIAL_EMERGENCY",
          equipment_id: "P-101A",
          override_cost_sats: 250,
          auto_approve: true,
        });
        expect(screen.getByText("ID: EXEC-JM-TEST1234")).toBeInTheDocument();
        expect(screen.getByText("185ms")).toBeInTheDocument();
      });
    });

    it("resets scenario when reset button is clicked", async () => {
      vi.spyOn(api, "resetJudgeMode").mockResolvedValueOnce({
        status: "RESET",
        message: "Reset successful",
        ready: true,
      });

      render(<JudgeMode />);

      const resetButton = screen.getByTestId("reset-scenario-button");
      fireEvent.click(resetButton);

      await waitFor(() => {
        expect(api.resetJudgeMode).toHaveBeenCalledTimes(1);
      });
    });
  });
});
