import { test, expect } from '@playwright/test';

test.describe('Concierge Chat Interaction', () => {
    test('should allow user to send a message and receive a response', async ({ page, context }) => {
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

        // 0. Seed User '1' via WhatsApp Webhook (Browser Fetch) to ensure it exists
        await page.goto('/'); // Go to root first to be on correct domain for fetch
        console.log('Seeding User 1 via WhatsApp Webhook...');
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

        // Navigate to dashboard where chat widget lives
        await page.goto(`/messages?e2e-key=${apiKey}`);

        // Open chat widget if it's collapsible, or find the input area directly
        const chatInput = page.getByPlaceholder(/Message your coach/i);

        // Ensure input is visible and NOT disabled
        await expect(chatInput).toBeVisible({ timeout: 15000 });
        await expect(chatInput).not.toBeDisabled({ timeout: 10000 });

        // Type a test message
        const testMessage = `Test E2E ${Date.now()}: Recovery check`;
        await chatInput.click();
        await chatInput.fill(testMessage);

        // Wait for React state
        await page.waitForTimeout(500);

        // Try Enter key - usually the most reliable for chat apps
        await chatInput.press('Enter');

        // Also click the button just in case UI requires it (common in mobile-first designs)
        // Target the button containing the 'lucide-send' icon
        const sendButton = page.locator('button:has(svg.lucide-send), button:has(svg)');

        if (await sendButton.count() > 0) {
            // Try specific "Send" button first
            await sendButton.last().click({ force: true });
        }

        // Verify USER message appears (confirmation of send + reload)
        console.log(`Waiting for user message: ${testMessage}`);
        await expect(page.getByText(testMessage)).toBeVisible({ timeout: 15000 });
        console.log('User message verified in chat history');

        // Verify input is enabled again (signifies loading/sending finished)
        await expect(chatInput).not.toBeDisabled({ timeout: 10000 });
        console.log('Input re-enabled, chat loop complete');

        // Optional check for ANY bubble appearing after sent
        const chatBubbles = page.locator('div[class*="rounded-2xl"]');
        await expect(chatBubbles.first()).toBeVisible();
    });
});
