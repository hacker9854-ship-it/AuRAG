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

      expect(screen.getByTestId("execution-progress-bar")).toBeInTheDocument();

      // Check citations
      expect(screen.getByText("FE-001")).toBeInTheDocument();
      expect(screen.getByText("PROC-001")).toBeInTheDocument();
    });
  });

  describe("JudgeMode Component", () => {
    it("renders primary CTA button, escalation button, and provider failure button", () => {
      render(<JudgeMode />);

      expect(screen.getByTestId("run-emergency-button")).toBeInTheDocument();
      expect(screen.getByTestId("run-escalation-button")).toBeInTheDocument();
      expect(screen.getByTestId("run-provider-failure-button")).toBeInTheDocument();
      expect(screen.getByTestId("reset-scenario-button")).toBeInTheDocument();
      expect(screen.getByText("RUN INDUSTRIAL EMERGENCY")).toBeInTheDocument();
      expect(screen.getByText("Run Provider Failure")).toBeInTheDocument();
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

    it("executes provider failure scenario and shows failure alert without false success toast", async () => {
      const mockFailureResponse: api.JudgeExecutionResponse = {
        execution_id: "EXEC-FAIL-TEST",
        scenario: "PROVIDER_FAILURE",
        status: "FAILED",
        total_elapsed_ms: 140,
        provider_mode: "MOCK / SIMULATION",
        summary: "Provider Failure Simulated: Channel liquidity exhausted.",
        payment_record: {
          payment_id: "PAY-EXEC-FAIL-TEST",
          amount_sats: 250,
          status: "FAILED",
          retry_guidance: "Payment not executed. Zero satoshis deducted. Retry guidance: Re-balance payment channel via LSP.",
        },
        events: [
          {
            stage: "ANOMALY_DETECTED",
            status: "SUCCESS",
            elapsed_ms: 10,
            message: "Sensor anomaly detected",
            evidence_refs: ["P-101A"],
            data: {},
            timestamp: new Date().toISOString(),
          },
          {
            stage: "SETTLEMENT_CONFIRMED",
            status: "FAILED",
            elapsed_ms: 135,
            message: "Lightning settlement failed: Channel route liquidity exhausted",
            evidence_refs: ["ERR-CHANNEL-LIQUIDITY"],
            data: { settled: false },
            timestamp: new Date().toISOString(),
          },
        ],
      };

      vi.spyOn(api, "executeJudgeMode").mockResolvedValueOnce(mockFailureResponse);

      render(<JudgeMode />);

      const failureButton = screen.getByTestId("run-provider-failure-button");
      fireEvent.click(failureButton);

      await waitFor(() => {
        expect(api.executeJudgeMode).toHaveBeenCalledWith({
          scenario: "PROVIDER_FAILURE",
          equipment_id: "P-101A",
          override_cost_sats: 250,
          auto_approve: true,
        });
        expect(screen.getByTestId("provider-failure-alert")).toBeInTheDocument();
        expect(screen.getByText("Payment Unsettled — Simulated Provider Failure")).toBeInTheDocument();
        expect(screen.getByText(/Payment not executed\. Zero satoshis deducted\./i)).toBeInTheDocument();
        expect(screen.getAllByText("FAILED").length).toBeGreaterThanOrEqual(1);
        expect(screen.queryByText("Autonomous Settlement Complete")).not.toBeInTheDocument();
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

    it("renders the 5-question above-the-fold value ribbon answering core judge questions", () => {
      render(<JudgeMode />);
      expect(screen.getByTestId("judge-value-ribbon")).toBeInTheDocument();
      expect(screen.getByText("1. Why We Pay")).toBeInTheDocument();
      expect(screen.getByText("2. Justified By")).toBeInTheDocument();
      expect(screen.getByText("3. Why Allowed")).toBeInTheDocument();
      expect(screen.getByText("4. Settlement")).toBeInTheDocument();
      expect(screen.getByText("5. Business Impact")).toBeInTheDocument();
    });

    it("provides accessible aria-labels on all control buttons", () => {
      render(<JudgeMode />);
      expect(screen.getByLabelText(/Run industrial emergency autonomous settlement scenario/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Run public dataset replay scenario/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Run policy escalation scenario/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Run simulated provider failure scenario/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Reset demonstration state/i)).toBeInTheDocument();
    });

    it("executes public dataset replay scenario and displays public provenance badges", async () => {
      const mockReplayResponse: api.JudgeExecutionResponse = {
        execution_id: "EXEC-PUB-TEST01",
        scenario: "PUBLIC_DATASET_REPLAY",
        status: "SUCCESS",
        total_elapsed_ms: 195,
        provider_mode: "MOCK / SIMULATION",
        summary: "Public dataset replay complete: 250 sats settled for REPLAY-ASSET-01.",
        events: [
          {
            stage: "ANOMALY_DETECTED",
            status: "SUCCESS",
            elapsed_ms: 15,
            message: "[PUBLIC DATASET / REPLAY] Sensor anomaly replayed from NASA IMS Bearing Run-to-Failure (Test 2)",
            evidence_refs: ["REPLAY-ASSET-01", "NASA-IMS-T2-REC-042"],
            data: {
              equipment_id: "REPLAY-ASSET-01",
              sensor_id: "REPLAY-SENSOR-BEARING-01",
              vibration_mms: 5.42,
              threshold_mms: 4.5,
              data_source_type: "PUBLIC_DATASET",
              dataset_name: "NASA IMS Bearing Run-to-Failure (Test 2)",
              dataset_record_id: "NASA-IMS-T2-REC-042",
              replay_mode: true,
            },
            timestamp: "2004-02-18T09:42:39Z",
          },
          {
            stage: "EVIDENCE_MATCHED",
            status: "SUCCESS",
            elapsed_ms: 320,
            message: "Grounded empirical vibration spike from NASA IMS",
            evidence_refs: ["FE-001", "WO-1002", "PROC-001"],
            data: {
              retrieval_method: "PUBLIC_DATASET",
              matched_failure_event: "FE-001",
              governing_procedure: "PROC-001",
              confidence: 0.94,
            },
            timestamp: "2004-02-18T09:42:40Z",
          },
        ],
      };

      vi.spyOn(api, "executeJudgeMode").mockResolvedValueOnce(mockReplayResponse);

      render(<JudgeMode />);

      const replayButton = screen.getByTestId("run-public-replay-button");
      fireEvent.click(replayButton);

      await waitFor(() => {
        expect(api.executeJudgeMode).toHaveBeenCalledWith({
          scenario: "PUBLIC_DATASET_REPLAY",
          equipment_id: "REPLAY-ASSET-01",
          override_cost_sats: 250,
          auto_approve: true,
        });
        expect(screen.getByTestId("provenance-badge-public")).toBeInTheDocument();
        expect(screen.getAllByText(/PUBLIC DATASET \/ REPLAY/).length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("REPLAY-ASSET-01").length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("NASA-IMS-T2-REC-042").length).toBeGreaterThanOrEqual(1);
      });
    });
  });
});
