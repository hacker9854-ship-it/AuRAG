import { describe, expect, it } from "vitest";

import { mergeNotifications } from "./notifications";

describe("mergeNotifications", () => {
  it("deduplicates by event ID and keeps newest events first", () => {
    const result = mergeNotifications(
      [
        {
          id: "PE-1",
          type: "predictive_warning",
          title: "P-101 requires attention",
          description: "Old",
          severity: "high",
          equipment: "P-101",
          failure_event_id: "FE-001",
          similarity: 0.9,
          status: "unread",
          detected_at: "2026-07-20T12:00:00+00:00",
          action_href: "/predictive-watch?event=PE-1",
        },
      ],
      [
        {
          id: "PE-1",
          type: "predictive_warning",
          title: "P-101 requires attention",
          description: "Updated",
          severity: "high",
          equipment: "P-101",
          failure_event_id: "FE-001",
          similarity: 0.95,
          status: "unread",
          detected_at: "2026-07-20T12:00:01+00:00",
          action_href: "/predictive-watch?event=PE-1",
        },
        {
          id: "PE-2",
          type: "predictive_warning",
          title: "C-201 requires attention",
          description: "New",
          severity: "high",
          equipment: "C-201",
          failure_event_id: "FE-002",
          similarity: 0.91,
          status: "unread",
          detected_at: "2026-07-20T12:01:00+00:00",
          action_href: "/predictive-watch?event=PE-2",
        },
      ],
    );

    expect(result.map((item) => item.id)).toEqual(["PE-2", "PE-1"]);
    expect(result[1].description).toBe("Updated");
  });
});

