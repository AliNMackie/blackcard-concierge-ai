import { test, expect } from '@playwright/test';

test.describe('Trainer-Client Messaging', () => {
    test('should allow trainer to message client and client to reply', async ({ page }) => {
        // Enable browser console logging
        page.on('console', msg => console.log(`BROWSER: ${msg.text()}`));

        console.log('Test Started');

        // Navigate to a page first to have a window context (required for page.evaluate fetch)
        await page.goto('/god-mode');
        console.log('Initial Navigation Complete');

        // Use env var for API Key, fallback for local dev
        const apiKey = process.env.ELITE_API_KEY || 'EliteConcierge2026_GodSecret';

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

        // Wait for the seeded event to appear
        console.log('Waiting for seeded event...');
        await expect(page.getByText('E2E Test Initialization')).toBeVisible({ timeout: 15000 });
        console.log('Seeded event visible');

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
        await page.fill('textarea', testMessage);

        // Send
        await page.click('button:has-text("Send")');

        // Debug: Check if error appeared
        try {
            await expect(page.getByText('Send Message')).not.toBeVisible({ timeout: 5000 });
        } catch (e) {
            const errorMsg = page.locator('text=ERROR:');
            if (await errorMsg.isVisible()) {
                const text = await errorMsg.textContent();
                console.error(`Messaging Failed UI Error: ${text}`);
                throw new Error(`Messaging Failed: ${text}`);
            }
            throw e;
        }
        console.log(`Sent trainer message: ${testMessage}`);

        // 3. Client checks messages
        console.log('Switching to Client Messages...');
        await page.goto('/messages');

        // Verify message appears
        await expect(page.getByText(testMessage)).toBeVisible({ timeout: 10000 });
        await expect(page.getByText('From Your Trainer')).toBeVisible();

        // 4. Client replies
        const replyMessage = `Got it, thanks! ${Date.now()}`;
        await page.fill('input[placeholder="Message your coach..."]', replyMessage);
        // Click send
        await page.click('button:has(.lucide-send)');

        // Verify reply appears
        await expect(page.getByText(replyMessage)).toBeVisible();
        console.log(`Sent client reply: ${replyMessage}`);
    });
});
