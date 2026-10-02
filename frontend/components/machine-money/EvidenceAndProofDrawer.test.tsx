import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { EvidenceSummaryCard } from "./EvidenceSummaryCard";
import { PaymentProofDrawer } from "./PaymentProofDrawer";
import * as api from "@/lib/api";

const mockProofPackage: api.ProofPackageResponse = {
  identity: {
    payment_id: "PAY-2026-TEST-001",
    idempotency_key: "sha256:test-idem-001",
    created_at: new Date().toISOString(),
    settled_at: new Date().toISOString(),
  },
  payment: {
    amount_sats: 250,
    amount_msat: 250000,
    fee_sats: 0,
    status: "PAID",
    provider: "mock",
    network: "regtest",
    bolt11: "lnbcrt2500n1pj48ugqpp5qxaywxwgpdh7jydsjxnuq5fyke8wan5kfcyuqk8037vqtkk2234ssp50nuwt7l793l234xk7vsps0y3l2qr3e6l0qgfrthq38yyerww6fhsdz6tdx57s6tyqhjq56ff425cs25f985uhfqf45kxun094cxz7tdv4h8ggrxdaezq5pdxycrzsfqd36kyunfvdshg6t0dcxqrrsscqpjjga32ynxew6snx8mdhv9qdtt5405zt2kdh5h5fcsm7pydlnrfckzzntwqu77gcfdtyjkglaphs6rjjlj548gc8lhljpaw7vtcawejecqwtnmnz",
    memo: "Slurry feed pump repair settlement",
  },
  policy: {
    policy_id: "POL-LIGHTNING-MACHINE-MONEY",
    policy_name: "Autonomous Maintenance Spending Cap",
    decision: "ALLOWED",
    cap_sats: 500,
    confidence_score: 0.94,
    evaluated_by: "AutonomousPolicyEngine",
  },
  operational_context: {
    equipment_id: "P-101A",
    event_id: "EVT-VIB-001",
    work_order_id: "WO-2026-P101",
    failure_event_id: "FE-001",
    vendor_name: "maintenance-node-a",
    reason: "Vibration excursion matched bearing degradation signature",
    governing_procedure: "PROC-001",
  },
  cryptographic_proof: {
    payment_hash: "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
    preimage: "6170706c65",
    formula: "SHA-256(preimage) == payment_hash",
    is_verified: true,
    verification_mode: "MOCK_VERIFIED",
    status_label: "Cryptographically Verified",
  },
  graph_links: {
    equipment_tag: "P-101A",
    predictive_event: "EVT-VIB-001",
    work_order: "WO-2026-P101",
    payment_node: "PAY-2026-TEST-001",
    lineage: [
      "(Equipment: P-101A)",
      "(PredictiveEvent: EVT-VIB-001)",
      "(WorkOrder: WO-2026-P101)",
      "(Payment: PAY-2026-TEST-001)",
    ],
  },
  audit: {
    audit_ledger_status: "COMMITTED",
    table: "machine_money_payments",
    integrity: "VERIFIED",
    recorded_at: new Date().toISOString(),
  },
  provider_mode: "MOCK / SIMULATION",
};

