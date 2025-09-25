import { test, expect } from "@playwright/test";

test.describe("Happy Path Tests", () => {
  test("should navigate to dashboard and verify content", async ({ page }) => {
    await page.goto("http://localhost:3000");
    await expect(page).toHaveTitle(/Dashboard/);
    await expect(page.getByTestId("dashboard")).toBeVisible();
  });

  test("should navigate to Agents page and verify table", async ({ page }) => {
    await page.goto("http://localhost:3000/agents");
    await expect(page.getByTestId("agents-page")).toBeVisible();
    await expect(page.getByTestId("agents-table")).toBeVisible();
    await expect(page.getByTestId("add-agent")).toBeVisible();
  });

  test("should navigate to Tasks page and verify table", async ({ page }) => {
    await page.goto("http://localhost:3000/tasks");
    await expect(page.getByTestId("tasks-page")).toBeVisible();
    await expect(page.getByTestId("tasks-table")).toBeVisible();
    await expect(page.getByTestId("add-task")).toBeVisible();
  });

  test("should navigate to Leases page and verify table", async ({ page }) => {
    await page.goto("http://localhost:3000/leases");
    await expect(page.getByTestId("leases-page")).toBeVisible();
    await expect(page.getByTestId("leases-table")).toBeVisible();
    await expect(page.getByTestId("add-lease")).toBeVisible();
  });

  test("should navigate to Events page and verify table", async ({ page }) => {
    await page.goto("http://localhost:3000/events");
    await expect(page.getByTestId("events-page")).toBeVisible();
    await expect(page.getByTestId("events-table")).toBeVisible();
    await expect(page.getByTestId("add-event")).toBeVisible();
  });

  test("should navigate to Jobs page and verify table", async ({ page }) => {
    await page.goto("http://localhost:3000/jobs");
    await expect(page.getByTestId("jobs-page")).toBeVisible();
    await expect(page.getByTestId("jobs-table")).toBeVisible();
    await expect(page.getByTestId("add-job")).toBeVisible();
  });

  test("should navigate to Studio page and verify table", async ({ page }) => {
    await page.goto("http://localhost:3000/studio");
    await expect(page.getByTestId("studio-page")).toBeVisible();
    await expect(page.getByTestId("studio-table")).toBeVisible();
    await expect(page.getByTestId("add-studio")).toBeVisible();
  });

  test("should navigate to Scheduler page and verify table", async ({
    page,
  }) => {
    await page.goto("http://localhost:3000/scheduler");
    await expect(page.getByTestId("scheduler-page")).toBeVisible();
    await expect(page.getByTestId("scheduler-table")).toBeVisible();
    await expect(page.getByTestId("add-schedule")).toBeVisible();
  });

  test("should navigate to Settings page and verify content", async ({
    page,
  }) => {
    await page.goto("http://localhost:3000/settings");
    await expect(page.getByTestId("settings-page")).toBeVisible();
    await expect(page.getByTestId("settings-content")).toBeVisible();
    await expect(page.getByTestId("save-settings")).toBeVisible();
  });
});
