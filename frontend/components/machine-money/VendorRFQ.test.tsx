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
      vendor_id: "maintenance-node-a",
      vendor_name: "Industrial Dynamics Specialist Node A",
      node_pubkey: "02" + "a1" * 32,
      service_id: "bearing-inspection",
      service_name: "High-Frequency Vibration Bearing Diagnostic",
      amount_sats: 250,
      sla_hours: 2.0,
      reliability_score: 0.98,
      reputation_tier: "A+",
      parts_included: ["Synthetic Ester Lubricant"],
      is_synthetic: true,
      within_policy_cap: true,
      score: 80.0,
      valid_until: new Date(Date.now() + 900000).toISOString(),
    },
    {
      candidate_id: "BID-02",
      vendor_id: "eco-rotary-nodes",
      vendor_name: "EcoRotary Maintenance Collective",
      node_pubkey: "03" + "b2" * 32,
      service_id: "bearing-inspection",
      service_name: "Standard Bearing Inspection",
      amount_sats: 180,
      sla_hours: 3.5,
      reliability_score: 0.91,
      reputation_tier: "B",
      parts_included: ["Standard Grease"],
      is_synthetic: true,
      within_policy_cap: true,
      score: 65.0,
      valid_until: new Date(Date.now() + 900000).toISOString(),
    },
    {
      candidate_id: "BID-03",
      vendor_id: "apex-industrial-robotics",
      vendor_name: "Apex Industrial Robotics Dispatch",
      node_pubkey: "02" + "c3" * 32,
      service_id: "bearing-inspection",
      service_name: "Precision Bearing Diagnostic",
      amount_sats: 320,
      sla_hours: 1.0,
      reliability_score: 0.99,
      reputation_tier: "AAA",
      parts_included: ["Laser Coupling Targets"],
      is_synthetic: true,
      within_policy_cap: true,
      score: 95.0,
      valid_until: new Date(Date.now() + 900000).toISOString(),
    },
  ],
  selected_vendor: {
    candidate_id: "BID-03",
    vendor_id: "apex-industrial-robotics",
    vendor_name: "Apex Industrial Robotics Dispatch",
    node_pubkey: "02" + "c3" * 32,
    service_id: "bearing-inspection",
    service_name: "Precision Bearing Diagnostic",
    amount_sats: 320,
    sla_hours: 1.0,
    reliability_score: 0.99,
    reputation_tier: "AAA",
    parts_included: ["Laser Coupling Targets"],
    is_synthetic: true,
    within_policy_cap: true,
    score: 95.0,
    valid_until: new Date(Date.now() + 900000).toISOString(),
  },
  selection_rationale: "Selected vendor: Apex Industrial Robotics Dispatch (apex-industrial-robotics). Reason: Fastest dispatch SLA (1.0h vs catalog avg 2.2h) within the authorized spending policy (320 sats <= 500 sats cap).",
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
    expect(screen.getByText("Synthetic RFQ Model")).toBeInTheDocument();

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
    expect(screen.getByTestId("vendor-card-maintenance-node-a")).toBeInTheDocument();
    expect(screen.getByTestId("vendor-card-eco-rotary-nodes")).toBeInTheDocument();
    expect(screen.getByTestId("vendor-card-apex-industrial-robotics")).toBeInTheDocument();

    // Check values
    expect(screen.getByText("250 sats")).toBeInTheDocument();
    expect(screen.getByText("180 sats")).toBeInTheDocument();
    expect(screen.getAllByText("320 sats").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("1 hrs")).toBeInTheDocument();
    expect(screen.getByText("99%")).toBeInTheDocument();
  });

  it("renders explainable selection rationale box", async () => {
    vi.spyOn(api, "requestVendorRFQ").mockResolvedValue(mockRFQResponse);

    render(<VendorRFQ initialRFQ={mockRFQResponse} />);

    expect(screen.getByTestId("rfq-rationale-box")).toBeInTheDocument();
    expect(screen.getByText(/Fastest dispatch SLA \(1.0h vs catalog avg 2.2h\)/)).toBeInTheDocument();
  });

  it("switches strategy and requests updated RFQ", async () => {
    const rfqSpy = vi.spyOn(api, "requestVendorRFQ").mockResolvedValue({
      ...mockRFQResponse,
      strategy: "LOWEST_COST",
      selected_vendor: mockRFQResponse.candidates[1],
      selection_rationale: "Selected EcoRotary Maintenance Collective for lowest cost.",
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

    const ecoCard = screen.getByTestId("vendor-card-eco-rotary-nodes");
    fireEvent.click(ecoCard);

    expect(handleSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        vendor_id: "eco-rotary-nodes",
      })
    );
  });
});
