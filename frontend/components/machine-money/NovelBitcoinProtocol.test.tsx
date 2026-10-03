import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { NovelBitcoinProtocol } from "./NovelBitcoinProtocol";
import * as api from "@/lib/api";

describe("NovelBitcoinProtocol Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(api, "getNWCInfo").mockResolvedValue({
      protocol: "NIP-47 (Nostr Wallet Connect)",
      wallet_pubkey: "a4b1c2d3e4f5a4b1c2d3e4f5a4b1c2d3e4f5a4b1c2d3e4f5a4b1c2d3e4f5a4b1",
      client_pubkey: "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
      relays: ["wss://relay.damus.io", "wss://nos.lol"],
      methods_supported: ["pay_invoice", "get_balance", "get_info"],
      max_autonomous_spend_sats: 500,
      encryption: "NIP-04 (secp256k1 ECDH + AES-256-CBC)",
      request_kind: 23194,
      response_kind: 23195,
      status: "READY",
    });

    vi.spyOn(api, "getRoutingTopology").mockResolvedValue({
      nodes: [
        { pubkey: "node-plant", alias: "AuRAG Plant Edge", role: "SOURCE", location: "Mumbai", color: "#8b5cf6" },
        { pubkey: "node-vendor-1", alias: "Apex Diagnostics Node", role: "DESTINATION", location: "Bangalore", color: "#10b981" },
      ],
      channels: [
        { channel_id: "chan_source_lsp", node1: "node-plant", node2: "node-lsp", capacity_sats: 1000000, base_fee_msat: 1000, fee_rate_ppm: 50, cltv_delta: 40 },
      ],
      supported_vendors: [
        { id: "apex-diagnostics", name: "Apex Diagnostics", node_pubkey: "node-vendor-1", reputation: "99.4% SLA" },
      ],
    });

    vi.spyOn(api, "calculateMultiHopRoute").mockResolvedValue({
      target_vendor_id: "apex-diagnostics",
      target_vendor_name: "Apex Diagnostics Node",
      amount_sats: 250,
      total_fee_sats: 1,
      total_fee_ppm: 15,
      final_amount_sats: 251,
      path_nodes: [
        { pubkey: "node-plant", alias: "AuRAG Plant Edge Gateway", role: "SOURCE", location: "Mumbai, IN" },
        { pubkey: "node-lsp", alias: "Bitshala Regional LSP", role: "REGIONAL_LSP", location: "New Delhi, IN" },
        { pubkey: "node-hub", alias: "Industrial Peering Hub", role: "PEERING_HUB", location: "BOM-IX, Mumbai" },
        { pubkey: "node-vendor-1", alias: "Apex Diagnostics Node", role: "DESTINATION", location: "Bangalore, IN" },
      ],
      hops: [
        {
          hop_index: 1,
          from_node: "node-plant",
          from_alias: "AuRAG Plant Edge Gateway",
          to_node: "node-lsp",
          to_alias: "Bitshala Regional LSP",
          channel_id: "chan_source_lsp",
          fee_sats: 1,
          cltv_delta: 40,
          outgoing_cltv: 890144,
          amount_to_forward_sats: 251,
        },
      ],
      sphinx_onion_packet: {
        total_packet_size_bytes: 1366,
        packet_version: 0,
        ephemeral_key_hex: "02abcd1234abcd",
        layers: [
          {
            layer_index: 1,
            hop_alias: "Bitshala Regional LSP",
            ephemeral_key_slice: "02abcd1234...",
            payload_digest: "9876543210...",
            payload_summary: {
              amt_to_forward: 251,
              outgoing_cltv: 890144,
              short_channel_id: "chan_source_lsp",
            },
          },
        ],
      },
      htlc_settlement_cascade: {
        payment_hash: "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        payment_preimage: "aabbccddeeff11223344556677889900aabbccddeeff11223344556677889900",
        sha256_invariant_verified: true,
        steps: [
          {
            step: 1,
            phase: "FORWARD_HTLC",
            from: "AuRAG Plant Edge Gateway",
            to: "Bitshala Regional LSP",
            action: "ADD_HTLC",
            cltv_expiry: 890144,
            amount_sats: 251,
            evidence: "Forward HTLC offered with CLTV=890144",
          },
          {
            step: 2,
            phase: "BACKWARD_SETTLE",
            from: "Apex Diagnostics Node",
            to: "Bitshala Regional LSP",
            action: "FULFILL_HTLC",
            cltv_expiry: 890024,
            amount_sats: 250,
            evidence: "Preimage revealed",
          },
        ],
      },
    });
  });

  it("renders Section 20 headers and NWC architecture details", async () => {
    render(<NovelBitcoinProtocol />);

    expect(screen.getByText(/Section 20: Novel Bitcoin Protocol Innovations/i)).toBeInTheDocument();
    expect(screen.getByText(/NIP-47 \(NWC\)/i)).toBeInTheDocument();
    expect(screen.getByText(/BOLT 04 Sphinx Onion/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/kind: 23194/i)).toBeInTheDocument();
      expect(screen.getByText(/kind: 23195/i)).toBeInTheDocument();
      expect(screen.getByText(/wss:\/\/relay\.damus\.io/i)).toBeInTheDocument();
    });
  });

  it("executes NWC payment when 'Send Over Nostr' is clicked", async () => {
    vi.spyOn(api, "executeNWCPayment").mockResolvedValue({
      status: "SETTLED",
      method: "pay_invoice",
      amount_sats: 250,
      fee_sats: 1,
      preimage: "beef00112233445566778899aabbccddeeff00112233445566778899aabbccdd",
      payment_hash: "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      request_event: {
        id: "req123456789012345678901234567890",
        pubkey: "pub123456789012345678901234567890",
        created_at: 1727900000,
        kind: 23194,
        tags: [["p", "walletpubkey12345678901234567890"]],
        content: "encrypted_ciphertext_abc123",
        sig: "schnorr_sig_12345678901234567890",
      },
      response_event: {
        id: "res123456789012345678901234567890",
        pubkey: "walletpubkey12345678901234567890",
        created_at: 1727900001,
        kind: 23195,
        tags: [["p", "pub123456789012345678901234567890"]],
        content: "encrypted_response_payload",
        sig: "schnorr_res_sig_12345678901234567890",
      },
      relay: "wss://relay.damus.io",
      preimage_verified: true,
      settled_at: "2026-10-03T18:00:00Z",
    });

    render(<NovelBitcoinProtocol />);

    const sendBtn = screen.getByRole("button", { name: /Send Over Nostr/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/NWC Payment Settled/i)).toBeInTheDocument();
      expect(screen.getByText(/VALID SHA-256 MATCH/i)).toBeInTheDocument();
      expect(screen.getByText(/NIP-47 Request Event \(kind: 23194\)/i)).toBeInTheDocument();
      expect(screen.getByText(/NIP-47 Response Event \(kind: 23195\)/i)).toBeInTheDocument();
    });
  });

  it("switches to multi-hop tab and displays 4-hop topology and Sphinx onion layers", async () => {
    render(<NovelBitcoinProtocol />);

    const multiHopTab = screen.getByRole("tab", { name: /Multi-Hop HTLC Onion Routing/i });
    fireEvent.click(multiHopTab);

    await waitFor(() => {
      expect(screen.getByText(/4-Hop Industrial Lightning Path/i)).toBeInTheDocument();
      expect(screen.getByText(/Sphinx Packet: 1,366 Bytes/i)).toBeInTheDocument();
      expect(screen.getByText(/Sphinx Onion Packet Layers \(BOLT 04\)/i)).toBeInTheDocument();
      expect(screen.getByText(/HTLC Atomic Settlement Cascade/i)).toBeInTheDocument();
    });
  });
});
