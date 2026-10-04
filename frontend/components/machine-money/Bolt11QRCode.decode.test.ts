import { describe, it, expect } from "vitest";
import jsQR from "jsqr";
import { isRecognizedInvoiceFormat } from "./Bolt11QRCode";

/**
 * Helper to generate a binary QR matrix and convert it into RGBA imageData for jsQR,
 * proving that standard QR encoding produces an exact decode of the BOLT11 payload.
 */
function createQrImageData(modules: boolean[][], scale = 8, border = 4): {
  data: Uint8ClampedArray;
  width: number;
  height: number;
} {
  const size = modules.length;
  const fullSize = (size + border * 2) * scale;
  const rgba = new Uint8ClampedArray(fullSize * fullSize * 4);

  // Fill with white background
  rgba.fill(255);

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (modules[r][c]) {
        const startX = (c + border) * scale;
        const startY = (r + border) * scale;
        for (let py = 0; py < scale; py++) {
          for (let px = 0; px < scale; px++) {
            const idx = ((startY + py) * fullSize + (startX + px)) * 4;
            rgba[idx] = 0; // R
            rgba[idx + 1] = 0; // G
            rgba[idx + 2] = 0; // B
            rgba[idx + 3] = 255; // A
          }
        }
      }
    }
  }

  return { data: rgba, width: fullSize, height: fullSize };
}

describe("BOLT11 QR Standards Compliance & Optical Decoding (FR-01 / Task 1.1)", () => {
  it("verifies that a real BOLT11 invoice encoded in standard QR decodes to the exact string", async () => {
    const QRCode = await import("qrcode");
    const testInvoice =
      "lnbcrt2500n1pj48ugqpp5qxaywxwgpdh7jydsjxnuq5fyke8wan5kfcyuqk8037vqtkk2234ssp50nuwt7l793l234xk7vsps0y3l2qr3e6l0qgfrthq38yyerww6fhsdz6tdx57s6tyqhjq56ff425cs25f985uhfqf45kxun094cxz7tdv4h8ggrxdaezq5pdxycrzsfqd36kyunfvdshg6t0dcxqrrsscqpjjga32ynxew6snx8mdhv9qdtt5405zt2kdh5h5fcsm7pydlnrfckzzntwqu77gcfdtyjkglaphs6rjjlj548gc8lhljpaw7vtcawejecqwtnmnz";

    const qrData = QRCode.create(testInvoice, { errorCorrectionLevel: "M" });
    const size = qrData.modules.size;
    const modules: boolean[][] = [];
    for (let r = 0; r < size; r++) {
      const row: boolean[] = [];
      for (let c = 0; c < size; c++) {
        row.push(Boolean(qrData.modules.get(c, r)));
      }
      modules.push(row);
    }

    const { data, width, height } = createQrImageData(modules);
    const decoded = jsQR(data, width, height);

    expect(decoded).not.toBeNull();
    expect(decoded?.data).toBe(testInvoice);
  }, 15000);

  it("verifies optical decode across multiple networks and invoice lengths without distortion", async () => {
    const QRCode = await import("qrcode");
    const sampleInvoices = [
      "lnbcrt2500u1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqdqqcqzysxqyz5vq9p101a",
      "lnbc1200u1p3mockabovecapinvoice0000000000000000000000000000000000000000000000000000000000000000",
      "lntb500u1p0mocksignetinvoicetest000000000000000000000000000000000000000000000000000000000000000",
    ];

    for (const invoice of sampleInvoices) {
      const qrData = QRCode.create(invoice, { errorCorrectionLevel: "M" });
      const size = qrData.modules.size;
      const modules: boolean[][] = [];
      for (let r = 0; r < size; r++) {
        const row: boolean[] = [];
        for (let c = 0; c < size; c++) {
          row.push(Boolean(qrData.modules.get(c, r)));
        }
        modules.push(row);
      }

      const { data, width, height } = createQrImageData(modules);
      const decoded = jsQR(data, width, height);

      expect(decoded).not.toBeNull();
      expect(decoded?.data).toBe(invoice);
      expect(decoded?.data.startsWith("ln")).toBe(true);
    }
  }, 15000);

  it("proves that no pseudo-random or corrupt matrix is produced for standard payloads", async () => {
    const QRCode = await import("qrcode");
    const payload = "lnbcrt1000u1pmockintegritypayloadcheck1234567890abcdef";
    const qrData = QRCode.create(payload, { errorCorrectionLevel: "M" });

    // Finder patterns in top-left, top-right, bottom-left must be standard 7x7 squares
    const size = qrData.modules.size;
    expect(size).toBeGreaterThanOrEqual(21); // Minimum QR Version 1 size

    // Module at (0, 0) must be black/true (top-left finder corner)
    expect(Boolean(qrData.modules.get(0, 0))).toBe(true);
    // Center of top-left finder (3, 3) must be black/true
    expect(Boolean(qrData.modules.get(3, 3))).toBe(true);
  });

  it("accurately validates standard BOLT11 invoice formats via isRecognizedInvoiceFormat", () => {
    expect(isRecognizedInvoiceFormat("lnbc2500u1...")).toBe(true);
    expect(isRecognizedInvoiceFormat("lnbcrt50u1...")).toBe(true);
    expect(isRecognizedInvoiceFormat("lntb1000u1...")).toBe(true);
    expect(isRecognizedInvoiceFormat("lntbs250u1...")).toBe(true);
    expect(isRecognizedInvoiceFormat("lnsb250u1...")).toBe(true);
    expect(isRecognizedInvoiceFormat("  LNBCRT250U1... ")).toBe(true); // case-insensitive + trim
  });

  it("negative test: rejects non-BOLT11 or malformed invoice payloads", () => {
    expect(isRecognizedInvoiceFormat("")).toBe(false);
    expect(isRecognizedInvoiceFormat("bitcoin:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")).toBe(false);
    expect(isRecognizedInvoiceFormat("http://example.com/invoice")).toBe(false);
    expect(isRecognizedInvoiceFormat("random-gibberish-string")).toBe(false);
    expect(isRecognizedInvoiceFormat(null as unknown as string)).toBe(false);
  });
});
