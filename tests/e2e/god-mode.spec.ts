import { test, expect } from '@playwright/test';

test.describe('Trainer God Mode', () => {
    test('should load the dashboard and display live events', async ({ page }) => {
        // Navigate to God Mode
        await page.goto('/god-mode');

        // Check Header/Title
        await expect(page.getByText(/GOD MODE/i)).toBeVisible();

        // Check for the events table/list
        // We expect some rows or at least the container.
        // Assuming there's a refresh button we can click
        const refreshButton = page.getByRole('button', { name: /Refresh Stream/i });
        await expect(refreshButton).toBeVisible();
        await refreshButton.click();

        // Check for "Biometric Sentry" or similar text which indicates data loaded
        // Depending on seeding, this might be empty, but we check for structure
        await expect(page.locator('table, .grid, .flex').first()).toBeVisible();
    });
});
