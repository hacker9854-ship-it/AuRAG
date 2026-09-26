import { expect, test } from "@playwright/test";

const api = "http://localhost:8000";

test.beforeEach(async ({ page }) => {
  await page.route(`${api}/api/health/ready`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ready",
        ready: true,
        dependencies: {
          neo4j: { status: "up" },
          qdrant: { status: "up" },
          redis: { status: "up" },
        },
      }),
    }),
  );
  await page.route(`${api}/api/notifications`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    }),
  );
  await page.route(`${api}/api/events/predictive`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: ": keep-alive\n\n",
    }),
  );
});

test("drawer navigation reaches separate workspaces and closes after selection", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle Sidebar" }).click();
  await page.getByRole("link", { name: "Investigate" }).click();

  await expect(page).toHaveURL(/\/investigate$/);
  await expect(page.getByRole("heading", { name: "Operational investigation" })).toBeVisible();
  await expect(page.locator('[data-slot="sidebar"][data-mobile="true"]')).not.toBeVisible();

  await page.getByRole("button", { name: "Toggle Sidebar" }).click();
  await page.getByRole("link", { name: "Evaluation" }).click();
  await expect(page).toHaveURL(/\/evaluation$/);
  await expect(page.getByRole("heading", { name: "Answer quality evaluation" })).toBeVisible();
});

test("investigation reveals cited answer evidence without losing context", async ({
  page,
}) => {
  await page.route(`${api}/api/chat`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user_query: "Why did P-101 fail?",
        intent: "rca",
        routing_confidence: 0.97,
        routed_agent: "rca",
        agent_response: "P-101 failed after bearing wear linked to missed lubrication.",
        citations: ["FE-001"],
        graph_paths: [
          { type: "FailureEvent", id: "FE-001" },
          { type: "Equipment", id: "P-101" },
        ],
        score_id: null,
        ragas_status: "scored",
        ragas_scores: {
          faithfulness: 0.92,
          context_precision: 0.88,
          answer_relevancy: 0.94,
        },
        low_faithfulness: false,
      }),
    }),
  );
  await page.route(`${api}/api/graph`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        nodes: [
          {
            id: "FailureEvent:FE-001",
            type: "FailureEvent",
            properties: { id: "FE-001", symptom: "Bearing wear" },
          },
          {
            id: "Equipment:P-101",
            type: "Equipment",
            properties: { tag_id: "P-101", name: "Feed pump" },
          },
        ],
        relationships: [
          {
            source: "FailureEvent:FE-001",
            target: "Equipment:P-101",
            type: "OCCURRED_ON",
          },
        ],
      }),
    }),
  );

  await page.goto("/investigate");
  await expect(page.getByRole("tab", { name: "Investigation" })).toBeVisible();
  await page.getByLabel("Operational question").fill("Why did P-101 fail?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(
    page.getByText("P-101 failed after bearing wear linked to missed lubrication."),
  ).toBeVisible();

  await page.getByRole("button", { name: "FE-001", exact: true }).click();
  await expect(page.getByRole("tab", { name: "Evidence" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByText("FailureEvent", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Relations")).toBeVisible();
});

test("evaluation trend and filters remain usable without page overflow", async ({
  page,
}) => {
  let lowOnlyRequested = false;
  await page.route(`${api}/api/evaluations/summary`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        total: 2,
        status_counts: { scored: 2 },
        agent_counts: { rca: 2 },
        low_faithfulness_count: 1,
        averages: {
          faithfulness: 0.78,
          context_precision: 0.81,
          answer_relevancy: 0.86,
        },
        trend: [
          {
            day: "2026-07-20",
            total: 1,
            faithfulness: 0.72,
            context_precision: 0.79,
            answer_relevancy: 0.83,
            low_faithfulness_count: 1,
          },
          {
            day: "2026-07-21",
            total: 1,
            faithfulness: 0.84,
            context_precision: 0.83,
            answer_relevancy: 0.89,
            low_faithfulness_count: 0,
          },
        ],
      }),
    }),
  );
  await page.route(`${api}/api/evaluations?*`, (route) => {
    lowOnlyRequested ||= route.request().url().includes("low_faithfulness=true");
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        limit: 20,
        offset: 0,
        total: lowOnlyRequested ? 1 : 2,
        has_more: false,
      }),
    });
  });

  await page.goto("/evaluation");
  await expect(page.getByRole("img", { name: "Daily RAGAS metric trend" })).toBeVisible();
  await expect(page.getByLabel("Evaluation status")).toBeVisible();
  await expect(page.getByLabel("Routed agent")).toBeVisible();

  await page.getByRole("button", { name: "Review queue (1)" }).click();
  await expect.poll(() => lowOnlyRequested).toBe(true);
  await expect(page.getByText("Low-faithfulness review queue")).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    )
    .toBe(true);
});

test("operator can review, edit, and accept a persisted work order", async ({
  page,
}) => {
  let current = {
    id: "WO-AI-1",
    date: "2026-07-21",
    type: "Corrective",
    status: "Draft",
    equipment: "P-101",
    description: "Bearing pattern match",
    recommended_action: "Inspect and lubricate bearing.",
    version: 1,
    predictive_event_id: "PE-1",
    decisions: [],
  };

  await page.route(`${api}/api/work-orders`, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [current] }),
    }),
  );
  await page.route(`${api}/api/work-orders/WO-AI-1`, async (route) => {
    if (route.request().method() === "PATCH") {
      const patch = route.request().postDataJSON();
      current = {
        ...current,
        description: patch.description,
        recommended_action: patch.recommended_action,
        status: "In Review",
        version: 2,
      };
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(current),
    });
  });
  await page.route(`${api}/api/work-orders/WO-AI-1/decisions`, async (route) => {
    current = { ...current, status: "Approved", version: 3 };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(current),
    });
  });

  await page.goto("/work-orders");
  await page.getByRole("link", { name: "Review work order" }).click();
  await expect(page.getByText(/P-101 .* Corrective .* version 1/)).toBeVisible();

  await page.getByLabel("Description").fill("Edited bearing intervention");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("version 2")).toBeVisible();

  await page.getByRole("button", { name: "Accept" }).click();
  await expect(page.getByText("Approved", { exact: true })).toBeVisible();
  await expect(page.getByText("version 3")).toBeVisible();
});
