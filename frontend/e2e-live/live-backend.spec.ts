import { expect, test } from "@playwright/test";

test("desktop investigation uses the real API and renders graph evidence", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "live-desktop");

  await page.goto("/investigate");
  await expect(page.getByText("Operational", { exact: true })).toBeVisible();

  await page
    .getByLabel("Operational question")
    .fill("What caused the P-101 failure?");
  await page.getByRole("button", { name: "Send question" }).click();

  await expect(
    page.getByText("AuRAG agent", { exact: true }),
  ).toBeVisible({ timeout: 120_000 });
  await expect(
    page.getByRole("button", { name: /FE-001|WO-1002/ }).first(),
  ).toBeVisible();
  await expect(page.getByText("Driving evidence")).toBeVisible();
  await expect(page.getByText("Nodes", { exact: true })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByText("Relations", { exact: true })).toBeVisible();
});

test("mobile knowledge-risk workspace uses real backend data without overflow", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "live-mobile");

  await page.goto("/knowledge-risk");
  await expect(page.getByText("Operational", { exact: true })).toBeVisible();
  await expect(page.getByText("People at risk", { exact: true })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByText("Uncovered assets", { exact: true })).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
});
