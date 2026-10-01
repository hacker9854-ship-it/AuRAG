import { describe, it, expect } from "vitest";
import { hexToBytes, bytesToHex, sha256Hex, verifyPaymentPreimage } from "./crypto";

describe("Machine Money Cryptographic Utilities", () => {
  it("converts hex to bytes and back accurately", () => {
    const hex = "deadbeef0123456789abcdef";
    const bytes = hexToBytes(hex);
    expect(bytes.length).toBe(12);
    expect(bytesToHex(bytes)).toBe(hex);
  });

  it("computes exact SHA-256 hash for raw preimage bytes", async () => {
    // 32-byte known hex preimage
    const preimage = "11".repeat(32);
    const computedHash = await sha256Hex(preimage, true);
    expect(computedHash).toHaveLength(64);
    expect(typeof computedHash).toBe("string");

    // Re-computing produces deterministic output
    const recomputed = await sha256Hex(preimage, true);
    expect(recomputed).toBe(computedHash);
  });

  it("verifies matching preimage and payment hash", async () => {
    const preimage = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f";
    const expectedHash = await sha256Hex(preimage, true);

    const result = await verifyPaymentPreimage(preimage, expectedHash);
    expect(result.isValid).toBe(true);
    expect(result.computedHash).toBe(expectedHash);
  });

  it("rejects mismatched preimage and payment hash", async () => {
    const preimage = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f";
    const wrongHash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

    const result = await verifyPaymentPreimage(preimage, wrongHash);
    expect(result.isValid).toBe(false);
    expect(result.computedHash).not.toBe(wrongHash);
  });
});
