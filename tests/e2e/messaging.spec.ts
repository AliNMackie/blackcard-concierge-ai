import { test, expect } from '@playwright/test';

test.describe('Trainer-Client Messaging', () => {
    test('should allow trainer to message client and client to reply', async ({ page, context }) => {
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

        // Enable browser console logging
        page.on('console', msg => console.log(`BROWSER: ${msg.text()}`));

        console.log('Test Started');

        // Navigate to a page first with the E2E key in the query string
        // This is the most robust way to skip the ProtectedRoute redirect on first load
        await page.goto(`/god-mode?e2e-key=${apiKey}`);
        console.log('Initial Navigation Complete (with Query Bypass)');

        // 0. Seed User '1' via WhatsApp Webhook (Browser Fetch)
        console.log('Seeding User 1 via WhatsApp Webhook (Browser)...');
        const seedUserStatus = await page.evaluate(async (key) => {
            const res = await fetch('https://elite-concierge-api-557456081985.europe-west2.run.app/webhooks/whatsapp', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${key}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    From: '1',
                    Body: 'E2E Init User Creation',
                    Timestamp: new Date().toISOString()
                })
            });
            return res.status;
        }, apiKey);
        console.log(`User Seeding Status: ${seedUserStatus}`);
        expect(seedUserStatus).toBe(200);

        // 1. Seed a chat event ensure God Mode has data (Browser Fetch)
        console.log('Seeding test event (Browser)...');
        const seedEventStatus = await page.evaluate(async (key) => {
            const res = await fetch('https://elite-concierge-api-557456081985.europe-west2.run.app/events/chat', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${key}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: '1', message: 'E2E Test Initialization' })
            });
            return res.status;
        }, apiKey);
        console.log(`Event Seeding Status: ${seedEventStatus}`);
        expect(seedEventStatus).toBe(200);

        // 2. Reload God Mode to see data
        console.log('Reloading God Mode...');
        await page.reload();

        console.log('Page URL:', page.url());

        // Check if God Mode loaded
        try {
            await expect(page.locator('h1')).toHaveText('GOD MODE');
            console.log('God Mode Header Verified');
        } catch (e) {
            console.error('God Mode Header Mismatch/Timeout');
            throw e;
        }

        // Wait for the seeded event to appear (check for User 1 in the table)
        console.log('Waiting for seeded event for User 1...');
        await expect(page.locator('td').filter({ hasText: /^1$/ }).first()).toBeVisible({ timeout: 15000 });
        console.log('User 1 entry visible');

        // Look for the "Message" button
        const messageBtn = page.getByRole('button', { name: /message/i }).first();
        await expect(messageBtn).toBeVisible();
        await messageBtn.click();
        console.log('Message button clicked');

        // Check modal opens
        await expect(page.getByText('Send Message')).toBeVisible();
        console.log('Modal visible');

        // Type message
        const testMessage = `Test message ${Date.now()}`;
        console.log(`Filling message: ${testMessage}`);
        await page.locator('textarea').fill(testMessage);

        // Send
        console.log('Clicking Send button...');
        await page.locator('button:has-text("Send")').click();

        // Debug: Check if error appeared or modal closed
        try {
            await expect(page.getByText('Send Message')).not.toBeVisible({ timeout: 10000 });
            console.log('Message modal closed successfully');
        } catch (e) {
            const errorMsg = page.locator('text=ERROR:');
            if (await errorMsg.isVisible()) {
                const text = await errorMsg.textContent();
                console.error(`Messaging Failed UI Error: ${text}`);
                throw new Error(`Messaging Failed: ${text}`);
            }
            console.error('Modal failed to close or timed out');
            throw e;
        }

        // Wait for it to appear in the God Mode stream first (confirms backend persisted it)
        console.log('Verifying message in God Mode stream...');
        await expect(page.locator('td').getByText(testMessage).first()).toBeVisible({ timeout: 10000 });
        console.log(`Sent trainer message visible in God Mode: ${testMessage}`);

        // 3. Switch to Client View (Messages)
        console.log('Switching to Client Messages...');
        await page.waitForTimeout(2000); // Wait for backend processing
        await page.goto(`${process.env.BASE_URL}/messages?e2e-key=${apiKey}`);

        // Verify message appears
        console.log('Waiting for message to appear in Client View...');
        await expect(page.getByText(testMessage)).toBeVisible({ timeout: 15000 });
        await expect(page.getByText('From Your Trainer').first()).toBeVisible();

        // 4. Client replies
        const replyMessage = `Got it, thanks! ${Date.now()}`;
        console.log(`Sending client reply: ${replyMessage}`);
        await page.locator('input[placeholder*="Message your coach"]').fill(replyMessage);

        // Click send (using locator for the button next to the input)
        await page.locator('button:has(svg)').last().click();

        // Verify reply appears
        await expect(page.getByText(replyMessage)).toBeVisible({ timeout: 10000 });
        console.log(`Sent client reply visible: ${replyMessage}`);
    });
});
