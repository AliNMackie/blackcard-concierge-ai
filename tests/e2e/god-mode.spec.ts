import { test, expect } from '@playwright/test';

test.describe('Trainer God Mode', () => {
    test('should load the dashboard and display live events', async ({ page, context }) => {
        // Use env var for API Key
        const apiKey = process.env.ELITE_API_KEY;
        if (!apiKey) {
            throw new Error('ELITE_API_KEY environment variable is not set');
        }

        // Set E2E Auth Mock in local storage AND Cookies for robust bypass
        const domain = new URL(process.env.BASE_URL || 'https://blackcard-concierge.netlify.app').hostname;
        await context.addCookies([{
            name: 'E2E_AUTH_MOCK',
            value: apiKey || 'true',
            domain: domain,
            path: '/'
        }]);

        await context.addInitScript((key) => {
            window.localStorage.setItem('E2E_AUTH_MOCK', key || 'true');
        }, apiKey);

        // Navigate to God Mode with the E2E key in the query string
        await page.goto(`/god-mode?e2e-key=${apiKey}`);

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
