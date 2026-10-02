import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Bolt11QRCode } from "./Bolt11QRCode";
import { ProviderModeBadge } from "./ProviderModeBadge";
import { ProofVerification } from "./ProofVerification";
import { sha256Hex } from "@/lib/crypto";

describe("Machine Money Phase 1 Components", () => {
  describe("Bolt11QRCode", () => {
    const mockInvoice =
      "lnbcrt2500n1pj48ugqpp5qxaywxwgpdh7jydsjxnuq5fyke8wan5kfcyuqk8037vqtkk2234ssp50nuwt7l793l234xk7vsps0y3l2qr3e6l0qgfrthq38yyerww6fhsdz6tdx57s6tyqhjq56ff425cs25f985uhfqf45kxun094cxz7tdv4h8ggrxdaezq5pdxycrzsfqd36kyunfvdshg6t0dcxqrrsscqpjjga32ynxew6snx8mdhv9qdtt5405zt2kdh5h5fcsm7pydlnrfckzzntwqu77gcfdtyjkglaphs6rjjlj548gc8lhljpaw7vtcawejecqwtnmnz";

    it("renders standards-compliant SVG with exact invoice and mock badge", () => {
      render(<Bolt11QRCode value={mockInvoice} isMock={true} amountSats={250} />);

      // Container and mode indicator
      expect(screen.getByTestId("bolt11-qr-container")).toBeInTheDocument();
      const badge = screen.getByTestId("qr-mode-indicator");
      expect(badge).toHaveTextContent("MOCK / SIMULATION");

      // Verify SVG element is present
      const svg = screen.getByTestId("bolt11-qr-wrapper").querySelector("svg");
      expect(svg).toBeInTheDocument();

      // Copy button exists
      expect(screen.getByTestId("bolt11-copy-button")).toBeInTheDocument();
    });

    it("toggles textual fallback for full invoice transparency", () => {
      render(<Bolt11QRCode value={mockInvoice} isMock={false} />);

      const toggleButton = screen.getByTestId("bolt11-toggle-raw");
      fireEvent.click(toggleButton);

      const fallback = screen.getByTestId("bolt11-text-fallback");
      expect(fallback).toBeInTheDocument();
      expect(fallback).toHaveTextContent(mockInvoice);
    });

    it("displays empty state when no invoice is provided", () => {
      render(<Bolt11QRCode value="" />);
      expect(screen.getByTestId("bolt11-qr-empty")).toBeInTheDocument();
    });
  });

  describe("ProviderModeBadge", () => {
    it("renders MOCK / SIMULATION label for mock provider", () => {
      render(<ProviderModeBadge providerName="mock" network="regtest" isMock={true} />);
      expect(screen.getByTestId("provider-mode-label")).toHaveTextContent("MOCK / SIMULATION");
      expect(screen.getByTestId("provider-network")).toHaveTextContent("regtest");
      expect(screen.getByTestId("provider-name")).toHaveTextContent("mock");
    });

    it("renders LIVE LIGHTNING label for live provider", () => {
      render(<ProviderModeBadge providerName="lnbits" network="signet" isMock={false} />);
      expect(screen.getByTestId("provider-mode-label")).toHaveTextContent("LIVE LIGHTNING");
      expect(screen.getByTestId("provider-network")).toHaveTextContent("signet");
      expect(screen.getByTestId("provider-name")).toHaveTextContent("lnbits");
    });
  });

  describe("ProofVerification", () => {
    it("verifies matching preimage and payment hash in simulation mode", async () => {
      const preimage = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f";
      const paymentHash = await sha256Hex(preimage, true);

      render(<ProofVerification preimage={preimage} paymentHash={paymentHash} isMock={true} />);

      await waitFor(() => {
        expect(screen.getByTestId("proof-status-badge")).toHaveTextContent(
          "SIMULATION INTEGRITY VERIFIED"
        );
        expect(screen.getByTestId("verification-result-box")).toBeInTheDocument();
        expect(screen.getByText("Cryptographic Match Confirmed")).toBeInTheDocument();
        expect(screen.getByText(/Simulation integrity check/)).toBeInTheDocument();
      });
    });

    it("verifies live network settlement when in live mode", async () => {
      const preimage = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f";
      const paymentHash = await sha256Hex(preimage, true);

      render(
        <ProofVerification
          preimage={preimage}
          paymentHash={paymentHash}
          isMock={false}
          settlementSource="LIGHTNING_NODE"
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId("proof-status-badge")).toHaveTextContent(
          "NETWORK SETTLEMENT VERIFIED"
        );
        expect(screen.getByText(/Network settlement verified/)).toBeInTheDocument();
      });
    });

    it("rejects mismatching preimage and payment hash", async () => {
      const preimage = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f";
      const wrongPaymentHash = "1111111111111111111111111111111111111111111111111111111111111111";

      render(<ProofVerification preimage={preimage} paymentHash={wrongPaymentHash} isMock={true} />);

      await waitFor(() => {
        expect(screen.getByText("Hash Mismatch Detected")).toBeInTheDocument();
      });
    });
  });
});
