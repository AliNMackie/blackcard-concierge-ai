import { test, expect } from '@playwright/test';

test('Dashboard polls for new events (Real-time)', async ({ page }) => {
    // 1. Setup Mock for initial load
    await page.route('*/**/api/events', async (route) => {
        const json = [
            {
                id: 1,
                event_type: 'chat',
                agent_message: 'Initial Message',
                created_at: new Date().toISOString()
            }
        ];
        await route.fulfill({ json });
    });

    // 2. Login & Go to Dashboard
    await page.goto('/login');
    await page.fill('input[type="email"]', 'client@elite.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // 3. Verify Initial State
    await expect(page.getByText('Initial Message')).toBeVisible();

    // 4. Update Mock for next poll
    // SWR revalidates on focus too, or interval. 
    // We can force revalidation or just wait for interval (5s).
    // Mocking the NEXT response.
    await page.unroute('*/**/api/events');
    await page.route('*/**/api/events', async (route) => {
        const json = [
            {
                id: 2,
                event_type: 'wearable',
                agent_message: 'New High Strain Detected',
                created_at: new Date().toISOString()
            },
            {
                id: 1,
                event_type: 'chat',
                agent_message: 'Initial Message',
                created_at: new Date().toISOString()
            }
        ];
        await route.fulfill({ json });
    });

    // 5. Wait for Polling update (SWR default is fast in test if focused)
    // We might need to wait 5s or trigger revalidation.
    // Playwright can simulate network idle or time.
    // Let's reload to be lazy? NO, we want to test polling.
    // We can wait for the text to appear.

    // Speed up time? SWR config in test?
    // 5s is long for a test.
    // But let's just wait for it.

    console.log('Waiting for polling update...');
    await expect(page.getByText('New High Strain Detected')).toBeVisible({ timeout: 10000 });

    // 6. Verify Live Indicator
    const indicator = page.getByText('Live');
    await expect(indicator).toBeVisible();
});
