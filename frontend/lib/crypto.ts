/**
 * Cryptographic utility functions for Machine Money payment proof verification.
 * Standard Lightning Network invoices verify that:
 * SHA256(preimage) === payment_hash
 */

/**
 * Converts a hex string to a Uint8Array byte buffer.
 */
export function hexToBytes(hex: string): Uint8Array {
  const cleanHex = hex.trim().replace(/^0x/, "");
  if (cleanHex.length % 2 !== 0) {
    throw new Error(`Invalid hex string length: ${cleanHex.length}`);
  }
  const bytes = new Uint8Array(cleanHex.length / 2);
  for (let i = 0; i < cleanHex.length; i += 2) {
    bytes[i / 2] = parseInt(cleanHex.substring(i, i + 2), 16);
  }
  return bytes;
}

/**
 * Converts an ArrayBuffer / Uint8Array to a lowercase hex string.
 */
export function bytesToHex(buffer: ArrayBuffer | Uint8Array): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .toLowerCase();
}

/**
 * Computes SHA-256 digest of raw preimage bytes (or UTF-8 string)
 * using the browser / Node.js Web Crypto API.
 */
export async function sha256Hex(input: string, isHexBytes: boolean = true): Promise<string> {
  const cleanInput = input.trim();
  if (!cleanInput) {
    return "";
  }

  let data: Uint8Array;
  if (isHexBytes) {
    try {
      data = hexToBytes(cleanInput);
    } catch {
      // Fallback to UTF-8 encoded bytes if not valid hex
      data = new TextEncoder().encode(cleanInput);
    }
  } else {
    data = new TextEncoder().encode(cleanInput);
  }

  // Use global crypto.subtle (available in modern browsers & Node 19+)
  if (typeof crypto !== "undefined" && crypto.subtle) {
    const hashBuffer = await crypto.subtle.digest("SHA-256", data as unknown as BufferSource);
    return bytesToHex(hashBuffer);
  }

  throw new Error("Web Crypto API (crypto.subtle) is not available in current environment");
}

/**
 * Verifies whether SHA256(preimage) matches the given payment_hash.
 */
export async function verifyPaymentPreimage(
  preimage: string,
  expectedPaymentHash: string
): Promise<{
  isValid: boolean;
  computedHash: string;
  expectedHash: string;
  isSimulated: boolean;
}> {
  const cleanExpected = expectedPaymentHash.trim().toLowerCase();
  if (!preimage || !expectedPaymentHash) {
    return {
      isValid: false,
      computedHash: "",
      expectedHash: cleanExpected,
      isSimulated: false,
    };
  }

  try {
    const computedHash = await sha256Hex(preimage, true);
    const isValid = computedHash.toLowerCase() === cleanExpected;
    return {
      isValid,
      computedHash,
      expectedHash: cleanExpected,
      isSimulated: false,
    };
  } catch {
    return {
      isValid: false,
      computedHash: "",
      expectedHash: cleanExpected,
      isSimulated: false,
    };
  }
}
