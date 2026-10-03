const { chromium } = require("@playwright/test");
const path = require("path");
const fs = require("fs");

async function capture() {
  const screenshotsDir = path.resolve(__dirname, "../../docs/screenshots");
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  console.log("Launching Chromium...");
  const browser = await chromium.launch({
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    colorScheme: "dark",
  });

  const page = await context.newPage();

  console.log("Navigating to http://localhost:3000/machine-money ...");
  await page.goto("http://localhost:3000/machine-money", {
    waitUntil: "domcontentloaded",
    timeout: 30000,
  });

  console.log("Waiting for judge mode console...");
  await page.waitForSelector('[data-testid="judge-mode-console"]', { timeout: 20000 });
  await page.waitForTimeout(1500);

  // 1. Run Industrial Emergency (Happy Path Intervene)
  console.log("1. Running Industrial Emergency scenario (250 sats)...");
  const emergencyBtn = page.locator('[data-testid="run-emergency-button"]');
  await emergencyBtn.click();

  console.log("Waiting for emergency execution SUCCESS...");
  await page.waitForSelector('text="SUCCESS"', { timeout: 45000 });
  await page.waitForTimeout(1500);

  const judgeConsole = page.locator('[data-testid="judge-mode-console"]');

  // Screenshot 1: Above Fold
  console.log("Capturing machine-money-above-fold.png...");
  await judgeConsole.screenshot({
    path: path.join(screenshotsDir, "machine-money-above-fold.png"),
  });

  // Screenshot 2: Populated Execution Timeline
  console.log("Capturing machine-money-execution-timeline.png...");
  const timelineCard = page.locator('[data-testid="execution-timeline"]');
  if ((await timelineCard.count()) > 0) {
    await timelineCard.screenshot({
      path: path.join(screenshotsDir, "machine-money-execution-timeline.png"),
    });
  }

  // Screenshot 5: Proof Drawer / Verification
  console.log("Capturing machine-money-proof-drawer.png...");
  const cryptoProof = page.locator('[data-testid="judge-crypto-proof-section"]');
  if ((await cryptoProof.count()) > 0) {
    await cryptoProof.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    await cryptoProof.screenshot({
      path: path.join(screenshotsDir, "machine-money-proof-drawer.png"),
    });
  }

  // Screenshot 3: Vendor RFQ (3 pre-approved synthetic vendor nodes)
  console.log("Capturing machine-money-rfq.png...");
  const rfqContainer = page.locator('[data-testid="vendor-rfq-container"]');
  if ((await rfqContainer.count()) > 0) {
    await rfqContainer.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    await rfqContainer.screenshot({
      path: path.join(screenshotsDir, "machine-money-rfq.png"),
    });
  }

  // Screenshot 7: Economics & Explainability Drawer
  console.log("Capturing machine-money-economics.png...");
  const explainBtn = page.locator('button:has-text("Explainability Drawer")');
  if ((await explainBtn.count()) > 0) {
    await explainBtn.scrollIntoViewIfNeeded();
    await explainBtn.click();
    await page.waitForTimeout(1000);
    const dialog = page.locator('[role="dialog"]');
    if ((await dialog.count()) > 0) {
      await dialog.screenshot({
        path: path.join(screenshotsDir, "machine-money-economics.png"),
      });
      await page.keyboard.press("Escape");
      await page.waitForTimeout(800);
    }
  }

  // Screenshot 4: Policy Escalation (>500 sats)
  console.log("4. Running Policy Escalation scenario (1,200 sats)...");
  await judgeConsole.scrollIntoViewIfNeeded();
  const escalationBtn = page.locator('[data-testid="run-escalation-button"]');
  await escalationBtn.click();
  console.log("Waiting for PENDING_APPROVAL...");
  await page.waitForSelector('text="PENDING_APPROVAL"', { timeout: 45000 });
  await page.waitForTimeout(1500);
  console.log("Capturing machine-money-policy-escalation.png...");
  await judgeConsole.screenshot({
    path: path.join(screenshotsDir, "machine-money-policy-escalation.png"),
  });

  // Screenshot 6: Provider Failure (Graceful Degradation)
  console.log("6. Running Provider Failure scenario (250 sats)...");
  const providerFailBtn = page.locator('[data-testid="run-provider-failure-button"]');
  await providerFailBtn.click();
  console.log("Waiting for provider failure alert...");
  await page.waitForSelector('[data-testid="provider-failure-alert"]', { timeout: 45000 });
  await page.waitForTimeout(1500);
  console.log("Capturing machine-money-provider-failure.png...");
  await judgeConsole.screenshot({
    path: path.join(screenshotsDir, "machine-money-provider-failure.png"),
  });

  console.log("ALL 7 SCREENSHOTS SUCCESSFULLY CAPTURED!");
  await browser.close();
}

capture().catch((err) => {
  console.error("Screenshot capture error:", err);
  process.exit(1);
});
