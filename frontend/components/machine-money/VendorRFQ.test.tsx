import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { VendorRFQ } from "./VendorRFQ";
import * as api from "@/lib/api";

const mockRFQResponse: api.VendorRFQResponse = {
  rfq_id: "RFQ-TEST-001",
  requested_at: new Date().toISOString(),
  service_id: "bearing-inspection",
  equipment_id: "P-101A",
  strategy: "FASTEST_SLA",
  policy_cap_sats: 500,
  candidates: [
    {
      candidate_id: "BID-01",
      vendor_id: "apex-diagnostics",
      vendor_name: "Apex Diagnostics",
      node_pubkey: "02" + "a1".repeat(32),
      service_id: "bearing-inspection",
      service_name: "Precision Bearing Inspection & Laser Alignment",
      amount_sats: 250,
      sla_hours: 1.2,
      reliability_score: 0.994,
      reputation_tier: "AAA",
      parts_included: ["Laser Coupling Targets", "Acoustic Sensor Pods", "Mobil SHC 100"],
      is_synthetic: true,
      within_policy_cap: true,
      score: 92.5,
      valid_until: new Date(Date.now() + 900000).toISOString(),
    },
    {
      candidate_id: "BID-02",
      vendor_id: "precision-dynamics",
      vendor_name: "Precision Dynamics",
      node_pubkey: "03" + "b2".repeat(32),
      service_id: "bearing-inspection",
      service_name: "Express Ultrasound Diagnostic & Vibration Analysis",
      amount_sats: 320,
      sla_hours: 0.8,
      reliability_score: 0.989,
      reputation_tier: "AA+",
      parts_included: ["Ultrasound Sensor Probe", "Sensor Coupling Gel"],
      is_synthetic: true,
      within_policy_cap: true,
      score: 96.0,
      valid_until: new Date(Date.now() + 900000).toISOString(),
    },
    {
      candidate_id: "BID-03",
      vendor_id: "quantum-reliability",
      vendor_name: "Quantum Reliability",
      node_pubkey: "02" + "c3".repeat(32),
      service_id: "bearing-inspection",
      service_name: "Comprehensive Rotary Dynamics & Bearing Overhaul",
      amount_sats: 450,
      sla_hours: 2.5,
      reliability_score: 0.975,
      reputation_tier: "A",
      parts_included: ["Complete Bearing Assembly", "Synthetic Lubricant Pack"],
      is_synthetic: true,
      within_policy_cap: true,
      score: 68.0,
      valid_until: new Date(Date.now() + 900000).toISOString(),
    },
  ],
  selected_vendor: {
    candidate_id: "BID-02",
    vendor_id: "precision-dynamics",
    vendor_name: "Precision Dynamics",
    node_pubkey: "03" + "b2".repeat(32),
    service_id: "bearing-inspection",
    service_name: "Express Ultrasound Diagnostic & Vibration Analysis",
    amount_sats: 320,
    sla_hours: 0.8,
    reliability_score: 0.989,
    reputation_tier: "AA+",
    parts_included: ["Ultrasound Sensor Probe", "Sensor Coupling Gel"],
    is_synthetic: true,
    within_policy_cap: true,
    score: 96.0,
    valid_until: new Date(Date.now() + 900000).toISOString(),
  },
  selection_rationale: "Selected vendor: Precision Dynamics (precision-dynamics). Reason: Fastest dispatch SLA (0.8h vs catalog avg 1.5h) within authorized spending policy (320 sats <= 500 sats cap).",
  scoring_model: {
    rule: "Minimize SLA hours subject to amount_sats <= policy_cap_sats",
    strategy: "FASTEST_SLA",
  },
  is_synthetic: true,
  synthetic_disclosure: "Synthetic vendor quote model for Bitshala BOSS Battle Machine Money autonomous bidding demonstration",
};

