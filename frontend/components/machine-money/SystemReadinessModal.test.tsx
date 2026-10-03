import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SystemReadinessModal } from "./SystemReadinessModal";
import type { MachineMoneyHealth } from "@/lib/api";

describe("Machine Money Phase 10: Safe System Readiness Indicators (Task 10.3)", () => {
  const mockHealth: MachineMoneyHealth = {
    provider_name: "mock",
    is_connected: true,
    network: "regtest",
    balance_sats: 1000000,
    latency_ms: 1.2,
    details: {
      simulation: true,
      label: "MOCK / SIMULATION",
    },
  };

  const liveHealth: MachineMoneyHealth = {
    provider_name: "lnbits",
    is_connected: true,
    network: "regtest",
    balance_sats: 500000,
    latency_ms: 18.4,
    is_mock: false,
    details: {
      simulation: false,
      label: "LIVE LIGHTNING",
    },
  };

  it("does not render when isOpen is false", () => {
    render(<SystemReadinessModal isOpen={false} onClose={vi.fn()} health={mockHealth} />);
    expect(screen.queryByTestId("system-readiness-modal")).not.toBeInTheDocument();
  });

  it("renders safe system readiness modal with truthful simulation environment status", () => {
    render(<SystemReadinessModal isOpen={true} onClose={vi.fn()} health={mockHealth} />);

    expect(screen.getByTestId("system-readiness-modal")).toBeInTheDocument();
    expect(screen.getByText("Safe System Readiness & Operational Health")).toBeInTheDocument();
    expect(screen.getByText("SIMULATION ENVIRONMENT READY")).toBeInTheDocument();

    // Check all 6 subsystem cards
    expect(screen.getByTestId("subsystem-lightning")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-policy")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-database")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-rfq")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-economics")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-security")).toBeInTheDocument();

    // Verify truthful mock labelling (PRD3 Task 3.2)
    expect(screen.getAllByText("DEMO VALUE (MOCK)").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("3 Synthetic Vendor Nodes")).toBeInTheDocument();
    expect(screen.getByText("Modelled Downtime Exposure")).toBeInTheDocument();

    // Verify key safety guarantees
    expect(screen.getByText("0 Secrets in Memory")).toBeInTheDocument();
    expect(screen.getByText("Strict Backend Rejection")).toBeInTheDocument();
    expect(screen.getByText(/Safe Observability Notice/i)).toBeInTheDocument();
  });

  it("renders ALL SYSTEMS NOMINAL and CONNECTED status when live provider is verified", () => {
    render(<SystemReadinessModal isOpen={true} onClose={vi.fn()} health={liveHealth} />);

    expect(screen.getByText("ALL SYSTEMS NOMINAL")).toBeInTheDocument();
    expect(screen.getByText("CONNECTED")).toBeInTheDocument();
    expect(screen.getByText("18.4 ms")).toBeInTheDocument();
    expect(screen.getByText(/500,?000 sats/)).toBeInTheDocument();
  });

  it("renders GRAPH STATUS: DEGRADED / FALLBACK when Neo4j is degraded, never ALL SYSTEMS NOMINAL", () => {
    const degradedGraphHealth: MachineMoneyHealth = {
      ...liveHealth,
      details: {
        ...liveHealth.details,
        graph_status: "DEGRADED / FALLBACK",
        graph_connected: false,
      },
    };
    render(<SystemReadinessModal isOpen={true} onClose={vi.fn()} health={degradedGraphHealth} />);
    expect(screen.queryByText("ALL SYSTEMS NOMINAL")).not.toBeInTheDocument();
    expect(screen.getByText("GRAPH STATUS: DEGRADED / FALLBACK")).toBeInTheDocument();
    expect(screen.getByText("DEGRADED / FALLBACK")).toBeInTheDocument();
  });

  it("ensures zero secret keys or private hashes are visible in rendered output", () => {
    const { container } = render(
      <SystemReadinessModal isOpen={true} onClose={vi.fn()} health={mockHealth} />
    );
    const content = container.textContent || "";

    expect(content).not.toMatch(/gsk_[a-zA-Z0-9]+/);
    expect(content).not.toMatch(/AIza[a-zA-Z0-9_-]+/);
    expect(content).not.toMatch(/ghp_[a-zA-Z0-9]+/);
    expect(content).not.toMatch(/admin_key/i);
    expect(content).not.toMatch(/invoice_key/i);
  });

  it("invokes onClose when close button is clicked", () => {
    const onCloseSpy = vi.fn();
    render(<SystemReadinessModal isOpen={true} onClose={onCloseSpy} health={mockHealth} />);

    const closeButton = screen.getByTestId("system-readiness-close");
    fireEvent.click(closeButton);

    expect(onCloseSpy).toHaveBeenCalledTimes(1);
  });

  it("complies with WCAG 2.1 AA dialog semantics", () => {
    render(<SystemReadinessModal isOpen={true} onClose={vi.fn()} health={mockHealth} />);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "system-readiness-title");
  });
});
