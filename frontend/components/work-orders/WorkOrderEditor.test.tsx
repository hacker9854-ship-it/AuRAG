import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import WorkOrderEditor from "./WorkOrderEditor";

const workOrder = {
  id: "WO-AI-1",
  date: "2026-07-20",
  type: "Corrective",
  status: "Draft",
  description: "Bearing pattern match",
  recommended_action: "Inspect and lubricate bearing.",
  source: "predictive_intelligence",
  version: 1,
  equipment: "P-101",
  predictive_event_id: "PE-1",
  created_at: "2026-07-20T12:00:00+00:00",
  updated_at: "2026-07-20T12:00:00+00:00",
  decisions: [],
};

describe("WorkOrderEditor", () => {
  it("persists edits with the current optimistic version", async () => {
    const onSave = vi.fn().mockResolvedValue({ ...workOrder, version: 2, status: "In Review" });
    render(<WorkOrderEditor workOrder={workOrder} onSave={onSave} onDecision={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Edited bearing intervention" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() =>
      expect(onSave).toHaveBeenCalledWith({
        expected_version: 1,
        description: "Edited bearing intervention",
        recommended_action: "Inspect and lubricate bearing.",
      }),
    );
  });

  it("requires a reason and persists rejection", async () => {
    const onDecision = vi.fn().mockResolvedValue({ ...workOrder, version: 2, status: "Rejected" });
    render(<WorkOrderEditor workOrder={workOrder} onSave={vi.fn()} onDecision={onDecision} />);

    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    expect(screen.getByRole("button", { name: "Confirm rejection" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Rejection reason"), {
      target: { value: "Duplicate of planned maintenance." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirm rejection" }));

    await waitFor(() =>
      expect(onDecision).toHaveBeenCalledWith({
        decision: "reject",
        expected_version: 1,
        reason: "Duplicate of planned maintenance.",
      }),
    );
  });
});

