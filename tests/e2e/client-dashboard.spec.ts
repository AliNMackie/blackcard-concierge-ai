import { test, expect } from '@playwright/test';

test.describe('Client Dashboard', () => {
    test('should load the main dashboard', async ({ page }) => {
        await page.goto('/dashboard');

        // Check for main greeting
        await expect(page.getByText(/Hello/i)).toBeVisible();

        // Check for key cards
        await expect(page.getByText(/Readiness Status/i)).toBeVisible();
        await expect(page.getByText(/Today's Objective/i)).toBeVisible();
        await expect(page.getByText(/Start/i)).toBeVisible();

        // Concierge might be an icon or tab, check for tab bar
        await expect(page.locator('a[href="/messages"], a[href*="messages"]')).toBeVisible();
    });
});
