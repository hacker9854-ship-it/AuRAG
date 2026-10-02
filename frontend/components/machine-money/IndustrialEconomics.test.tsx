import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { IndustrialEconomics } from "./IndustrialEconomics";
import * as api from "@/lib/api";

const mockMetrics: api.MachineMoneyMetrics = {
  total_spend_sats: 1600,
  total_spend_msat: 1600000,
  total_fee_sats: 4,
  fiat_spend_usd_estimate: 1.04,
  settled_count: 3,
  pending_count: 1,
  failed_count: 0,
  total_transactions: 4,
  autonomous_count: 2,
  human_approval_count: 2,
  autonomous_rate_percentage: 66.7,
  average_settlement_latency_ms: 1842.0,
  average_settlement_latency_seconds: 1.842,
  vendor_spend: [
    {
      vendor_name: "Industrial Dynamics Specialist Node",
      spend_sats: 1200,
      payment_count: 2,
      percentage: 75.0,
    },
    {
      vendor_name: "BearingTech Diagnostic Services",
      spend_sats: 400,
      payment_count: 1,
      percentage: 25.0,
    },
  ],
  total_quotes_generated: 4,
  quotes_converted: 3,
  quote_to_payment_conversion_rate: 75.0,
  computed_at: new Date().toISOString(),
};

const mockEconomics: api.IndustrialEconomicsModel = {
  is_estimated: true,
  estimated_marker: "ESTIMATED_SYNTHETIC_MODEL",
  calculation_version: "v2026.1-industrial-m2m",
  equipment_tag: "P-101A",
  equipment_name: "Heavy Crude Distillation Charge Pump P-101A",
  downtime_hours_avoided: 4.5,
  hourly_downtime_cost_usd: 260000.0,
  estimated_downtime_exposure_usd: 1170000.0,
  risk_weighted_exposure_usd: 994500.0,
  intervention_cost_sats: 250,
  intervention_cost_usd: 0.1625,
  net_value_preserved_usd: 1169999.84,
  protection_multiple: 7200000.0,
  lead_time_saved_hours: 4.2,
  assumptions: {
    plant_id: "plant-mumbai-01",
    equipment_tag: "P-101A",
    equipment_name: "Heavy Crude Distillation Charge Pump P-101A",
    criticality_tier: "TIER_1_CRITICAL",
    hourly_downtime_cost_usd: 260000.0,
    unmitigated_downtime_hours: 4.5,
    catastrophic_failure_probability: 0.85,
    manual_procurement_hours: 4.2,
    autonomous_m2m_dispatch_seconds: 2.1,
    default_intervention_sats: 250,
    btc_fiat_usd_rate: 65000.0,
    data_basis: "Synthetic plant model (Petrochemical refining unit P-101A)",
    assumptions_version: "2026.1-synthetic-p101a",
  },
  formula: "Net Value Preserved = (Avoided Downtime Hours * Hourly Outage Rate) - Intervention Cost USD",
  risk_weighted_formula: "Risk-Weighted Exposure = Gross Exposure * Failure Probability Factor",
  data_basis: "Synthetic plant model (Petrochemical refining unit P-101A)",
  transparency_notes: "Modelled estimate based on synthetic industrial plant assumptions for hackathon demonstration.",
  computed_at: new Date().toISOString(),
};

describe("IndustrialEconomics Component (Phase 5 / Tasks 5.3 & 5.4)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, "getMachineMoneyMetrics").mockResolvedValue(mockMetrics);
    vi.spyOn(api, "getIndustrialEconomics").mockResolvedValue(mockEconomics);
    vi.spyOn(api, "calculateCustomIndustrialEconomics").mockResolvedValue({
      ...mockEconomics,
      downtime_hours_avoided: 6.0,
      estimated_downtime_exposure_usd: 1560000.0,
      net_value_preserved_usd: 1559999.84,
    });
  });

  it("renders Machine Money Intelligence and Industrial Economics dashboard cards", async () => {
    render(<IndustrialEconomics equipmentTag="P-101A" activeInterventionSats={250} />);

    // Title and version badges
    expect(screen.getByText("Machine Money Intelligence & Industrial Economics")).toBeInTheDocument();
    expect(screen.getByText("v2026.1-industrial-m2m")).toBeInTheDocument();
    expect(screen.getByText("MODELLED / SYNTHETIC")).toBeInTheDocument();

    // Downtime exposure cards
    await waitFor(() => {
      expect(screen.getByText("$1.17M")).toBeInTheDocument();
      expect(screen.getByText("Modelled Downtime Exposure")).toBeInTheDocument();
      expect(screen.getByText("250")).toBeInTheDocument();
      expect(screen.getByText("7.2M×")).toBeInTheDocument();
    });

    // M2M metrics
    expect(screen.getByText("Total M2M Spend")).toBeInTheDocument();
    expect(screen.getByText("Autonomous Execution")).toBeInTheDocument();
    expect(screen.getByText("Avg Settlement Latency")).toBeInTheDocument();
    expect(screen.getByText("Quote-to-Payment")).toBeInTheDocument();

    // Vendor spend distribution
    expect(screen.getByText("Vendor Settlement Distribution (Autonomous Procurement)")).toBeInTheDocument();
    expect(screen.getByText("Industrial Dynamics Specialist Node")).toBeInTheDocument();
  });

  it("opens Explainability Drawer and displays mathematical formula and assumptions table (Task 5.4)", async () => {
    render(<IndustrialEconomics equipmentTag="P-101A" activeInterventionSats={250} />);

    // Open drawer
    const explainBtn = screen.getByRole("button", { name: /Explainability Drawer/i });
    fireEvent.click(explainBtn);

    // Verify dialog content
    expect(screen.getByText("Industrial Economics Explainability & Assumption Basis")).toBeInTheDocument();
    expect(screen.getByText("Mathematical Calculation Formula")).toBeInTheDocument();
    expect(screen.getByText(/Step-by-Step Economic Derivation:/)).toBeInTheDocument();
    expect(screen.getByText(/Modelled Downtime Exposure = Avoided Outage Duration \(4\.5h\) × Outage Cost Rate/)).toBeInTheDocument();
    expect(screen.getByText(/Net Value Preserved = \(Avoided Outage Hours/)).toBeInTheDocument();
    expect(screen.getByText("Parameterized Synthetic Plant Assumptions (Task 5.2)")).toBeInTheDocument();
    expect(screen.getAllByText(/\$260,000/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("85%")).toBeInTheDocument();

    expect(screen.getByText("Interactive Sensitivity Sandbox (Live Model Testing)")).toBeInTheDocument();

    // Close drawer
    const closeBtn = screen.getByRole("button", { name: "Close Drawer" });
    fireEvent.click(closeBtn);

    expect(screen.queryByText("Industrial Economics Explainability & Assumption Basis")).not.toBeInTheDocument();
  });

  it("copies formula to clipboard from Explainability Drawer", async () => {
    const clipboardSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: clipboardSpy,
      },
    });

    render(<IndustrialEconomics equipmentTag="P-101A" activeInterventionSats={250} />);

    // Open drawer
    fireEvent.click(screen.getByRole("button", { name: /Explainability Drawer/i }));

    // Click copy button
    const copyBtn = screen.getByRole("button", { name: /Copy/i });
    fireEvent.click(copyBtn);

    expect(clipboardSpy).toHaveBeenCalled();
  });
});
