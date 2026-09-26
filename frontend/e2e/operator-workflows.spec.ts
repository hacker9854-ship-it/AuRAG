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

test("workspace shell persists while route titles and nested navigation update", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Operational", { exact: true })).toBeVisible();

  const sidebar = page.locator('[data-slot="sidebar-wrapper"]');
  await sidebar.evaluate((node) => {
    node.setAttribute("data-e2e-shell", "persistent");
  });

  await page.getByRole("link", { name: "Investigate" }).click();
  await expect(page.getByText("Operational investigation")).toBeVisible();
  await expect(sidebar).toHaveAttribute("data-e2e-shell", "persistent");

  await page.getByRole("link", { name: "Work Orders" }).click();
  await expect(page.getByRole("heading", { name: "Work-order decisions" })).toBeVisible();
  await expect(sidebar).toHaveAttribute("data-e2e-shell", "persistent");
});

test("operator can review, edit, and accept a persisted work order", async ({ page }) => {
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