describe("Machine Money Phase 3: Evidence & Proof Drawer", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("EvidenceSummaryCard", () => {
    it("renders the 4 core pillars and confidence score correctly", () => {
      render(
        <EvidenceSummaryCard
          equipmentId="P-101A"
          confidence={0.94}
          failureSignatureId="FE-001"
          governingProcedure="PROC-001"
          relatedWorkOrder="WO-1002"
          workOrderId="WO-2026-P101"
          costSats={250}
          policyCap={500}
        />
      );

      // Card container
      expect(screen.getByTestId("evidence-summary-card")).toBeInTheDocument();

      // 4 Pillars
      expect(screen.getByText("1. Telemetry Anomaly")).toBeInTheDocument();
      expect(screen.getByText("2. Matched Evidence")).toBeInTheDocument();
      expect(screen.getByText("3. Service Action")).toBeInTheDocument();
      expect(screen.getByText("4. Policy Gate")).toBeInTheDocument();

      // Confidence
      expect(screen.getByText("94%")).toBeInTheDocument();

      // Citations
      expect(screen.getByText("PROC-001")).toBeInTheDocument();
      expect(screen.getByText("WO-1002")).toBeInTheDocument();

      // Amounts and Policy
      expect(screen.getAllByText(/250 sats/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/500 sats Cap/)).toBeInTheDocument();
      expect(screen.getByText("AUTHORIZED")).toBeInTheDocument();
    });

    it("triggers onOpenProofDrawer and onOpenGraphTrail when clicked", () => {
      const handleOpenDrawer = vi.fn();
      const handleOpenTrail = vi.fn();

      render(
        <EvidenceSummaryCard
          onOpenProofDrawer={handleOpenDrawer}
          onOpenGraphTrail={handleOpenTrail}
        />
      );

      const drawerBtn = screen.getByTestId("open-proof-drawer-btn");
      fireEvent.click(drawerBtn);
      expect(handleOpenDrawer).toHaveBeenCalledTimes(1);

      const trailBtn = screen.getByText("Inspect Neo4j Graph Trail");
      fireEvent.click(trailBtn);
      expect(handleOpenTrail).toHaveBeenCalledTimes(1);
    });
  });

  describe("PaymentProofDrawer", () => {
    it("does not render when isOpen is false", () => {
      const { container } = render(
        <PaymentProofDrawer
          isOpen={false}
          onClose={vi.fn()}
          initialProofPackage={mockProofPackage}
        />
      );
      expect(container.firstChild).toBeNull();
    });

    it("renders drawer with all 4 tabs and allows tab switching", async () => {
      render(
        <PaymentProofDrawer
          isOpen={true}
          onClose={vi.fn()}
          initialProofPackage={mockProofPackage}
        />
      );

      // Verify drawer container
      expect(screen.getByTestId("payment-proof-drawer")).toBeInTheDocument();
      expect(screen.getByText(/Payment Proof & Operational Audit Package/)).toBeInTheDocument();

      // Verify tabs exist
      expect(screen.getByTestId("proof-tab-crypto")).toBeInTheDocument();
      expect(screen.getByTestId("proof-tab-invoice")).toBeInTheDocument();
      expect(screen.getByTestId("proof-tab-graph")).toBeInTheDocument();
      expect(screen.getByTestId("proof-tab-audit")).toBeInTheDocument();

      // Default tab: crypto
      expect(screen.getByText("SHA-256 Preimage Verification")).toBeInTheDocument();
      expect(screen.getByText(/250 sats/)).toBeInTheDocument();

      // Switch to Invoice tab
      fireEvent.click(screen.getByTestId("proof-tab-invoice"));
      expect(screen.getByText("BOLT11 Payment Request")).toBeInTheDocument();

      // Switch to Operational Graph Lineage tab
      fireEvent.click(screen.getByTestId("proof-tab-graph"));
      expect(screen.getByText("Neo4j Operational Lineage (Graph Trail)")).toBeInTheDocument();
      expect(screen.getByText(/\(Equipment: P-101A\)/)).toBeInTheDocument();

      // Switch to Audit Ledger tab
      fireEvent.click(screen.getByTestId("proof-tab-audit"));
      expect(screen.getByText("Audit Ledger & Policy Governance")).toBeInTheDocument();
      expect(screen.getByText(/POL-LIGHTNING-MACHINE-MONEY/)).toBeInTheDocument();
    });

    it("calls onClose when close button is clicked", () => {
      const handleClose = vi.fn();
      render(
        <PaymentProofDrawer
          isOpen={true}
          onClose={handleClose}
          initialProofPackage={mockProofPackage}
        />
      );

      const closeBtn = screen.getByTestId("proof-drawer-close-button");
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it("loads proof package via api if not provided initially", async () => {
      const spy = vi.spyOn(api, "getPaymentProofPackage").mockResolvedValue(mockProofPackage);

      render(
        <PaymentProofDrawer
          isOpen={true}
          onClose={vi.fn()}
          paymentId="PAY-2026-TEST-001"
        />
      );

      expect(spy).toHaveBeenCalledWith("PAY-2026-TEST-001");
      await waitFor(() => {
        expect(screen.getByText("PAY-2026-TEST-001")).toBeInTheDocument();
      });
    });

    it("renders dialog and tablist accessibility attributes", () => {
      render(
        <PaymentProofDrawer
          isOpen={true}
          onClose={vi.fn()}
          initialProofPackage={mockProofPackage}
        />
      );

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute("aria-labelledby", "proof-drawer-title");
      expect(screen.getByRole("tablist", { name: "Proof package categories" })).toBeInTheDocument();
      expect(screen.getByLabelText("Close payment proof drawer")).toBeInTheDocument();
    });
  });
});
