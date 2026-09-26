import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e-live",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  timeout: 180_000,
  use: {
    baseURL: "http://localhost:3001",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "live-desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "live-mobile",
      use: { ...devices["Pixel 7"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --hostname localhost --port 3001",
    url: "http://localhost:3001",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
