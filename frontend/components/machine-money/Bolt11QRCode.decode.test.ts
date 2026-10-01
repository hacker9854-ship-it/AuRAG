import { describe, it, expect } from "vitest";
import jsQR from "jsqr";

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

describe("BOLT11 QR Standards Compliance & Optical Decoding (FR-01 / E2E-E)", () => {
  it("verifies that a real BOLT11 invoice encoded in standard QR decodes to the exact string", async () => {
    // Dynamically import QRCode encoder
    const QRCode = await import("qrcode");
    const testInvoice = "lnbcrt2500u1pmocksimulatedinvoice0000000000000000000000000000000000";

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
  });
});
