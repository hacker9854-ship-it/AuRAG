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

  it("does not render when isOpen is false", () => {
    render(<SystemReadinessModal isOpen={false} onClose={vi.fn()} health={mockHealth} />);
    expect(screen.queryByTestId("system-readiness-modal")).not.toBeInTheDocument();
  });

  it("renders safe system readiness modal with all 6 operational subsystems", () => {
    render(<SystemReadinessModal isOpen={true} onClose={vi.fn()} health={mockHealth} />);

    expect(screen.getByTestId("system-readiness-modal")).toBeInTheDocument();
    expect(screen.getByText("Safe System Readiness & Operational Health")).toBeInTheDocument();
    expect(screen.getByText("ALL SYSTEMS NOMINAL")).toBeInTheDocument();

    // Check all 6 subsystem cards
    expect(screen.getByTestId("subsystem-lightning")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-policy")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-database")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-rfq")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-economics")).toBeInTheDocument();
    expect(screen.getByTestId("subsystem-security")).toBeInTheDocument();

    // Verify key safety guarantees
    expect(screen.getByText("0 Secrets in Memory")).toBeInTheDocument();
    expect(screen.getByText("Strict Backend Rejection")).toBeInTheDocument();
    expect(screen.getByText(/Safe Observability Notice/i)).toBeInTheDocument();
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
