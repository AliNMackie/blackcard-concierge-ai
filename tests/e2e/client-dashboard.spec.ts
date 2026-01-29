import { test, expect } from '@playwright/test';

test.describe('Client Dashboard', () => {
    test('should load the main dashboard', async ({ page }) => {
        await page.goto('/dashboard');

        // Check for main greeting
        await expect(page.getByText(/Welcome/i)).toBeVisible();

        // Check for key cards
        await expect(page.getByText(/Daily Readiness/i).or(page.getByText(/Recovery Score/i))).toBeVisible();
        await expect(page.getByText(/Concierge/i)).toBeVisible();
    });
});
