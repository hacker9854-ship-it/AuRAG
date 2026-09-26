import { describe, expect, it } from "vitest";

import { getWorkspaceTitle } from "@/components/AppShell";

describe("getWorkspaceTitle", () => {
  it("maps top-level and nested workspace routes", () => {
    expect(getWorkspaceTitle("/")).toBe("Command Center");
    expect(getWorkspaceTitle("/investigate")).toBe("Investigate");
    expect(getWorkspaceTitle("/work-orders")).toBe("Work Orders");
    expect(getWorkspaceTitle("/work-orders/WO-AI-1")).toBe("Work Order");
  });

  it("uses a safe fallback for unknown workspace routes", () => {
    expect(getWorkspaceTitle("/unknown")).toBe("Workspace");
  });
});
