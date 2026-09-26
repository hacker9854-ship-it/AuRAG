import { beforeEach, describe, expect, it, vi } from "vitest";

import { getChatIdentity } from "./session";

describe("getChatIdentity", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.stubGlobal("crypto", { randomUUID: vi.fn().mockReturnValueOnce("user-1").mockReturnValueOnce("session-1") });
  });

  it("persists a user across visits and a session within the current tab", () => {
    const first = getChatIdentity();
    const second = getChatIdentity();

    expect(first).toEqual({ userId: "operator-user-1", sessionId: "session-session-1" });
    expect(second).toEqual(first);
    expect(localStorage.getItem("aurag.user_id")).toBe("operator-user-1");
    expect(sessionStorage.getItem("aurag.session_id")).toBe("session-session-1");
  });
});