describe("Machine Money Phase 4: Multi-Vendor RFQ Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders container, strategy toggles, and synthetic disclosure", async () => {
    vi.spyOn(api, "requestVendorRFQ").mockResolvedValue(mockRFQResponse);

    render(
      <VendorRFQ
        serviceId="bearing-inspection"
        equipmentId="P-101A"
        policyCapSats={500}
        initialRFQ={mockRFQResponse}
      />
    );

    expect(screen.getByTestId("vendor-rfq-container")).toBeInTheDocument();
    expect(screen.getByText("Autonomous RFQ Marketplace")).toBeInTheDocument();
    expect(screen.getByText("Pre-approved Synthetic Vendor Nodes")).toBeInTheDocument();

    // 4 Strategy buttons
    expect(screen.getByTestId("strategy-fastest_sla")).toBeInTheDocument();
    expect(screen.getByTestId("strategy-lowest_cost")).toBeInTheDocument();
    expect(screen.getByTestId("strategy-highest_reliability")).toBeInTheDocument();
    expect(screen.getByTestId("strategy-balanced")).toBeInTheDocument();
  });

  it("renders candidate vendor cards with amounts, SLAs, and reputation tiers", async () => {
    vi.spyOn(api, "requestVendorRFQ").mockResolvedValue(mockRFQResponse);

    render(<VendorRFQ initialRFQ={mockRFQResponse} />);

    // Check candidate cards
    expect(screen.getByTestId("vendor-card-apex-diagnostics")).toBeInTheDocument();
    expect(screen.getByTestId("vendor-card-precision-dynamics")).toBeInTheDocument();
    expect(screen.getByTestId("vendor-card-quantum-reliability")).toBeInTheDocument();

    // Check values
    expect(screen.getByText("250 sats")).toBeInTheDocument();
    expect(screen.getAllByText("320 sats").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("450 sats")).toBeInTheDocument();
    expect(screen.getByText("0.8 hrs")).toBeInTheDocument();
    expect(screen.getAllByText(/Synthetic Node/).length).toBe(3);
  });

  it("renders explainable selection rationale box with scoring model", async () => {
    vi.spyOn(api, "requestVendorRFQ").mockResolvedValue(mockRFQResponse);

    render(<VendorRFQ initialRFQ={mockRFQResponse} />);

    expect(screen.getByTestId("rfq-rationale-box")).toBeInTheDocument();
    expect(screen.getByText(/Fastest dispatch SLA \(0.8h vs catalog avg 1.5h\)/)).toBeInTheDocument();
    expect(screen.getByText(/Score = \(0.5 × CostNorm\) \+ \(0.3 × LatencyNorm\) \+ \(0.2 × SLANorm\)/)).toBeInTheDocument();
  });

  it("switches strategy and requests updated RFQ", async () => {
    const rfqSpy = vi.spyOn(api, "requestVendorRFQ").mockResolvedValue({
      ...mockRFQResponse,
      strategy: "LOWEST_COST",
      selected_vendor: mockRFQResponse.candidates[0],
      selection_rationale: "Selected Apex Diagnostics for lowest cost (250 sats).",
    });

    render(<VendorRFQ initialRFQ={mockRFQResponse} />);

    const lowestCostBtn = screen.getByTestId("strategy-lowest_cost");
    fireEvent.click(lowestCostBtn);

    await waitFor(() => {
      expect(rfqSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          strategy: "LOWEST_COST",
        })
      );
    });
  });

  it("allows manual candidate card selection override", async () => {
    const handleSelect = vi.fn();
    vi.spyOn(api, "requestVendorRFQ").mockResolvedValue(mockRFQResponse);

    render(
      <VendorRFQ
        initialRFQ={mockRFQResponse}
        onSelectCandidate={handleSelect}
      />
    );

    const apexCard = screen.getByTestId("vendor-card-apex-diagnostics");
    fireEvent.click(apexCard);

    expect(handleSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        vendor_id: "apex-diagnostics",
      })
    );
  });
});
