import { test, expect } from '@playwright/test';

test.describe('Client Dashboard', () => {
    test('should load the main dashboard', async ({ page, context }) => {
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
            window.localStorage.setItem('E2E_BYPASS', 'true'); // New flag for api.ts
        }, apiKey);

        // Navigate to dashboard with the E2E key in the query string
        await page.goto(`/dashboard?e2e-key=${apiKey}`);

        // Check for main greeting
        await expect(page.getByText(/Hello/i)).toBeVisible();

        // Check for key cards
        await expect(page.getByText(/Readiness Status/i)).toBeVisible();

        // Check for activity feed header
        await expect(page.getByText(/Recent Activity/i)).toBeVisible();

        // Concierge might be an icon or tab, check for tab bar
        // The current implementation has a Tab Bar Placeholder with icons, not links
        // So we check if the dashboard rendered without errors
        await expect(page.locator('.fixed.bottom-0')).toBeVisible();
    });
});
